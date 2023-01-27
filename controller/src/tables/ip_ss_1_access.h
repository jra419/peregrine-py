#pragma once

#include "../table.h"

namespace peregrine {

class IpSs1Access : public Table {
private:
	struct key_fields_t {
		// Key fields IDs
		bf_rt_id_t recirc_toggle;
	};

	struct actions_t {
		// Actions ids
		bf_rt_id_t ss_1_incr;
		bf_rt_id_t ss_1_read;
	};

	key_fields_t key_fields;
	actions_t actions;

public:
	IpSs1Access(const bfrt::BfRtInfo *info,
				std::shared_ptr<bfrt::BfRtSession> session,
				const bf_rt_target_t &dev_tgt)
		: Table(info, session, dev_tgt,
				"SwitchIngress_a.stats_ip_a.ss_1_access") {
		init_key({
			{"ig_md.meta.recirc_toggle", &key_fields.recirc_toggle},
		});

		init_actions({
			{"SwitchIngress_a.stats_ip_a.ss_1_incr", &actions.ss_1_incr},
			{"SwitchIngress_a.stats_ip_a.ss_1_read", &actions.ss_1_read},
		});

		// fill up table
		add_entry(0, actions.ss_1_incr);
		add_entry(1, actions.ss_1_read);
	}

private:
	void add_entry(uint32_t value, bf_rt_id_t action_id) {
		key_setup(value);
		data_setup(action_id);

		auto bf_status = table->tableEntryAdd(*session, dev_tgt, *key, *data);
		assert(bf_status == BF_SUCCESS);
	}

	void key_setup(uint32_t value) {
		table->keyReset(key.get());

		auto bf_status = key->setValue(key_fields.recirc_toggle,
									   static_cast<uint64_t>(value));
		assert(bf_status == BF_SUCCESS);
	}

	void data_setup(bf_rt_id_t action_id) {
		auto bf_status = table->dataReset(action_id, data.get());
		assert(bf_status == BF_SUCCESS);
	}
};

};	// namespace peregrine