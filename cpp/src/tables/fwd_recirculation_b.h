#pragma once

#include "../table.h"

namespace peregrine {

class FwdRecirculation_b : public Table {
private:
	struct key_fields_t {
		// Key fields IDs
		bf_rt_id_t ingress_port;
	};

	struct data_fields_t {
		// Data field ids
		bf_rt_id_t port;
	};

	struct actions_t {
		// Actions ids
		bf_rt_id_t modify_eg_port;
	};

	key_fields_t key_fields;
	data_fields_t data_fields;
	actions_t actions;

public:
	FwdRecirculation_b(const bfrt::BfRtInfo *info,
					   std::shared_ptr<bfrt::BfRtSession> session,
					   const bf_rt_target_t &dev_tgt)
		: Table(info, session, dev_tgt, "SwitchIngress_b.fwd_recirculation") {
		init_key({
			{"ig_intr_md.ingress_port", &key_fields.ingress_port},
		});

		init_actions({
			{"SwitchIngress_b.modify_eg_port", &actions.modify_eg_port},
		});

		init_data_with_actions({
			{"port", {actions.modify_eg_port, &data_fields.port}},
		});
	}

	void add_entry(uint32_t ig_port, uint32_t eg_port) {
		key_setup(ig_port);
		data_setup(eg_port);

		auto bf_status = table->tableEntryAdd(*session, dev_tgt, *key, *data);
		assert(bf_status == BF_SUCCESS);
	}

private:
	void key_setup(uint32_t ig_port) {
		table->keyReset(key.get());
		auto bf_status = key->setValue(key_fields.ingress_port,
									   static_cast<uint64_t>(ig_port));
		assert(bf_status == BF_SUCCESS);
	}

	void data_setup(uint32_t eg_port) {
		auto bf_status = table->dataReset(actions.modify_eg_port, data.get());
		assert(bf_status == BF_SUCCESS);

		bf_status =
			data->setValue(data_fields.port, static_cast<uint64_t>(eg_port));
		assert(bf_status == BF_SUCCESS);
	}
};

};	// namespace peregrine