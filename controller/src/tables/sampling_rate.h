#pragma once

#include "../table.h"

#define SAMPLING_RATE_KEY 1
#define DEFAULT_SAMPLING_RATE 64

namespace peregrine {

class SamplingRate : public Table {
private:
	struct key_fields_t {
		// Key fields IDs
		bf_rt_id_t sampling_rate_key;
	};

	struct data_fields_t {
		// Data field ids
		bf_rt_id_t sampling_rate;
	};

	struct actions_t {
		// Actions ids
		bf_rt_id_t set_sampling_rate;
	};

	key_fields_t key_fields;
	data_fields_t data_fields;
	actions_t actions;

public:
	SamplingRate(const bfrt::BfRtInfo *info,
				   std::shared_ptr<bfrt::BfRtSession> session,
				   const bf_rt_target_t &dev_tgt)
		: Table(info, session, dev_tgt,
				"SwitchIngress_a.sampling_rate") {
		init_key({
			{"ig_md.meta.sampling_rate_key", &key_fields.sampling_rate_key},
		});

		init_actions({
			{"SwitchIngress_a.set_sampling_rate", &actions.set_sampling_rate},
		});

		init_data_with_actions({
			{"sampling_rate", {actions.set_sampling_rate, &data_fields.sampling_rate}},
		});

		// fill up table
		set_sampling_rate(DEFAULT_SAMPLING_RATE);
	}

	void set_sampling_rate(uint32_t sampling_rate) {
		key_setup(SAMPLING_RATE_KEY);
		data_setup(sampling_rate);

		auto bf_status = table->tableEntryAdd(*session, dev_tgt, *key, *data);
		assert(bf_status == BF_SUCCESS);
	}

private:
	void key_setup(uint32_t value) {
		table->keyReset(key.get());

		auto bf_status = key->setValue(key_fields.sampling_rate_key,
									   static_cast<uint64_t>(value));
		assert(bf_status == BF_SUCCESS);
	}

	void data_setup(uint32_t sampling_rate) {
		auto bf_status = table->dataReset(actions.set_sampling_rate, data.get());
		assert(bf_status == BF_SUCCESS);

		bf_status =
			data->setValue(data_fields.sampling_rate, static_cast<uint64_t>(sampling_rate));
		assert(bf_status == BF_SUCCESS);
	}
};

};	// namespace peregrine