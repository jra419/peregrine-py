#pragma once

#include "packet.h"
#include "table.h"

namespace peregrine {

class IpResStructUpdate : public Table {
private:
	struct key_fields_t {
		// Key fields IDs
		bf_rt_id_t res_check;
	};

	struct actions_t {
		// Actions ids
		bf_rt_id_t res_read;
		bf_rt_id_t res_update;
	};

	key_fields_t key_fields;
	actions_t actions;

public:
	IpResStructUpdate(const bfrt::BfRtInfo *info,
					  std::shared_ptr<bfrt::BfRtSession> session,
					  const bf_rt_target_t &dev_tgt)
		: Table(info, session, dev_tgt,
				"SwitchIngress_a.stats_ip_a.res_struct_update") {
		init_key({
			{"ig_md.stats_ip.res_check", &key_fields.res_check},
		});

		init_actions({
			{"SwitchIngress_a.stats_ip_a.res_read",
			 &actions.res_read},
			{"SwitchIngress_a.stats_ip_a.res_update",
			 &actions.res_update},
		});

		// fill mac ip src decay check table
		add_entry(0, actions.res_read);
		add_entry(1, actions.res_update);
	}

private:
	void add_entry(uint32_t flag, bf_rt_id_t action_id) {
		key_setup(flag);
		data_setup(action_id);

		auto bf_status = table->tableEntryAdd(*session, dev_tgt, *key, *data);
		assert(bf_status == BF_SUCCESS);
	}

	void key_setup(uint32_t flag) {
		table->keyReset(key.get());
		auto bf_status = key->setValue(key_fields.res_check,
									   static_cast<uint64_t>(flag));
		assert(bf_status == BF_SUCCESS);
	}

	void data_setup(bf_rt_id_t action_id) {
		auto bf_status = table->dataReset(action_id, data.get());
		assert(bf_status == BF_SUCCESS);
	}
};

};	// namespace peregrine