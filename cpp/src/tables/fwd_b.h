#pragma once

#include "../table.h"

namespace peregrine {

class Fwd_b : public Table {
private:
	struct key_fields_t {
		// Key fields IDs
		bf_rt_id_t forward;
	};

	struct actions_t {
		// Actions ids
		bf_rt_id_t hit;
	};

	key_fields_t key_fields;
	actions_t actions;

public:
	Fwd_b(const bfrt::BfRtInfo *info,
		  std::shared_ptr<bfrt::BfRtSession> session,
		  const bf_rt_target_t &dev_tgt)
		: Table(info, session, dev_tgt, "SwitchEgress_b.fwd") {
		init_key({
			{"hdr.peregrine.forward", &key_fields.forward},
		});

		init_actions({
			{"SwitchEgress_b.hit", &actions.hit},
		});
	}

	void add_entry(uint32_t value) {
		key_setup(value);
		data_setup();

		auto bf_status = table->tableEntryAdd(*session, dev_tgt, *key, *data);
		assert(bf_status == BF_SUCCESS);
	}

private:
	void key_setup(uint32_t value) {
		table->keyReset(key.get());
		auto bf_status =
			key->setValue(key_fields.forward, static_cast<uint64_t>(value));
		assert(bf_status == BF_SUCCESS);
	}

	void data_setup() {
		auto bf_status = table->dataReset(actions.hit, data.get());
		assert(bf_status == BF_SUCCESS);
	}
};

};	// namespace peregrine