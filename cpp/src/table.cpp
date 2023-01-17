#include "table.h"

namespace peregrine {

void Table::dump_data_fields() {
	std::stringstream ss;
	dump_data_fields(ss);
	std::cerr << ss.str();
}

void Table::dump_data_fields(std::ostream &os) {
	std::vector<bf_rt_id_t> ids;
	auto bf_status = table->dataFieldIdListGet(&ids);
	assert(bf_status == BF_SUCCESS);
	for (auto id : ids) {
		std::string name;
		table->dataFieldNameGet(id, &name);
		os << "data " << name << "\n";
	}
}

void dump_entry(std::ostream &os, const bfrt::BfRtTable *table,
				bfrt::BfRtTableKey *key, bfrt::BfRtTableData *data) {
	std::vector<bf_rt_id_t> key_fields_ids;

	auto bf_status = table->keyFieldIdListGet(&key_fields_ids);
	assert(bf_status == BF_SUCCESS);

	for (auto key_field_id : key_fields_ids) {
		std::string key_field_name;
		bfrt::DataType key_field_data_type;
		bfrt::KeyFieldType key_field_type;

		bf_status = table->keyFieldNameGet(key_field_id, &key_field_name);
		assert(bf_status == BF_SUCCESS);

		os << "  (key)    " << key_field_name << " = ";

		bf_status =
			table->keyFieldDataTypeGet(key_field_id, &key_field_data_type);
		assert(bf_status == BF_SUCCESS);

		bf_status = table->keyFieldTypeGet(key_field_id, &key_field_type);
		assert(bf_status == BF_SUCCESS);

		switch (key_field_data_type) {
			case bfrt::DataType::BOOL: {
				assert(false &&
					   "Bool type handling not implemented for key field "
					   "data types");
			} break;
			case bfrt::DataType::UINT64: {
				uint64_t key_field_value;

				switch (key_field_type) {
					case bfrt::KeyFieldType::EXACT: {
						bf_status =
							key->getValue(key_field_id, &key_field_value);
						assert(bf_status == BF_SUCCESS);
						os << key_field_value;
					} break;
					case bfrt::KeyFieldType::TERNARY: {
						uint64_t key_field_mask;
						bf_status = key->getValueandMask(
							key_field_id, &key_field_value, &key_field_mask);
						assert(bf_status == BF_SUCCESS);
						os << key_field_value;
						os << " (mask=" << key_field_mask << ")";
					} break;
					default: {
						assert(false &&
							   "Only Exact and Ternary key types are "
							   "implemented for uint64 data type");
					}
				}
			} break;
			case bfrt::DataType::FLOAT: {
				assert(false &&
					   "Float type handling not implemented for key field "
					   "data types");
			} break;
			case bfrt::DataType::STRING: {
				std::string key_field_value;
				bf_status = key->getValue(key_field_id, &key_field_value);
				assert(bf_status == BF_SUCCESS);
				os << key_field_value;

				switch (key_field_type) {
					case bfrt::KeyFieldType::EXACT: {
						bf_status =
							key->getValue(key_field_id, &key_field_value);
						assert(bf_status == BF_SUCCESS);
						os << key_field_value;
					} break;
					default: {
						assert(false &&
							   "Only Exact key type is implemented for String "
							   "data type");
					}
				}
			} break;
			case bfrt::DataType::INT_ARR: {
				assert(false &&
					   "Int array type handling not implemented for key "
					   "field data types");
			} break;
			case bfrt::DataType::BOOL_ARR: {
				assert(false &&
					   "Bool array type handling not implemented for key "
					   "field data types");
			} break;
			case bfrt::DataType::BYTE_STREAM: {
				size_t size;
				std::vector<uint8_t> value;

				bf_status = table->keyFieldSizeGet(key_field_id, &size);
				assert(bf_status == BF_SUCCESS);

				assert(size % 8 == 0);
				size /= 8;
				value.resize(size);

				switch (key_field_type) {
					case bfrt::KeyFieldType::EXACT: {
						bf_status =
							key->getValue(key_field_id, size, value.data());
						assert(bf_status == BF_SUCCESS);

						for (auto v : value) {
							os << " 0x";
							os << std::setw(2) << std::setfill('0') << std::hex
							   << (int)v;
						}
					} break;
					case bfrt::KeyFieldType::TERNARY: {
						std::vector<uint8_t> mask(size);
						bf_status = key->getValueandMask(
							key_field_id, size, value.data(), mask.data());
						assert(bf_status == BF_SUCCESS);
						for (auto i = 0u; i < value.size(); i++) {
							auto v = value[i];
							auto m = mask[i];
							os << " 0x";
							os << std::setw(2) << std::setfill('0') << std::hex
							   << (int)v;
							os << " (mask=0x";
							os << std::setw(2) << std::setfill('0') << std::hex
							   << (int)m;
							os << ")";
						}
					} break;
					default: {
						assert(false &&
							   "Only Exact and Ternary key types are "
							   "implemented for byte stream data type");
					}
				}
			} break;
			case bfrt::DataType::CONTAINER: {
				assert(false &&
					   "Container type handling not implemented for data "
					   "types");
			} break;
			case bfrt::DataType::STRING_ARR: {
				assert(false &&
					   "String array type handling not implemented for key "
					   "field data types");
			} break;
			default: {
				assert(false && "Unexpected key field data type");
			}
		}
		os << "\n";
	}

	bf_rt_id_t action_id;
	bool has_action;
	std::vector<bf_rt_id_t> data_fields_ids;

	if (table->actionIdApplicable()) {
		data->actionIdGet(&action_id);
		has_action = true;

		std::string action_name;
		bf_status = table->actionNameGet(action_id, &action_name);
		assert(bf_status == BF_SUCCESS);

		os << "  (action) " << action_name << "\n";

		bf_status = table->dataFieldIdListGet(action_id, &data_fields_ids);
		assert(bf_status == BF_SUCCESS);
	} else {
		has_action = false;

		bf_status = table->dataFieldIdListGet(&data_fields_ids);
		assert(bf_status == BF_SUCCESS);
	}

	for (auto data_field_id : data_fields_ids) {
		std::string data_field_name;
		bfrt::DataType data_field_data_type;

		if (has_action) {
			bf_status = table->dataFieldNameGet(data_field_id, action_id,
												&data_field_name);
		} else {
			bf_status =
				table->dataFieldNameGet(data_field_id, &data_field_name);
		}
		assert(bf_status == BF_SUCCESS);

		if (has_action) {
			bf_status = table->dataFieldDataTypeGet(data_field_id, action_id,
													&data_field_data_type);
		} else {
			bf_status = table->dataFieldDataTypeGet(data_field_id,
													&data_field_data_type);
		}
		assert(bf_status == BF_SUCCESS);

		if (data_field_name.size() && data_field_name[0] == '$') {
			continue;
		}

		os << "  (data)   " << data_field_name << " = ";

		switch (data_field_data_type) {
			case bfrt::DataType::BOOL: {
				bool data_field_value;
				bf_status = data->getValue(data_field_id, &data_field_value);
				assert(bf_status == BF_SUCCESS);
				os << data_field_value;
			} break;
			case bfrt::DataType::UINT64: {
				uint64_t data_field_value;
				bf_status = data->getValue(data_field_id, &data_field_value);
				assert(bf_status == BF_SUCCESS);
				os << data_field_value;
			} break;
			case bfrt::DataType::FLOAT: {
				float data_field_value;
				bf_status = data->getValue(data_field_id, &data_field_value);
				assert(bf_status == BF_SUCCESS);
				os << data_field_value;
			} break;
			case bfrt::DataType::STRING: {
				std::string data_field_value;
				bf_status = data->getValue(data_field_id, &data_field_value);
				assert(bf_status == BF_SUCCESS);
				os << data_field_value;
			} break;
			case bfrt::DataType::INT_ARR: {
				std::vector<uint64_t> data_field_value;
				bf_status = data->getValue(data_field_id, &data_field_value);
				assert(bf_status == BF_SUCCESS);
				os << "[";
				for (auto entry : data_field_value) {
					os << " " << entry;
				}
				os << " ]";
			} break;
			case bfrt::DataType::BOOL_ARR: {
				std::vector<bool> data_field_value;
				bf_status = data->getValue(data_field_id, &data_field_value);
				assert(bf_status == BF_SUCCESS);
				os << "[";
				for (auto entry : data_field_value) {
					if (entry) {
						os << " true";
					} else {
						os << " false";
					}
				}
				os << " ]";
			} break;
			case bfrt::DataType::BYTE_STREAM: {
				size_t size;
				std::vector<uint8_t> value;

				if (has_action) {
					bf_status = table->dataFieldSizeGet(data_field_id,
														action_id, &size);
					assert(bf_status == BF_SUCCESS);
				} else {
					bf_status = table->dataFieldSizeGet(data_field_id, &size);
					assert(bf_status == BF_SUCCESS);
				}

				assert(size % 8 == 0);
				size /= 8;
				value.resize(size);

				bf_status = data->getValue(data_field_id, size, value.data());
				assert(bf_status == BF_SUCCESS);

				for (auto v : value) {
					os << " 0x";
					os << std::setw(2) << std::setfill('0') << std::hex
					   << (int)v;
				}
			} break;
			case bfrt::DataType::CONTAINER: {
				assert(false &&
					   "Container type handling not implemented for data "
					   "types");
			} break;
			case bfrt::DataType::STRING_ARR: {
				std::vector<std::string> data_field_value;
				bf_status = data->getValue(data_field_id, &data_field_value);
				assert(bf_status == BF_SUCCESS);
				os << "[";
				for (auto entry : data_field_value) {
					os << " " << entry;
				}
				os << " ]";
			} break;
			default: {
				assert(false && "Not implemented");
			}
		}
		os << "\n";
	}

	os << "\n";
}

struct kd_t {
	std::vector<std::unique_ptr<bfrt::BfRtTableKey>> keys;
	std::vector<std::unique_ptr<bfrt::BfRtTableData>> datas;
	bfrt::BfRtTable::keyDataPairs pairs;

	kd_t(const bfrt::BfRtTable *table, uint32_t n)
		: keys(n), datas(n), pairs(n) {
		for (auto i = 0u; i < n; i++) {
			auto bf_status = table->keyAllocate(&keys[i]);
			assert(bf_status == BF_SUCCESS);

			bf_status = table->dataAllocate(&datas[i]);
			assert(bf_status == BF_SUCCESS);

			pairs[i] = std::pair<bfrt::BfRtTableKey *, bfrt::BfRtTableData *>(
				keys[i].get(), datas[i].get());
		}
	}
};

void Table::dump() {
	std::stringstream ss;
	dump(ss);
	std::cerr << ss.str();
}

void Table::dump(std::ostream &os) {
	bf_status_t bf_status;
	uint32_t total_entries;
	uint32_t processed_entries;
	auto flag = bfrt::BfRtTable::BfRtTableGetFlag::GET_FROM_HW;

	os << "\n";
	os << "================================================\n";
	os << "  Table name: " << table_name << "\n";

	total_entries = get_usage();

	os << "  Entries: " << total_entries << "\n";
	os << "\n";

	processed_entries = 0;

	bf_status = table->keyReset(key.get());
	assert(bf_status == BF_SUCCESS);

	bf_status = table->dataReset(data.get());
	assert(bf_status == BF_SUCCESS);

	while (processed_entries != total_entries) {
		if (processed_entries == 0) {
			bf_status = table->tableEntryGetFirst(*session, dev_tgt, flag,
												  key.get(), data.get());

			assert(bf_status == BF_SUCCESS);
			processed_entries++;

			dump_entry(os, table, key.get(), data.get());
		} else {
			uint32_t to_request = total_entries - processed_entries;
			uint32_t num_returned;

			kd_t kd(table, to_request);

			bf_status =
				table->tableEntryGetNext_n(*session, dev_tgt, *key, to_request,
										   flag, &kd.pairs, &num_returned);

			assert(num_returned == to_request);
			assert(bf_status == BF_SUCCESS);
			processed_entries += num_returned;

			for (auto i = 0u; i < num_returned; i++) {
				dump_entry(os, table, kd.keys[i].get(), kd.datas[i].get());
			}
		}
	}

	os << "================================================\n";
}

void Table::dump_table_names(const bfrt::BfRtInfo *bfrtInfo) {
	std::stringstream ss;

	std::vector<const bfrt::BfRtTable *> tables;
	auto bf_status = bfrtInfo->bfrtInfoGetTables(&tables);
	assert(bf_status == BF_SUCCESS);

	ss << "================================================\n";
	ss << "All tables:\n";

	for (auto table : tables) {
		std::string table_name;
		table->tableNameGet(&table_name);
		ss << "  " << table_name << "\n";
	}

	ss << "================================================\n";
	std::cerr << ss.str();
}

};	// namespace peregrine