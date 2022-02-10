control c_stats_ip(inout header_t hdr, inout ingress_metadata_a_t ig_md) {

	// ----------------------------------------
	// Hashes
	// ----------------------------------------

	Hash<bit<16>>(HashAlgorithm_t.CRC16) hash_ip_0; // Hash for flow id (a->b)
	Hash<bit<16>>(HashAlgorithm_t.CRC16) hash_ip_1; // Hash for flow id (b->a)

	// ----------------------------------------
	// Registers and temp. variables
	// ----------------------------------------

	Register<bit<32>, _>(REG_SIZE) reg_ip_ts;
	Register<bit<32>, _>(REG_SIZE) reg_ip_cnt_0; 		// Packet count for flow id (a->b)
	Register<bit<32>, _>(REG_SIZE) reg_ip_cnt_1; 		// Packet count for flow id (b->a)
	Register<bit<32>, _>(REG_SIZE) reg_ip_len;   		// Packet length
	Register<bit<32>, _>(REG_SIZE) reg_ip_ss;    		// Squared sum of the packet length
	Register<bit<32>, _>(REG_SIZE) reg_ip_mean;		// Mean
	Register<bit<32>, _>(1) reg_ip_mean_squared_0;			// Squared mean for flow id (a->b)
	Register<bit<32>, _>(REG_SIZE) reg_ip_variance;	// Variance
	Register<bit<32>, _>(REG_SIZE) reg_ip_last_res; 	// Residue values

	// Temporary variables for stats calculation.
	bit<32> res_prod = 0;

	// ----------------------------------------
	// Register actions
	// ----------------------------------------

	// Check if more than 100 ms have elapsed since the last update for the current flow.
	// If so, increase the stored value by 100 ms and set a flag.
	// 1525 corresponds to the bit-sliced value for 100 ms (in ns).
    RegisterAction<_, _, bit<1>>(reg_ip_ts) ract_decay_check_100_ms = {
        void apply(inout bit<32> value, out bit<1> result) {
            result = 0;
            if (DECAY_100_MS < ig_md.meta.current_ts - value) {
                value = value + DECAY_100_MS;
                result = 1;
            } else {
                value = ig_md.meta.current_ts;
            }
        }
    };

	// Check if more than 1 sec has elapsed since the last update for the current flow.
	// If so, increase the stored value by 1 sec and set a flag.
	// 15258 corresponds to the bit-sliced value for 1 sec (in ns).
    RegisterAction<_, _, bit<1>>(reg_ip_ts) ract_decay_check_1_s = {
        void apply(inout bit<32> value, out bit<1> result) {
            result = 0;
            if (DECAY_1_S < ig_md.meta.current_ts - value) {
                value = value + DECAY_1_S;
                result = 1;
            } else {
                value = ig_md.meta.current_ts;
            }
        }
    };

	// Check if more than 10 secs have elapsed since the last update for the current flow.
	// If so, increase the stored value by 10 secs and set a flag.
	// 152587 corresponds to the bit-sliced value for 10 secs (in ns).
    RegisterAction<_, _, bit<1>>(reg_ip_ts) ract_decay_check_10_s = {
        void apply(inout bit<32> value, out bit<1> result) {
            result = 0;
            if (DECAY_10_S < ig_md.meta.current_ts - value) {
                value = value + DECAY_10_S;
                result = 1;
            } else {
                value = ig_md.meta.current_ts;
            }
        }
    };

	// Check if more than 60 secs have elapsed since the last update for the current flow.
	// If so, increase the stored value by 60 secs and set a flag.
	// 915527 corresponds to the bit-sliced value for 60 secs (in ns).
    RegisterAction<_, _, bit<1>>(reg_ip_ts) ract_decay_check_60_s = {
        void apply(inout bit<32> value, out bit<1> result) {
            result = 0;
            if (DECAY_60_S < ig_md.meta.current_ts - value) {
                value = value + DECAY_60_S;
                result = 1;
            } else {
                value = ig_md.meta.current_ts;
            }
        }
    };

	MathUnit<bit<32>>(MathOp_t.MUL, 1, 2) div_pkt_cnt;
	RegisterAction<_, _, bit<32>>(reg_ip_cnt_0) ract_pkt_cnt_0_incr = {
		void apply(inout bit<32> value, out bit<32> result) {
			if (ig_md.stats_ip.decay_check == 0) {
				value = value + 1;
			} else {
				value = div_pkt_cnt.execute(value) + 1;
			}
			result = value;
		}
	};

	RegisterAction<_, _, bit<32>>(reg_ip_cnt_1) ract_pkt_cnt_1_incr = {
		void apply(inout bit<32> value) {
			value = ig_md.stats_ip.pkt_cnt_0;
		}
	};

	RegisterAction<_, _, bit<32>>(reg_ip_cnt_1) ract_pkt_cnt_1_read = {
		void apply(inout bit<32> value, out bit<32> result) {
			value = value;
			result = value;
		}
	};

	MathUnit<bit<32>>(MathOp_t.MUL, 1, 2) div_pkt_len;
	RegisterAction<_, _, bit<32>>(reg_ip_len) ract_pkt_len_incr = {
		void apply(inout bit<32> value, out bit<32> result) {
			if (ig_md.stats_ip.decay_check == 0) {
				value = value + (bit<32>)hdr.ipv4.len;
			} else {
				value = div_pkt_len.execute(value);
			}
			result = value;
		}
	};

    MathUnit<bit<32>>(MathOp_t.MUL, 1, 2) div_ss;
    RegisterAction<_, _, bit<32>>(reg_ip_ss) ract_ss_calc = {
        void apply(inout bit<32> value, out bit<32> result) {
            if (ig_md.stats_ip.decay_check == 0) {
                value = value + ig_md.meta.pkt_len_squared;
            } else {
                value = div_ss.execute(value);
            }
            result = value;
        }
    };

	RegisterAction<_, _, bit<32>>(reg_ip_mean) ract_mean_0_write = {
		void apply(inout bit<32> value) {
			value = ig_md.stats_ip.mean_0;
		}
	};

	RegisterAction<_, _, bit<32>>(reg_ip_mean) ract_mean_1_read = {
		void apply(inout bit<32> value, out bit<32> result) {
			value = value;
			result = value;
		}
	};

	MathUnit<bit<32>>(MathOp_t.SQR, 1) square_mean_0;
	RegisterAction<_, _, bit<32>>(reg_ip_mean_squared_0) ract_mean_squared_0_calc = {
		void apply(inout bit<32> value, out bit<32> result) {
			value = square_mean_0.execute(ig_md.stats_ip.mean_0);
			result = value;
		}
	};

	RegisterAction<_, _, bit<32>>(reg_ip_variance) ract_variance_0_write = {
		void apply(inout bit<32> value) {
			value = ig_md.stats_ip.variance_0;
		}
	};

	RegisterAction<_, _, bit<32>>(reg_ip_variance) ract_variance_1_read = {
		void apply(inout bit<32> value, out bit<32> result) {
			value = value;
			result = value;
		}
	};

	RegisterAction<_, _, bit<32>>(reg_ip_last_res) ract_last_res_write = {
		void apply(inout bit<32> value) {
			value = ig_md.stats_ip.residue;
		}
	};

	RegisterAction<_, _, bit<32>>(reg_ip_last_res) ract_last_res_read = {
		void apply(inout bit<32> value, out bit<32> result) {
			value = value;
			result = ig_md.stats_ip.residue - value;
		}
	};

	// ----------------------------------------
	// Actions
	// ----------------------------------------

	action hash_calc_ip_0() {
		ig_md.hash.ip_0 = (bit<16>)hash_ip_0.get({hdr.ipv4.src_addr, hdr.ipv4.dst_addr})[12:0];
	}

	action hash_calc_ip_1() {
		ig_md.hash.ip_1 = (bit<16>)hash_ip_1.get({hdr.ipv4.dst_addr, hdr.ipv4.src_addr})[12:0];
	}

    action decay_check_100_ms() {
        ig_md.stats_ip.decay_check = ract_decay_check_100_ms.execute(ig_md.hash.ip_0);
    }

    action decay_check_1_s() {
        ig_md.stats_ip.decay_check = ract_decay_check_1_s.execute(ig_md.hash.ip_0);
    }

    action decay_check_10_s() {
        ig_md.stats_ip.decay_check = ract_decay_check_10_s.execute(ig_md.hash.ip_0);
    }

    action decay_check_60_s() {
        ig_md.stats_ip.decay_check = ract_decay_check_60_s.execute(ig_md.hash.ip_0);
    }

	action pkt_cnt_0_incr() {
		ig_md.stats_ip.pkt_cnt_0 = ract_pkt_cnt_0_incr.execute(ig_md.hash.ip_0);
	}

	action pkt_cnt_1_read() {
		ig_md.stats_ip.pkt_cnt_1 = ract_pkt_cnt_1_read.execute(ig_md.hash.ip_1);
	}

	action pkt_len_incr() {
		ig_md.stats_ip.pkt_len = ract_pkt_len_incr.execute(ig_md.hash.ip_0);
	}

	action ss_calc() {
		ig_md.stats_ip.ss = ract_ss_calc.execute(ig_md.hash.ip_0);
	}

	action residue_calc() {
		ig_md.stats_ip.residue = ig_md.stats_ip.pkt_len - ig_md.stats_ip.mean_0;
	}

	action mean_1_read() {
		ig_md.stats_ip.mean_1 = ract_mean_1_read.execute(ig_md.hash.ip_1);
	}

	// The original operation uses a modulo here, so we need to cover the case where we obtain a negative number.
	action variance_0_calc() {
		ig_md.stats_ip.variance_0 = ig_md.stats_ip.mean_squared_0 - ig_md.stats_ip.mean_ss;
		ig_md.stats_ip.variance_0_neg = ig_md.stats_ip.mean_ss - ig_md.stats_ip.mean_squared_0;
	}

	action variance_1_read() {
		ig_md.stats_ip.variance_1 = ract_variance_1_read.execute(ig_md.hash.ip_1);
	}

	action mean_squared_0_calc() {
		ig_md.stats_ip.mean_squared_0 = ract_mean_squared_0_calc.execute(ig_md.hash.ip_0);
	}

	action last_res_1_read() {
		ig_md.stats_ip.last_res = ract_last_res_read.execute(ig_md.hash.ip_1);
	}

	action rshift_mean_1() {
		ig_md.stats_ip.mean_0 = ig_md.stats_ip.pkt_len >> 1;
		ig_md.stats_ip.mean_ss = ig_md.stats_ip.ss >> 1;
	}

	action rshift_mean_2() {
		ig_md.stats_ip.mean_0 = ig_md.stats_ip.pkt_len >> 2;
		ig_md.stats_ip.mean_ss = ig_md.stats_ip.ss >> 2;
	}

	action rshift_mean_3() {
		ig_md.stats_ip.mean_0 = ig_md.stats_ip.pkt_len >> 3;
		ig_md.stats_ip.mean_ss = ig_md.stats_ip.ss >> 3;
	}

	action rshift_mean_4() {
		ig_md.stats_ip.mean_0 = ig_md.stats_ip.pkt_len >> 4;
		ig_md.stats_ip.mean_ss = ig_md.stats_ip.ss >> 4;
	}

	action rshift_mean_5() {
		ig_md.stats_ip.mean_0 = ig_md.stats_ip.pkt_len >> 5;
		ig_md.stats_ip.mean_ss = ig_md.stats_ip.ss >> 5;
	}

	action rshift_mean_6() {
		ig_md.stats_ip.mean_0 = ig_md.stats_ip.pkt_len >> 6;
		ig_md.stats_ip.mean_ss = ig_md.stats_ip.ss >> 6;
	}

	action rshift_mean_7() {
		ig_md.stats_ip.mean_0 = ig_md.stats_ip.pkt_len >> 7;
		ig_md.stats_ip.mean_ss = ig_md.stats_ip.ss >> 7;
	}

	action rshift_mean_8() {
		ig_md.stats_ip.mean_0 = ig_md.stats_ip.pkt_len >> 8;
		ig_md.stats_ip.mean_ss = ig_md.stats_ip.ss >> 8;
	}

	action rshift_mean_9() {
		ig_md.stats_ip.mean_0 = ig_md.stats_ip.pkt_len >> 9;
		ig_md.stats_ip.mean_ss = ig_md.stats_ip.ss >> 9;
	}

	action rshift_mean_10() {
		ig_md.stats_ip.mean_0 = ig_md.stats_ip.pkt_len >> 10;
		ig_md.stats_ip.mean_ss = ig_md.stats_ip.ss >> 10;
	}

	action rshift_mean_11() {
		ig_md.stats_ip.mean_0 = ig_md.stats_ip.pkt_len >> 11;
		ig_md.stats_ip.mean_ss = ig_md.stats_ip.ss >> 11;
	}

	action rshift_mean_12() {
		ig_md.stats_ip.mean_0 = ig_md.stats_ip.pkt_len >> 12;
		ig_md.stats_ip.mean_ss = ig_md.stats_ip.ss >> 12;
	}

	action rshift_mean_13() {
		ig_md.stats_ip.mean_0 = ig_md.stats_ip.pkt_len >> 13;
		ig_md.stats_ip.mean_ss = ig_md.stats_ip.ss >> 13;
	}

	action rshift_mean_14() {
		ig_md.stats_ip.mean_0 = ig_md.stats_ip.pkt_len >> 14;
		ig_md.stats_ip.mean_ss = ig_md.stats_ip.ss >> 14;
	}

	action rshift_mean_15() {
		ig_md.stats_ip.mean_0 = ig_md.stats_ip.pkt_len >> 15;
		ig_md.stats_ip.mean_ss = ig_md.stats_ip.ss >> 15;
	}

	action miss() {}

    table decay_check {
        key = {
            ig_md.meta.decay_cntr : exact;
        }
        actions = {
            decay_check_100_ms;
            decay_check_1_s;
            decay_check_10_s;
            decay_check_60_s;
            miss;
        }
        const default_action = miss;
        size = 1024;
    }

	table pkt_mean {
		key = {
			ig_md.stats_ip.pkt_cnt_0 : ternary;
		}
		actions = {
			rshift_mean_1;
			rshift_mean_2;
			rshift_mean_3;
			rshift_mean_4;
			rshift_mean_5;
			rshift_mean_6;
			rshift_mean_7;
			rshift_mean_8;
			rshift_mean_9;
			rshift_mean_10;
			rshift_mean_11;
			rshift_mean_12;
			rshift_mean_13;
			rshift_mean_14;
			rshift_mean_15;
			miss;
		}
		const default_action = miss;
		size = 1024;
	}

	// ----------------------------------------
	// Apply
	// ----------------------------------------

	apply {

		// Hash calculation.
		hash_calc_ip_0();
		hash_calc_ip_1();

		ig_md.hash.ip_0 = ig_md.hash.ip_0 + ig_md.meta.decay_cntr;
		ig_md.hash.ip_1 = ig_md.hash.ip_1 + ig_md.meta.decay_cntr;

	    // Check if more than 60 secs have elapsed since the last update for the current flow.
		decay_check.apply();

		// Increment the current packet count and length.
		pkt_cnt_0_incr();
		pkt_len_incr();

		// Squared sum (packet length) calculation.
		ss_calc();

		// Mean calculation using right bit-shift.
		// Equivalent to pkt length / pkt count.
		// Division is performed by rounding up the current pkt count to a power of 2.
		// Additionally, we also calculate the mean for the squared sum values.
		pkt_mean.apply();

		// SR - Residue calculation.
		residue_calc();

		// Squared mean 0 calculation.
		mean_squared_0_calc();

		// Variance 0 calculation.
		variance_0_calc();

		if (ig_md.stats_ip.pkt_cnt_0 % 1024 != 0) {

			// Update the current pkt cnt 0 value on pkt cnt register 1.
			ract_pkt_cnt_1_incr.execute(ig_md.hash.ip_0);

			// Update the stored mean 0 value.
			ract_mean_0_write.execute(ig_md.hash.ip_0);

			// Update the stored variance 0 value.
			ract_variance_0_write.execute(ig_md.hash.ip_0);

			// Update the current last residue value.
			ract_last_res_write.execute(ig_md.hash.ip_0);

		} else {

			// Read the current pkt cnt 1 value.
			pkt_cnt_1_read();

			// Read the current mean 1 value.
			mean_1_read();

			// Read the current variance 1 value.
			variance_1_read();

			// Read the current last residue 1 value.
			last_res_1_read();
		}
	}
}
