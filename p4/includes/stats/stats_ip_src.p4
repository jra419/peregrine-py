control c_stats_ip_src(inout header_t hdr, inout ingress_metadata_a_t ig_md) {

    // ----------------------------------------
    // Hashes
    // ----------------------------------------

    Hash<bit<16>>(HashAlgorithm_t.CRC16) hash_ip_src;

    // ----------------------------------------
    // Registers and temp. variables
    // ----------------------------------------

    Register<bit<32>, _>(REG_SIZE) reg_ip_src_ts;

    Register<bit<32>, _>(REG_SIZE) reg_ip_src_cnt;          // Packet count
    Register<bit<32>, _>(REG_SIZE) reg_ip_src_len;          // Packet length
    Register<bit<32>, _>(REG_SIZE) reg_ip_src_ss;           // Squared sum of the packet length

    /* Register<bit<32>, _>(REG_SIZE) reg_ip_src_mean;         // Mean */
    Register<bit<32>, _>(REG_SIZE) reg_ip_src_mean_squared; // Squared mean

    /* Register<bit<32>, _>(REG_SIZE) reg_ip_src_std_dev;      // Std. deviation */

    // ----------------------------------------
    // Register actions
    // ----------------------------------------

	// Check if more than 60 secs have elapsed since the last update for the current flow.
	// If so, increase the stored value by 60 secs and set a flag.
	// 915527 corresponds to the bit-sliced value for 60 secs (in ns).
    RegisterAction<_, _, bit<32>>(reg_ip_src_ts) ract_decay_check = {
        void apply(inout bit<32> value, out bit<32> result) {
            result = 0;
            if (ig_md.meta.current_ts - value > 915527 && value != 0) {
                    value = value + 915527;
                    result = 1;
            } else {
                value = ig_md.meta.current_ts;
            }
        }
    };

    MathUnit<bit<32>>(MathOp_t.MUL, 1, 2) div_pkt_cnt;
    RegisterAction<_, _, bit<32>>(reg_ip_src_cnt) ract_pkt_cnt_incr = {
        void apply(inout bit<32> value, out bit<32> result) {
            if (ig_md.stats_ip_src.decay_check == 0) {
                value = value + 1;
            } else {
                value = div_pkt_cnt.execute(value) + 1;
            }
            result = value;
        }
    };

    MathUnit<bit<32>>(MathOp_t.MUL, 1, 2) div_pkt_len;
    RegisterAction<_, _, bit<32>>(reg_ip_src_len) ract_pkt_len_incr = {
        void apply(inout bit<32> value, out bit<32> result) {
            if (ig_md.stats_ip_src.decay_check == 0) {
                value = value + (bit<32>)hdr.ipv4.len;
            } else {
                value = div_pkt_len.execute(value);
            }
            result = value;
        }
    };

    MathUnit<bit<32>>(MathOp_t.MUL, 1, 2) div_ss;
    RegisterAction<_, _, bit<32>>(reg_ip_src_ss) ract_ss_calc = {
        void apply(inout bit<32> value, out bit<32> result) {
            if (ig_md.stats_ip_src.decay_check == 0) {
                value = value + ig_md.meta.pkt_len_squared;
            } else {
                value = div_ss.execute(value);
            }
            result = value;
        }
    };

    /*
    RegisterAction<_, _, bit<32>>(reg_ip_src_mean) ract_mean_write = {
        void apply(inout bit<32> value) {
            value = ig_md.stats_ip_src.mean_0;
        }
    };
    */

    MathUnit<bit<32>>(MathOp_t.SQR, 1) square_mean;
    RegisterAction<_, _, bit<32>>(reg_ip_src_mean_squared) ract_mean_squared_calc = {
        void apply(inout bit<32> value, out bit<32> result) {
            value = square_mean.execute(ig_md.stats_ip_src.mean_0);
            result = value;
        }
    };

    /*
    MathUnit<bit<32>>(MathOp_t.SQRT, 1) sqrt_std_dev;
	RegisterAction<_, _, bit<32>>(reg_ip_src_std_dev) ract_std_dev_calc = {
		void apply(inout bit<32> value, out bit<32> result) {
			value = sqrt_std_dev.execute(ig_md.stats_ip_src.variance_0);
			result = value;
		}
	};

	MathUnit<bit<32>>(MathOp_t.SQRT, 1) sqrt_std_dev_neg;
	RegisterAction<_, _, bit<32>>(reg_ip_src_std_dev) ract_std_dev_calc_neg = {
		void apply(inout bit<32> value, out bit<32> result) {
			value = sqrt_std_dev_neg.execute(ig_md.stats_ip_src.variance_0_neg);
			result = value;
		}
	};
    */

    // ----------------------------------------
    // Actions
    // ----------------------------------------

    action hash_calc_ip_src() {
        ig_md.hash.ip_src = hash_ip_src.get({hdr.ipv4.src_addr});
    }

    action decay_check() {
        ig_md.stats_ip_src.decay_check = ract_decay_check.execute(ig_md.hash.ip_src);
    }

    action pkt_cnt_incr() {
        ig_md.stats_ip_src.pkt_cnt_0 = ract_pkt_cnt_incr.execute(ig_md.hash.ip_src);
    }

    action pkt_len_incr() {
        ig_md.stats_ip_src.pkt_len = ract_pkt_len_incr.execute(ig_md.hash.ip_src);
    }

    action ss_calc() {
        ig_md.stats_ip_src.ss = ract_ss_calc.execute(ig_md.hash.ip_src);
    }

	action mean_squared_calc() {
		ig_md.stats_ip_src.mean_squared_0 = ract_mean_squared_calc.execute(ig_md.hash.ip_src);
	}

	action variance_calc() {
		ig_md.stats_ip_src.variance_0 = ig_md.stats_ip_src.mean_squared_0 - ig_md.stats_ip_src.mean_ss;
		ig_md.stats_ip_src.variance_0_neg = ig_md.stats_ip_src.mean_ss - ig_md.stats_ip_src.mean_squared_0;
	}

    /*
	action std_dev_calc() {
		ig_md.stats_ip_src.std_dev_0 = ract_std_dev_calc.execute(ig_md.hash.ip_src);
	}

	action std_dev_calc_neg() {
		ig_md.stats_ip_src.std_dev_0 = ract_std_dev_calc_neg.execute(ig_md.hash.ip_src);
	}
    */

	action rshift_mean_1() {
		ig_md.stats_ip_src.mean_0 = ig_md.stats_ip_src.pkt_len >> 1;
		ig_md.stats_ip_src.mean_ss = ig_md.stats_ip_src.ss >> 1;
	}

	action rshift_mean_2() {
		ig_md.stats_ip_src.mean_0 = ig_md.stats_ip_src.pkt_len >> 2;
		ig_md.stats_ip_src.mean_ss = ig_md.stats_ip_src.ss >> 2;
	}

	action rshift_mean_3() {
		ig_md.stats_ip_src.mean_0 = ig_md.stats_ip_src.pkt_len >> 3;
		ig_md.stats_ip_src.mean_ss = ig_md.stats_ip_src.ss >> 3;
	}

	action rshift_mean_4() {
		ig_md.stats_ip_src.mean_0 = ig_md.stats_ip_src.pkt_len >> 4;
		ig_md.stats_ip_src.mean_ss = ig_md.stats_ip_src.ss >> 4;
	}

	action rshift_mean_5() {
		ig_md.stats_ip_src.mean_0 = ig_md.stats_ip_src.pkt_len >> 5;
		ig_md.stats_ip_src.mean_ss = ig_md.stats_ip_src.ss >> 5;
	}

	action rshift_mean_6() {
		ig_md.stats_ip_src.mean_0 = ig_md.stats_ip_src.pkt_len >> 6;
		ig_md.stats_ip_src.mean_ss = ig_md.stats_ip_src.ss >> 6;
	}

	action rshift_mean_7() {
		ig_md.stats_ip_src.mean_0 = ig_md.stats_ip_src.pkt_len >> 7;
		ig_md.stats_ip_src.mean_ss = ig_md.stats_ip_src.ss >> 7;
	}

	action rshift_mean_8() {
		ig_md.stats_ip_src.mean_0 = ig_md.stats_ip_src.pkt_len >> 8;
		ig_md.stats_ip_src.mean_ss = ig_md.stats_ip_src.ss >> 8;
	}

	action rshift_mean_9() {
		ig_md.stats_ip_src.mean_0 = ig_md.stats_ip_src.pkt_len >> 9;
		ig_md.stats_ip_src.mean_ss = ig_md.stats_ip_src.ss >> 9;
	}

	action rshift_mean_10() {
		ig_md.stats_ip_src.mean_0 = ig_md.stats_ip_src.pkt_len >> 10;
		ig_md.stats_ip_src.mean_ss = ig_md.stats_ip_src.ss >> 10;
	}

	action rshift_mean_11() {
		ig_md.stats_ip_src.mean_0 = ig_md.stats_ip_src.pkt_len >> 11;
		ig_md.stats_ip_src.mean_ss = ig_md.stats_ip_src.ss >> 11;
	}

	action rshift_mean_12() {
		ig_md.stats_ip_src.mean_0 = ig_md.stats_ip_src.pkt_len >> 12;
		ig_md.stats_ip_src.mean_ss = ig_md.stats_ip_src.ss >> 12;
	}

	action rshift_mean_13() {
		ig_md.stats_ip_src.mean_0 = ig_md.stats_ip_src.pkt_len >> 13;
		ig_md.stats_ip_src.mean_ss = ig_md.stats_ip_src.ss >> 13;
	}

	action rshift_mean_14() {
		ig_md.stats_ip_src.mean_0 = ig_md.stats_ip_src.pkt_len >> 14;
		ig_md.stats_ip_src.mean_ss = ig_md.stats_ip_src.ss >> 14;
	}

	action rshift_mean_15() {
		ig_md.stats_ip_src.mean_0 = ig_md.stats_ip_src.pkt_len >> 15;
		ig_md.stats_ip_src.mean_ss = ig_md.stats_ip_src.ss >> 15;
	}

    action miss() {}

    table pkt_mean {
		key = {
			ig_md.stats_ip_src.pkt_cnt_0 : ternary;
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
        hash_calc_ip_src();

	    // Check if more than 60 secs have elapsed since the last update for the current flow.
        decay_check();

        // Increment the current packet count and length.
        pkt_cnt_incr();
        pkt_len_incr();

        // Squared sum (packet length) calculation.
        ss_calc();

        // Mean calculation using right bit-shift.
        // Equivalent to pkt length / pkt count.
        // Division is performed by rounding up the current pkt count to a power of 2.
        // Additionally, we also calculate the mean for the squared sum values.
        pkt_mean.apply();

        // Update the stored mean 0 value.
        // ract_mean_write.execute(ig_md.hash.ip_src);

        // Squared mean calculation.
        mean_squared_calc();

        // Variance 0 calculation.
        variance_calc();

		if (ig_md.stats_ip_src.variance_0[31:31] != 0) {
			ig_md.stats_ip_src.variance_0 = ig_md.stats_ip_src.variance_0_neg;
		}

		// Std. dev 0 calculation.
        /*
		if (ig_md.stats_ip_src.variance_0[31:31] == 0) {
			std_dev_calc();
		} else {
			std_dev_calc_neg();
			ig_md.stats_ip_src.variance_0 = ig_md.stats_ip_src.variance_0_neg;
		}
        */
    }
}
