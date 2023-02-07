#pragma once

#include "../table.h"

namespace peregrine {

class FwdRecirculation_a : public Table {
private:
	struct key_fields_t {
		// Key fields IDs
		bf_rt_id_t ingress_port;
		bf_rt_id_t recirc_toggle;
	};

	struct data_fields_t {
		// Data field ids
		bf_rt_id_t port;
		bf_rt_id_t COUNTER_SPEC_BYTES;
		bf_rt_id_t COUNTER_SPEC_PKTS;
	};

	struct actions_t {
		// Actions ids
		bf_rt_id_t fwd;
		bf_rt_id_t modify_eg_port;
	};

	key_fields_t key_fields;
	data_fields_t data_fields;
	actions_t actions;

public:
	FwdRecirculation_a(const bfrt::BfRtInfo *info,
					   std::shared_ptr<bfrt::BfRtSession> session,
					   const bf_rt_target_t &dev_tgt)
		: Table(info, session, dev_tgt, "SwitchIngress_a.fwd_recirculation") {
		init_key({
			{"ig_intr_md.ingress_port", &key_fields.ingress_port},
			{"ig_md.meta.recirc_toggle", &key_fields.recirc_toggle},
		});

		init_actions({
			{"SwitchIngress_a.fwd", &actions.fwd},
			{"SwitchIngress_a.modify_eg_port", &actions.modify_eg_port},
		});

		init_data_with_actions({
			{"port", {actions.fwd, &data_fields.port}},
			{"$COUNTER_SPEC_BYTES",
			 {actions.fwd, &data_fields.COUNTER_SPEC_BYTES}},
			{"$COUNTER_SPEC_PKTS",
			 {actions.fwd, &data_fields.COUNTER_SPEC_PKTS}},
		});

		init_data_with_actions({
			{"port", {actions.modify_eg_port, &data_fields.port}},
			{"$COUNTER_SPEC_BYTES",
			 {actions.modify_eg_port, &data_fields.COUNTER_SPEC_BYTES}},
			{"$COUNTER_SPEC_PKTS",
			 {actions.modify_eg_port, &data_fields.COUNTER_SPEC_PKTS}},
		});
	}

	void add_entry(uint32_t ig_port, bool recirc_toggle, uint32_t int_port) {
		key_setup(ig_port, recirc_toggle);

		if (recirc_toggle) {
			data_setup(int_port, actions.modify_eg_port);
		} else {
			data_setup(int_port, actions.fwd);
		}

		auto bf_status = table->tableEntryAdd(*session, dev_tgt, *key, *data);
		assert(bf_status == BF_SUCCESS);
	}

	std::pair<uint64_t, uint64_t> get_bytes_and_packets(uint32_t port,
														bool from_hw = false) {
		uint64_t bytes;
		uint64_t packets;

		auto with_recirc = get_bytes_and_packets(port, true, from_hw);
		auto without_recirc = get_bytes_and_packets(port, false, from_hw);

		bytes = with_recirc.first + without_recirc.first;
		packets = with_recirc.second + without_recirc.second;

		return std::pair<uint64_t, uint64_t>(bytes, packets);
	}

private:
	std::pair<uint64_t, uint64_t> get_bytes_and_packets(uint32_t port,
														bool recirc_toggle,
														bool from_hw) {
		auto hwflag = from_hw ? bfrt::BfRtTable::BfRtTableGetFlag::GET_FROM_HW
							  : bfrt::BfRtTable::BfRtTableGetFlag::GET_FROM_SW;

		key_setup(port, recirc_toggle);

		auto bf_status =
			table->tableEntryGet(*session, dev_tgt, *key, hwflag, data.get());
		if (bf_status != BF_SUCCESS) {
			// assert(bf_status == BF_SUCCESS);
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

	void key_setup(uint32_t ig_port, bool recirc_toggle) {
		table->keyReset(key.get());

		auto bf_status = key->setValue(key_fields.ingress_port,
									   static_cast<uint64_t>(ig_port));
		assert(bf_status == BF_SUCCESS);

		bf_status = key->setValue(key_fields.recirc_toggle, recirc_toggle);
		assert(bf_status == BF_SUCCESS);
	}

	void data_setup(uint32_t int_port, bf_rt_id_t action) {
		auto bf_status = table->dataReset(action, data.get());
		assert(bf_status == BF_SUCCESS);

		bf_status =
			data->setValue(data_fields.port, static_cast<uint64_t>(int_port));
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