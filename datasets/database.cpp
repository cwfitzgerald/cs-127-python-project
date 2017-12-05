#include <cstring>
#include <fstream>
#include <functional>
#include <future>
#include <iostream>
#include <json.hpp>
#include <locale>
#include <regex>
#include <sparsehash/dense_hash_map>
#include <sparsehash/dense_hash_set>
#include <sqlite3.h>
#include <thread>
#include <vector>
// #include <map>
// #include <set>
// #include <sparsehash/sparse_hash_map>
// #include <sparsehash/sparse_hash_set>
// #include <unordered_map>
// #include <unordered_set>

using namespace std::string_literals;
using json = nlohmann::json;

class dense_set_wrapper : public google::dense_hash_set<int> {
  public:
	dense_set_wrapper() : google::dense_hash_set<int>() {
		google::dense_hash_set<int>::set_empty_key(-1);
	}
};

class dense_hash_wrapper : public google::dense_hash_map<std::string, dense_set_wrapper> {
  public:
	dense_hash_wrapper() : google::dense_hash_map<std::string, dense_set_wrapper>() {
		google::dense_hash_map<std::string, dense_set_wrapper>::set_empty_key(""s);
	}
};

namespace google {
	template <class K>
	void to_json(json& j, const dense_hash_set<K>& hm) {
		j = json{};
		for (auto& t : hm) {
			j.emplace_back(t.second);
		}
	}
	template <class K, class V>
	void to_json(json& j, const dense_hash_map<K, V>& hm) {
		j = json{};
		for (auto& t : hm) {
			j[t.first] = t.second;
		}
	}
	// void from_json(const json& j, dense_hash_map<K, V>& hm) {

	// }
} // namespace google

using dictionary_type = dense_hash_wrapper; // 5.33
// using dictionary_type = google::sparse_hash_map<std::string, google::sparse_hash_set<int>>;
// // 16.31
// using dictionary_type = std::unordered_map<std::string, std::unordered_set<int>>; // 5.46
// using dictionary_type = std::map<std::string, std::set<int>>; // 7.66
// Python 9.81

dictionary_type iindex_build_database_impl(const char* filename, int dataset_id, const std::vector<int>& data_columns,
                                           std::size_t threads, std::size_t offset) {

	std::regex find_alpha("[[:alpha:]]+", std::regex_constants::extended);

	dictionary_type dictionary;

	sqlite3* database;
	sqlite3_stmt* find_all_content;
	sqlite3_open_v2("datasets.sql", &database, SQLITE_OPEN_READONLY | SQLITE_OPEN_NOMUTEX, nullptr);

	sqlite3_prepare_v2(database,
	                   "SELECT id, contents FROM data WHERE filename = :filename and id % :threads "
	                   "= :offset;",
	                   -1, &find_all_content, nullptr);

	sqlite3_bind_int(find_all_content, 1, dataset_id);
	sqlite3_bind_int(find_all_content, 2, int(threads));
	sqlite3_bind_int(find_all_content, 3, int(offset));

	while (sqlite3_step(find_all_content) != SQLITE_DONE) {
		int id = sqlite3_column_int(find_all_content, 0);
		const char* data = reinterpret_cast<const char*>(sqlite3_column_text(find_all_content, 1));
		json data_json;
		try {
			data_json = json::parse(data);
		}
		catch (std::exception& e) {
			std::cerr << "Skipping " << id << '\n';
			continue;
		}
		auto starting_size = dictionary.size();

		uint64_t key_count = 0;
		for (int column : data_columns) {
			std::string coldata = data_json[column];
			auto matches_start = std::sregex_iterator(coldata.begin(), coldata.end(), find_alpha);
			auto matches_end = std::sregex_iterator();

			for (auto i = matches_start; i != matches_end; ++i) {
				std::smatch match = *i;
				std::string match_str = match.str();
				for (char& c : match_str) {
					c = char(std::tolower(c));
				}
				dictionary[match_str].insert(id);
				key_count++;
			}
		}
		auto ending_size = dictionary.size();
		std::cout << "Adding iindex nodes for " << filename << " " << id << ": " << key_count << " added. "
		          << ending_size << " total. Diff: " << ending_size - starting_size << '\n';
	}

	sqlite3_finalize(find_all_content);

	sqlite3_close(database);

	return dictionary;
}

dictionary_type merge_dictionaries(std::vector<dictionary_type>& dictionaries) {
	dictionary_type dict;

	for (std::size_t i = dictionaries.size(); i > 0; --i) {
		for (auto & [ key, value ] : dictionaries[i - 1]) {
			dict[key].insert(value.begin(), value.end());
		}
		dictionaries.pop_back();
	}

	return dict;
}

google::dense_hash_map<std::string, int64_t> create_translation_map(int dataset_id, dictionary_type& dict) {
	google::dense_hash_map<std::string, int64_t> ret;
	ret.set_empty_key(""s);

	sqlite3* database;
	sqlite3_stmt* create_statement;
	sqlite3_stmt* delete_statement;
	sqlite3_stmt* add_statement;
	sqlite3_stmt* begin_statement;
	sqlite3_stmt* commit_statement;
	sqlite3_open("datasets.sql", &database);
	sqlite3_prepare_v2(database,
	                   "CREATE TABLE IF NOT EXISTS iindex (file_id integer, key integer primary key, contents text)",
	                   -1, &create_statement, nullptr);
	sqlite3_step(create_statement);
	sqlite3_finalize(create_statement);

	sqlite3_prepare_v2(database, "DELETE FROM iindex WHERE file_id = :fild_id", -1, &delete_statement, nullptr);
	sqlite3_bind_int(delete_statement, 1, dataset_id);

	sqlite3_prepare_v2(database, "BEGIN", -1, &begin_statement, nullptr);
	sqlite3_prepare_v2(database, "COMMIT", -1, &commit_statement, nullptr);

	sqlite3_prepare_v2(database, "INSERT OR REPLACE INTO iindex (file_id, contents) VALUES(:file_id, :contents)", -1,
	                   &add_statement, nullptr);
	sqlite3_bind_int(add_statement, 1, dataset_id);

	sqlite3_step(begin_statement);
	sqlite3_step(delete_statement);

	int i = 0;
	for (auto & [ key, value ] : dict) {
		json j = value;

		std::string s = j.dump();

		sqlite3_bind_text(add_statement, 2, s.c_str(), -1, SQLITE_TRANSIENT);

		sqlite3_step(add_statement);

		auto current_id = sqlite3_last_insert_rowid(database);

		sqlite3_reset(add_statement);

		ret[key] = current_id;

		if (i++ % 1000 == 0) {
			std::cout << "\033[K\rAdding Key: " << key << " -> " << current_id << " -> " << value.size()
			          << " documents";
		}
	}
	std::cout << '\n';

	sqlite3_step(commit_statement);

	sqlite3_finalize(begin_statement);
	sqlite3_finalize(commit_statement);
	sqlite3_finalize(add_statement);

	return ret;
}

extern "C" void iindex_build_database(const char* filename) {
	std::locale::global(std::locale("en_US.UTF-8"));

	std::cout << filename << '\n';

	std::ifstream json_settings_file("index.json");

	json settings;
	json_settings_file >> settings;

	// auto doc_col = settings[filename]["document_column"].get<int>();
	auto data_columns = settings[filename]["data_columns"].get<std::vector<int>>();
	auto dataset_id = settings[filename]["id"].get<int>();

	// iindex_build_database_impl(filename, dataset_id, data_columns, 1, 0);

	auto threads = std::thread::hardware_concurrency() - 2;

	// auto threads = 4ULL;

	std::vector<std::future<dictionary_type>> future_list;
	future_list.reserve(threads);

	for (std::size_t i = 0; i < threads; ++i) {
		future_list.emplace_back(std::async(std::launch::async, iindex_build_database_impl, filename, dataset_id,
		                                    std::ref(data_columns), threads, i));
	}

	std::vector<dictionary_type> answer_list;
	answer_list.reserve(threads);

	for (auto& future : future_list) {
		answer_list.emplace_back(future.get());
	}

	auto final_dict = merge_dictionaries(answer_list);

	std::cout << "Total Length: " << final_dict.size() << '\n';

	auto translation = create_translation_map(dataset_id, final_dict);

	std::fstream json_translation_file("translations.json");

	json translation_json;

	if (json_translation_file) {
		json_translation_file >> translation_json;
	}

	translation_json[std::to_string(dataset_id)] = translation;

	json_translation_file.close();

	std::ofstream json_translation_file_out("translations.json", std::fstream::out | std::fstream::trunc);

	json_translation_file_out << std::setw(4) << translation_json;
}
