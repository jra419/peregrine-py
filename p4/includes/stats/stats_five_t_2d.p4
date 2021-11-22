control c_stats_five_t_2d(inout header_t hdr, inout ingress_metadata_b_t ig_md, in ingress_intrinsic_metadata_t ig_intr_md) {

	// ----------------------------------------
	// Hashes
	// ----------------------------------------

	Hash<bit<32>>(HashAlgorithm_t.CRC32) hash_five_t_0; // Hash for flow id (a->b)
	Hash<bit<32>>(HashAlgorithm_t.CRC32) hash_five_t_1; // Hash for flow id (b->a)

	// ----------------------------------------
	// Registers and temp. variables
	// ----------------------------------------

	Register<bit<32>, _>(REG_SIZE) reg_five_t_mean_squared_1;		// Squared mean for flow id (b->a)
	Register<bit<32>, _>(REG_SIZE) reg_five_t_variance_squared_0;	// Squared variance for flow id (a->b)
	Register<bit<32>, _>(REG_SIZE) reg_five_t_variance_squared_1;	// Squared variance for flow id (b->a)
	Register<bit<32>, _>(REG_SIZE) reg_five_t_std_dev_0;			// Std. deviation for flow id (a->b)
	Register<bit<32>, _>(REG_SIZE) reg_five_t_std_dev_1;			// Std. deviation for flow id (b->a)
	Register<bit<32>, _>(REG_SIZE) reg_five_t_last_res; 			// Residue values
	Register<bit<32>, _>(REG_SIZE) reg_five_t_sum_res_prod;			// Sum of residual products
	Register<bit<32>, _>(REG_SIZE) reg_five_t_magnitude; 			// Magnitude
	Register<bit<32>, _>(REG_SIZE) reg_five_t_radius;				// Radius

	// Temporary variables for stats calculation
	bit<32> magnitude_temp = 0;
	bit<32> radius_temp = 0;
	bit<32> res_prod = 0;

	// ----------------------------------------
	// Register actions
	// ----------------------------------------

	MathUnit<bit<32>>(MathOp_t.SQR, 1) square_mean_1;
	RegisterAction<_, _, bit<32>>(reg_five_t_mean_squared_1) ract_mean_squared_1_calc = {
		void apply(inout bit<32> value, out bit<32> result) {
			value = square_mean_1.execute(hdr.kitsune.five_t_mean_1);
			result = value;
		}
	};

	MathUnit<bit<32>>(MathOp_t.SQRT, 1) sqrt_std_dev_0;
	RegisterAction<_, _, bit<32>>(reg_five_t_std_dev_0) ract_std_dev_0_calc = {
		void apply(inout bit<32> value, out bit<32> result) {
			value = sqrt_std_dev_0.execute(hdr.kitsune.five_t_variance);
			result = value;
		}
	};

	MathUnit<bit<32>>(MathOp_t.SQRT, 1) sqrt_std_dev_0_neg;
	RegisterAction<_, _, bit<32>>(reg_five_t_std_dev_0) ract_std_dev_0_calc_neg = {
		void apply(inout bit<32> value, out bit<32> result) {
			value = sqrt_std_dev_0_neg.execute(hdr.kitsune.five_t_variance_neg);
			result = value;
		}
	};

	MathUnit<bit<32>>(MathOp_t.SQRT, 1) sqrt_std_dev_1;
	RegisterAction<_, _, bit<32>>(reg_five_t_std_dev_1) ract_std_dev_1_calc = {
		void apply(inout bit<32> value, out bit<32> result) {
			value = sqrt_std_dev_1.execute(hdr.kitsune.five_t_variance_1);
			result = value;
		}
	};

	MathUnit<bit<32>>(MathOp_t.SQRT, 1) sqrt_magnitude;
	RegisterAction<_, _, bit<32>>(reg_five_t_magnitude) ract_magnitude_calc = {
		void apply(inout bit<32> value, out bit<32> result) {
			value = sqrt_magnitude.execute(magnitude_temp);
			result = value;
		}
	};

	MathUnit<bit<32>>(MathOp_t.SQR, 1) square_variance_0;
	RegisterAction<_, _, bit<32>>(reg_five_t_variance_squared_0) ract_variance_squared_0_calc = {
		void apply(inout bit<32> value, out bit<32> result) {
			value = square_variance_0.execute(hdr.kitsune.five_t_variance);
			result = value;
		}
	};

	MathUnit<bit<32>>(MathOp_t.SQR, 1) square_variance_1;
	RegisterAction<_, _, bit<32>>(reg_five_t_variance_squared_1) ract_variance_squared_1_calc = {
		void apply(inout bit<32> value, out bit<32> result) {
			value = square_variance_1.execute(hdr.kitsune.five_t_variance_1);
			result = value;
		}
	};

	MathUnit<bit<32>>(MathOp_t.SQRT, 1) sqrt_radius;
	RegisterAction<_, _, bit<32>>(reg_five_t_radius) ract_radius_calc = {
		void apply(inout bit<32> value, out bit<32> result) {
			value = sqrt_radius.execute(radius_temp);
			result = value;
		}
	};

	RegisterAction<_, _, bit<32>>(reg_five_t_sum_res_prod) ract_sum_res_prod_incr = {
		void apply(inout bit<32> value, out bit<32> result) {
			value = value + hdr.kitsune.five_t_last_res;
			result = value;
		}
	};

	// ----------------------------------------
	// Actions
	// ----------------------------------------

	action hash_calc_five_t_0() {
		ig_md.hash.five_t_0 = (bit<32>)hash_five_t_0.get({hdr.ipv4.src_addr,
										   				  hdr.ipv4.dst_addr,
										   				  hdr.ipv4.protocol,
										   				  ig_md.meta.l4_src_port,
										   				  ig_md.meta.l4_dst_port})[13:0];
	}

	action hash_calc_five_t_1() {
		ig_md.hash.five_t_1 = (bit<32>)hash_five_t_1.get({hdr.ipv4.dst_addr,
										   				  hdr.ipv4.src_addr,
										   				  hdr.ipv4.protocol,
										   				  ig_md.meta.l4_dst_port,
										   				  ig_md.meta.l4_src_port})[13:0];
	}

	action mean_squared_1_calc() {
		ig_md.stats_five_t.mean_squared_1 = ract_mean_squared_1_calc.execute(ig_md.hash.five_t_1);
	}

	action std_dev_0_calc() {
		ig_md.stats_five_t.std_dev_0 = ract_std_dev_0_calc.execute(ig_md.hash.five_t_0);
	}

	action std_dev_0_calc_neg() {
		ig_md.stats_five_t.std_dev_0 = ract_std_dev_0_calc_neg.execute(ig_md.hash.five_t_0);
	}

	action std_dev_1_calc() {
		ig_md.stats_five_t.std_dev_1 = ract_std_dev_1_calc.execute(ig_md.hash.five_t_1);
	}

	action magnitude_calc() {
		ig_md.stats_five_t.magnitude = ract_magnitude_calc.execute(ig_md.hash.five_t_0);
	}

	action variance_squared_0_calc() {
		ig_md.stats_five_t.variance_squared_0 = ract_variance_squared_0_calc.execute(ig_md.hash.five_t_0);
	}

	action variance_squared_1_calc() {
		ig_md.stats_five_t.variance_squared_1 = ract_variance_squared_1_calc.execute(ig_md.hash.five_t_1);
	}

	action radius_calc() {
		ig_md.stats_five_t.radius = ract_radius_calc.execute(ig_md.hash.five_t_0);
	}

	action sum_res_prod() {
		ig_md.stats_five_t.sum_res_prod = ract_sum_res_prod_incr.execute(ig_md.hash.five_t_0);
	}

	action rshift_cov_1() {
		ig_md.stats_five_t.cov = ig_md.stats_five_t.sum_res_prod >> 1;
	}

	action rshift_cov_2() {
		ig_md.stats_five_t.cov = ig_md.stats_five_t.sum_res_prod >> 2;
	}

	action rshift_cov_3() {
		ig_md.stats_five_t.cov = ig_md.stats_five_t.sum_res_prod >> 3;
	}

	action rshift_cov_4() {
		ig_md.stats_five_t.cov = ig_md.stats_five_t.sum_res_prod >> 4;
	}

	action rshift_cov_5() {
		ig_md.stats_five_t.cov = ig_md.stats_five_t.sum_res_prod >> 5;
	}

	action rshift_cov_6() {
		ig_md.stats_five_t.cov = ig_md.stats_five_t.sum_res_prod >> 6;
	}

	action rshift_cov_7() {
		ig_md.stats_five_t.cov = ig_md.stats_five_t.sum_res_prod >> 7;
	}

	action rshift_cov_8() {
		ig_md.stats_five_t.cov = ig_md.stats_five_t.sum_res_prod >> 8;
	}

	action rshift_cov_9() {
		ig_md.stats_five_t.cov = ig_md.stats_five_t.sum_res_prod >> 9;
	}

	action rshift_cov_10() {
		ig_md.stats_five_t.cov = ig_md.stats_five_t.sum_res_prod >> 10;
	}

	action rshift_cov_11() {
		ig_md.stats_five_t.cov = ig_md.stats_five_t.sum_res_prod >> 11;
	}

	action rshift_cov_12() {
		ig_md.stats_five_t.cov = ig_md.stats_five_t.sum_res_prod >> 12;
	}

	action rshift_cov_13() {
		ig_md.stats_five_t.cov = ig_md.stats_five_t.sum_res_prod >> 13;
	}

	action rshift_cov_14() {
		ig_md.stats_five_t.cov = ig_md.stats_five_t.sum_res_prod >> 14;
	}

	action rshift_cov_15() {
		ig_md.stats_five_t.cov = ig_md.stats_five_t.sum_res_prod >> 15;
	}

	action rshift_std_dev_1_1() {
		ig_md.stats_five_t.std_dev_1 = hdr.kitsune.five_t_std_dev_0 >> 1;
	}

	action rshift_std_dev_1_2() {
		ig_md.stats_five_t.std_dev_1 = hdr.kitsune.five_t_std_dev_0 >> 2;
	}

	action rshift_std_dev_1_3() {
		ig_md.stats_five_t.std_dev_1 = hdr.kitsune.five_t_std_dev_0 >> 3;
	}

	action rshift_std_dev_1_4() {
		ig_md.stats_five_t.std_dev_1 = hdr.kitsune.five_t_std_dev_0 >> 4;
	}

	action rshift_std_dev_1_5() {
		ig_md.stats_five_t.std_dev_1 = hdr.kitsune.five_t_std_dev_0 >> 5;
	}

	action rshift_std_dev_1_6() {
		ig_md.stats_five_t.std_dev_1 = hdr.kitsune.five_t_std_dev_0 >> 6;
	}

	action rshift_std_dev_1_7() {
		ig_md.stats_five_t.std_dev_1 = hdr.kitsune.five_t_std_dev_0 >> 7;
	}

	action rshift_std_dev_1_8() {
		ig_md.stats_five_t.std_dev_1 = hdr.kitsune.five_t_std_dev_0 >> 8;
	}

	action rshift_std_dev_1_9() {
		ig_md.stats_five_t.std_dev_1 = hdr.kitsune.five_t_std_dev_0 >> 9;
	}

	action rshift_std_dev_1_10() {
		ig_md.stats_five_t.std_dev_1 = hdr.kitsune.five_t_std_dev_0 >> 10;
	}

	action rshift_std_dev_1_11() {
		ig_md.stats_five_t.std_dev_1 = hdr.kitsune.five_t_std_dev_0 >> 11;
	}

	action rshift_std_dev_1_12() {
		ig_md.stats_five_t.std_dev_1 = hdr.kitsune.five_t_std_dev_0 >> 12;
	}

	action rshift_std_dev_1_13() {
		ig_md.stats_five_t.std_dev_1 = hdr.kitsune.five_t_std_dev_0 >> 13;
	}

	action rshift_std_dev_1_14() {
		ig_md.stats_five_t.std_dev_1 = hdr.kitsune.five_t_std_dev_0 >> 14;
	}

	action rshift_std_dev_1_15() {
		ig_md.stats_five_t.std_dev_1 = hdr.kitsune.five_t_std_dev_0 >> 15;
	}

	action rshift_pcc_1() {
		ig_md.stats_five_t.pcc = ig_md.stats_five_t.cov >> 1;
	}

	action rshift_pcc_2() {
		ig_md.stats_five_t.pcc = ig_md.stats_five_t.cov >> 2;
	}

	action rshift_pcc_3() {
		ig_md.stats_five_t.pcc = ig_md.stats_five_t.cov >> 3;
	}

	action rshift_pcc_4() {
		ig_md.stats_five_t.pcc = ig_md.stats_five_t.cov >> 4;
	}

	action rshift_pcc_5() {
		ig_md.stats_five_t.pcc = ig_md.stats_five_t.cov >> 5;
	}

	action rshift_pcc_6() {
		ig_md.stats_five_t.pcc = ig_md.stats_five_t.cov >> 6;
	}

	action rshift_pcc_7() {
		ig_md.stats_five_t.pcc = ig_md.stats_five_t.cov >> 7;
	}

	action rshift_pcc_8() {
		ig_md.stats_five_t.pcc = ig_md.stats_five_t.cov >> 8;
	}

	action rshift_pcc_9() {
		ig_md.stats_five_t.pcc = ig_md.stats_five_t.cov >> 9;
	}

	action rshift_pcc_10() {
		ig_md.stats_five_t.pcc = ig_md.stats_five_t.cov >> 10;
	}

	action rshift_pcc_11() {
		ig_md.stats_five_t.pcc = ig_md.stats_five_t.cov >> 11;
	}

	action rshift_pcc_12() {
		ig_md.stats_five_t.pcc = ig_md.stats_five_t.cov >> 12;
	}

	action rshift_pcc_13() {
		ig_md.stats_five_t.pcc = ig_md.stats_five_t.cov >> 13;
	}

	action rshift_pcc_14() {
		ig_md.stats_five_t.pcc = ig_md.stats_five_t.cov >> 14;
	}

		action rshift_pcc_15() {
		ig_md.stats_five_t.pcc = ig_md.stats_five_t.cov >> 15;
	}

	action miss() {}

	table cov {
		key = {
			hdr.kitsune.five_t_pkt_cnt_1 : ternary;
		}
		actions = {
			rshift_cov_1;
			rshift_cov_2;
			rshift_cov_3;
			rshift_cov_4;
			rshift_cov_5;
			rshift_cov_6;
			rshift_cov_7;
			rshift_cov_8;
			rshift_cov_9;
			rshift_cov_10;
			rshift_cov_11;
			rshift_cov_12;
			rshift_cov_13;
			rshift_cov_14;
			rshift_cov_15;
			miss;
		}
		const default_action = miss;
		size = 1024;
	}

	table std_dev_1 {
		key = {
			hdr.kitsune.five_t_std_dev_0 : ternary;
		}
		actions = {
			rshift_std_dev_1_1;
			rshift_std_dev_1_2;
			rshift_std_dev_1_3;
			rshift_std_dev_1_4;
			rshift_std_dev_1_5;
			rshift_std_dev_1_6;
			rshift_std_dev_1_7;
			rshift_std_dev_1_8;
			rshift_std_dev_1_9;
			rshift_std_dev_1_10;
			rshift_std_dev_1_11;
			rshift_std_dev_1_12;
			rshift_std_dev_1_13;
			rshift_std_dev_1_14;
			rshift_std_dev_1_15;
			miss;
		}
		const default_action = miss;
		size = 1024;
	}

	table pcc {
		key = {
			ig_md.stats_five_t.std_dev_1 : ternary;
		}
		actions = {
			rshift_pcc_1;
			rshift_pcc_2;
			rshift_pcc_3;
			rshift_pcc_4;
			rshift_pcc_5;
			rshift_pcc_6;
			rshift_pcc_7;
			rshift_pcc_8;
			rshift_pcc_9;
			rshift_pcc_10;
			rshift_pcc_11;
			rshift_pcc_12;
			rshift_pcc_13;
			rshift_pcc_14;
			rshift_pcc_15;
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
		hash_calc_five_t_0();
		hash_calc_five_t_1();

		// Squared mean 1 calculation.
		mean_squared_1_calc();

		// Std. dev 0 calculation.
		if (hdr.kitsune.five_t_variance[31:31] == 0) {
			std_dev_0_calc();
		} else {
			std_dev_0_calc_neg();
			hdr.kitsune.five_t_variance = hdr.kitsune.five_t_variance_neg;
		}

		// Std. dev 1 calculation.
		std_dev_1_calc();

		// Variance squared calculation.
		variance_squared_0_calc();
		variance_squared_1_calc();

		// Magnitude calculation.

		magnitude_temp = hdr.kitsune.five_t_mean_squared_0 + ig_md.stats_five_t.mean_squared_1;
		magnitude_calc();

		// Radius calculation.

		radius_temp = ig_md.stats_five_t.variance_squared_0 + ig_md.stats_five_t.variance_squared_1;
		radius_calc();

		// Approx. Covariance calculation.

		sum_res_prod();

		// Weight 1 + Weight 2
		hdr.kitsune.five_t_pkt_cnt_1 = hdr.kitsune.five_t_pkt_cnt_1 + hdr.kitsune.five_t_pkt_cnt;

		cov.apply();

		// Correlation Coefficient calculation.

		std_dev_1.apply();
		pcc.apply();
	}
}
