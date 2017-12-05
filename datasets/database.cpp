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
	template <class K, class V>
	void to_json(json& j, const dense_hash_map<K, V>& hm) {
		j = json{};
		for (auto & [ key, value ] : hm) {
			j[key] = to_json(value);
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

dictionary_type iindex_build_database_impl(const char* filename, int dataset_id,
                                           const std::vector<int>& data_columns,
                                           std::size_t threads, std::size_t offset) {
	std::regex find_alpha("[[:alpha:]]+", std::regex_constants::extended);

	dictionary_type dictionary;

	sqlite3* database;
	sqlite3_stmt* find_all_content;
	sqlite3_open_v2("datasets.sql", &database, SQLITE_OPEN_READONLY | SQLITE_OPEN_NOMUTEX, nullptr);

	sqlite3_prepare_v2(database,
	                   "SELECT id, contents FROM data WHERE filename = :filename and id % :threads "
	                   "= :offset and id < 250;",
	                   -1, &find_all_content, nullptr);

	sqlite3_bind_int(find_all_content, 1, dataset_id);
	sqlite3_bind_int(find_all_content, 2, int(threads));
	sqlite3_bind_int(find_all_content, 3, int(offset));

	while (sqlite3_step(find_all_content) != SQLITE_DONE) {
		int id = sqlite3_column_int(find_all_content, 0);
		const char* data = reinterpret_cast<const char*>(sqlite3_column_text(find_all_content, 1));

		auto data_json = json::parse(data);

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
		std::cout << "Adding iindex nodes for " << filename << " " << id << ": " << key_count
		          << " added. " << ending_size << " total. Diff: " << ending_size - starting_size
		          << '\n';
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

google::dense_hash_map<std::string, int> create_translation_map(dictionary_type& dict) {
	google::dense_hash_map<std::string, int> ret;
	ret.set_empty_key(""s);
}

extern "C" void iindex_build_database(const char* filename) {
	std::locale::global(std::locale("en_US.UTF-8"));

	std::cout << filename << '\n';

	std::ifstream json_file("index.json");

	json settings;
	json_file >> settings;

	// auto doc_col = settings[filename]["document_column"].get<int>();
	auto data_columns = settings[filename]["data_columns"].get<std::vector<int>>();
	auto dataset_id = settings[filename]["id"].get<int>();

	// iindex_build_database_impl(filename, dataset_id, data_columns, 1, 0);

	auto threads = std::thread::hardware_concurrency();

	std::vector<std::future<dictionary_type>> future_list;
	future_list.reserve(threads);

	for (std::size_t i = 0; i < threads; ++i) {
		future_list.emplace_back(std::async(std::launch::async, iindex_build_database_impl,
		                                    filename, dataset_id, std::ref(data_columns), threads,
		                                    i));
	}

	std::vector<dictionary_type> answer_list;
	answer_list.reserve(threads);

	for (auto& future : future_list) {
		answer_list.emplace_back(future.get());
	}

	auto final_dict = merge_dictionaries(answer_list);

	std::cout << "Total Length: " << final_dict.size() << '\n';
}
