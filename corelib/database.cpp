#include <atomic>
#include <chrono>
#include <fstream>
#include <functional>
#include <future>
#include <iomanip>
#include <iostream>
#include <json.hpp>
#include <locale>
#include <memory>
#include <sparsehash/dense_hash_map>
#include <sparsehash/dense_hash_set>
#include <sparsehash/sparse_hash_map>
#include <sparsehash/sparse_hash_set>
#include <sqlite3.h>
#include <thread>
#include <unicode/regex.h>
#include <unicode/unistr.h>
#include <unicode/ustream.h>
#include <unicode/utypes.h>
#include <vector>

using namespace std::string_literals;
using namespace std::chrono_literals;
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
	template <class K>
	void from_json(const json& j, sparse_hash_set<K>& hm) {
		for (auto& v : j) {
			hm.insert(v.get<K>());
		}
	}
	template <class K, class V>
	void from_json(const json& j, sparse_hash_map<K, V>& hm) {
		for (auto it = j.begin(); it != j.end(); ++it) {
			hm[it.key()] = it.value().get<V>();
		}
	}
} // namespace google

using dictionary_build_type = dense_hash_wrapper;
using translation_storage_type = google::sparse_hash_map<std::string, int>;

class dictionary_creator : public std::vector<translation_storage_type> {
  public:
	dictionary_creator() : std::vector<translation_storage_type>() {
		std::ifstream f("datasets/translations.json");
		json j;

		f >> j;

		for (auto it = j.begin(); it != j.end(); ++it) {
			std::vector<translation_storage_type>::emplace_back(it.value().get<translation_storage_type>());
		}
	}
};

std::atomic<std::size_t> threads_done;
std::atomic<std::size_t> rows_finished;

dictionary_build_type build_iindex_database_impl(int dataset_id, const std::vector<int>& data_columns,
                                                 std::size_t threads, std::size_t offset) {

	UErrorCode regex_status = U_ZERO_ERROR;
	auto matcher = std::make_unique<icu::RegexMatcher>("\\p{Letter}+", 0, regex_status);

	if (U_FAILURE(regex_status)) {
		std::cout << u_errorName(regex_status) << '\n';
		std::terminate();
	}

	dictionary_build_type dictionary;

	sqlite3* database;
	sqlite3_stmt* find_all_content;
	sqlite3_open_v2("datasets/datasets.sql", &database, SQLITE_OPEN_READONLY | SQLITE_OPEN_NOMUTEX, nullptr);

	sqlite3_prepare_v2(database,
	                   "SELECT key, contents FROM data WHERE file_id = :filename and key % :threads "
	                   "= :offset;",
	                   -1, &find_all_content, nullptr);

	sqlite3_bind_int(find_all_content, 1, dataset_id);
	sqlite3_bind_int(find_all_content, 2, int(threads));
	sqlite3_bind_int(find_all_content, 3, int(offset));

	while (sqlite3_step(find_all_content) == SQLITE_ROW) {
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

		// auto starting_size = dictionary.size();

		uint64_t key_count = 0;
		for (int column : data_columns) {
			std::string coldata = data_json[column];

			auto string_data = icu::UnicodeString::fromUTF8(icu::StringPiece(coldata.c_str()));
			matcher->reset(string_data);

			while (matcher->find()) {
				auto start = matcher->start(regex_status);
				auto end = matcher->end(regex_status);

				icu::UnicodeString match;
				string_data.extract(start, end - start, match);
				match.toLower();

				std::string match_utf8;
				match.toUTF8String(match_utf8);
				dictionary[match_utf8].insert(id);
				key_count++;
			}
		}

		rows_finished += 1;
		// auto ending_size = dictionary.size();
		// std::cout << "Adding iindex nodes for " << filename << " " << id << ": " << key_count << " added. "
		//           << ending_size << " total. Diff: " << ending_size - starting_size << '\n';
	}

	sqlite3_finalize(find_all_content);

	sqlite3_close(database);

	threads_done += 1;

	return dictionary;
}

dictionary_build_type merge_dictionaries(std::vector<dictionary_build_type>& dictionaries) {
	dictionary_build_type dict;

	for (std::size_t i = dictionaries.size(); i > 0; --i) {
		for (auto& p : dictionaries[i - 1]) {
			auto key = p.first;
			auto value = p.second;
			dict[key].insert(value.begin(), value.end());
		}
		dictionaries.pop_back();
	}

	return dict;
}

google::dense_hash_map<std::string, int64_t> add_iindex_to_database(const char* filename, int dataset_id,
                                                                    dictionary_build_type& dict) {
	google::dense_hash_map<std::string, int64_t> ret;
	ret.set_empty_key(""s);

	sqlite3* database;
	sqlite3_stmt* delete_statement;
	sqlite3_stmt* begin_statement;
	sqlite3_stmt* commit_statement;
	sqlite3_stmt* add_statement;
	sqlite3_open("datasets/datasets.sql", &database);

	sqlite3_prepare_v2(database, "DELETE FROM iindex WHERE file_id = :fild_id", -1, &delete_statement, nullptr);
	sqlite3_bind_int(delete_statement, 1, dataset_id);

	sqlite3_prepare_v2(database, "BEGIN", -1, &begin_statement, nullptr);
	sqlite3_prepare_v2(database, "COMMIT", -1, &commit_statement, nullptr);

	sqlite3_prepare_v2(database, "INSERT OR REPLACE INTO iindex (file_id, contents) VALUES(:file_id, :contents)", -1,
	                   &add_statement, nullptr);
	sqlite3_bind_int(add_statement, 1, dataset_id);

	sqlite3_step(begin_statement);
	sqlite3_step(delete_statement);

	auto total_indices = dict.size();

	auto last_print = std::chrono::high_resolution_clock::now();

	int i = 0;
	for (auto& p : dict) {
		auto key = p.first;
		auto value = p.second;

		json j = value;

		std::string s = j.dump();

		sqlite3_bind_text(add_statement, 2, s.c_str(), -1, SQLITE_TRANSIENT);

		sqlite3_step(add_statement);

		auto current_id = sqlite3_last_insert_rowid(database);

		sqlite3_reset(add_statement);

		ret[key] = current_id;

		auto cur_time = std::chrono::high_resolution_clock::now();
		bool print = i == 0 || cur_time - last_print > 20ms;
		if (print) {
			last_print = cur_time;
			std::cout << "\r\033[K\r\t" << filename << " -- Row " << i << '/' << total_indices << ": "
			          << std::setprecision(0) << std::round((double(i) / double(total_indices)) * 100) << "%";
		}
		++i;
	}
	std::cout << "\r\033[K\r\t" << filename
	          << " -- \u001b[32;1mInverse Index Added to DB\u001b[0m Rows: " << total_indices << '\n';

	sqlite3_step(commit_statement);

	sqlite3_finalize(add_statement);
	sqlite3_finalize(begin_statement);
	sqlite3_finalize(commit_statement);
	sqlite3_finalize(delete_statement);

	return ret;
}

extern "C" void build_iindex_database(const char* filename) {
	///////////////////
	// LOAD SETTINGS //
	///////////////////
	std::ifstream json_settings_file("datasets/index.json");

	json settings;
	json_settings_file >> settings;

	auto data_columns = settings[filename]["data_columns"].get<std::vector<int>>();
	auto dataset_id = settings[filename]["id"].get<int>();

	/////////////////////////////
	// CREATE AND CALL THREADS //
	/////////////////////////////
	auto threads = std::thread::hardware_concurrency();
	threads_done = 0;
	rows_finished = 0;

	std::vector<std::future<dictionary_build_type>> future_list;
	future_list.reserve(threads);

	for (std::size_t i = 0; i < threads; ++i) {
		future_list.emplace_back(
		    std::async(std::launch::async, build_iindex_database_impl, dataset_id, std::ref(data_columns), threads, i));
	}

	while (threads_done != threads) {
		std::cout << "\r\033[K\r\t" << filename << " -- Adding Row #" << rows_finished;
		std::this_thread::sleep_for(20ms);
	}

	/////////////////
	// GET ANSWERS //
	/////////////////
	std::vector<dictionary_build_type> answer_list;
	answer_list.reserve(threads);

	for (auto& future : future_list) {
		answer_list.emplace_back(future.get());
	}

	// Merge answers into one dictionary
	std::cout << "\r\033[K\r\t" << filename << " -- Merging Dictionaries...";
	auto final_dict = merge_dictionaries(answer_list);
	std::cout << "\r\033[K\r\t" << filename << " -- \u001b[32;1mDictionary Built\u001b[0m Rows: " << final_dict.size()
	          << '\n';

	/////////////////////
	// ADD TO DATABASE //
	/////////////////////
	auto translation = add_iindex_to_database(filename, dataset_id, final_dict);

	///////////////////////////////
	// Save Translations to JSON //
	///////////////////////////////
	std::cout << "\r\033[K\r\t" << filename << " -- Adding translations to translations.json";
	std::fstream json_translation_file("datasets/translations.json");

	json translation_json;

	if (json_translation_file) {
		json_translation_file >> translation_json;
	}

	translation_json[std::to_string(dataset_id)] = translation;

	json_translation_file.close();

	std::ofstream json_translation_file_out("datasets/translations.json", std::fstream::out | std::fstream::trunc);

	json_translation_file_out << std::setw(4) << translation_json;

	std::cout << "\r\033[K\r\t" << filename << " -- \u001b[32;1mAdded Translations\u001b[0m to translations.json\n";
}

extern "C" int translate_string(int dataset_id, const char* search_term) {
	static dictionary_creator dict_list;

	auto&& dict = dict_list[dataset_id];

	auto it = dict.find(search_term);
	bool found = it != dict.end();
	if (found) {
		return it->second;
	}
	else {
		return -1;
	}
}
