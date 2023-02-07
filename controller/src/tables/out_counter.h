#pragma once

#include "../table.h"

namespace peregrine {

class OutCounter : public Table {
private:
	struct key_fields_t {
		// Key fields IDs
		bf_rt_id_t COUNTER_INDEX;
	};

	struct data_fields_t {
		// Data field ids
		bf_rt_id_t COUNTER_SPEC_BYTES;
		bf_rt_id_t COUNTER_SPEC_PKTS;
	};

	key_fields_t key_fields;
	data_fields_t data_fields;

public:
	OutCounter(const bfrt::BfRtInfo *info,
			   std::shared_ptr<bfrt::BfRtSession> session,
			   const bf_rt_target_t &dev_tgt)
		: Table(info, session, dev_tgt, "SwitchEgress_a.out_counter") {
		init_key({
			{"$COUNTER_INDEX", &key_fields.COUNTER_INDEX},
		});

		init_data({
			{"$COUNTER_SPEC_BYTES", &data_fields.COUNTER_SPEC_BYTES},
			{"$COUNTER_SPEC_PKTS", &data_fields.COUNTER_SPEC_PKTS},
		});
	}

	void add_entry(uint32_t port) {
		key_setup(port);
		data_setup();

		auto bf_status = table->tableEntryAdd(*session, dev_tgt, *key, *data);
		assert(bf_status == BF_SUCCESS);
	}

	std::pair<uint64_t, uint64_t> get_bytes_and_packets(uint32_t port,
														bool from_hw) {
		auto hwflag = from_hw ? bfrt::BfRtTable::BfRtTableGetFlag::GET_FROM_HW
							  : bfrt::BfRtTable::BfRtTableGetFlag::GET_FROM_SW;

		key_setup(port);

		auto bf_status = table->dataReset(data.get());
		assert(bf_status == BF_SUCCESS);

		bf_status =
			table->tableEntryGet(*session, dev_tgt, *key, hwflag, data.get());

		if (bf_status != BF_SUCCESS) {
			return std::pair<uint64_t, uint64_t>(0, 0);
		}

		uint64_t bytes;
		bf_status = data->getValue(data_fields.COUNTER_SPEC_BYTES, &bytes);
		assert(bf_status == BF_SUCCESS);

		uint64_t packets;
		bf_status = data->getValue(data_fields.COUNTER_SPEC_PKTS, &packets);
		assert(bf_status == BF_SUCCESS);

		return std::pair<uint64_t, uint64_t>(bytes, packets);
	}

private:
	void key_setup(uint32_t port) {
		table->keyReset(key.get());

		auto bf_status = key->setValue(key_fields.COUNTER_INDEX,
									   static_cast<uint64_t>(port));
		assert(bf_status == BF_SUCCESS);
	}

	void data_setup() {
		auto bf_status = table->dataReset(data.get());
		assert(bf_status == BF_SUCCESS);

		bf_status = data->setValue(data_fields.COUNTER_SPEC_BYTES,
								   static_cast<uint64_t>(0));
		assert(bf_status == BF_SUCCESS);

		bf_status = data->setValue(data_fields.COUNTER_SPEC_PKTS,
								   static_cast<uint64_t>(0));
		assert(bf_status == BF_SUCCESS);
	}
};

};	// namespace peregrine