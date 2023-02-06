#include <iostream>

#include "kitnet_client.h"

namespace peregrine {

uint64_t mac_to_uint64(const mac_t& mac) {
	uint64_t value = 0;
	
	for (auto byte = 0u; byte < 6; byte++) {
		value <<= 8;
		value |= mac[byte];
	}

	return value;
}

float KitNetClient::ProcessSample(const sample_t& sample) {
	ProcessSampleRequest request;
	
	request.set_mac_src(mac_to_uint64(sample.mac_src));
	request.set_ip_src(sample.ip_src);
	request.set_ip_dst(sample.ip_dst);
	request.set_ip_proto(sample.ip_proto);
	request.set_port_src(sample.port_src);
	request.set_port_dst(sample.port_dst);
	request.set_decay(sample.decay);
	request.set_mac_ip_src_pkt_cnt(sample.mac_ip_src_pkt_cnt);
	request.set_mac_ip_src_mean(sample.mac_ip_src_mean);
	request.set_mac_ip_src_std_dev(sample.mac_ip_src_std_dev);
	request.set_ip_src_pkt_cnt(sample.ip_src_pkt_cnt);
	request.set_ip_src_mean(sample.ip_src_mean);
	request.set_ip_src_std_dev(sample.ip_src_std_dev);
	request.set_ip_pkt_cnt(sample.ip_pkt_cnt);
	request.set_ip_mean_0(sample.ip_mean_0);
	request.set_ip_std_dev_0(sample.ip_std_dev_0);
	request.set_ip_magnitude(sample.ip_magnitude);
	request.set_ip_radius(sample.ip_radius);
	request.set_five_t_pkt_cnt(sample.five_t_pkt_cnt);
	request.set_five_t_mean_0(sample.five_t_mean_0);
	request.set_five_t_std_dev_0(sample.five_t_std_dev_0);
	request.set_five_t_magnitude(sample.five_t_magnitude);
	request.set_five_t_radius(sample.five_t_radius);
	request.set_ip_sum_res_prod_cov(sample.ip_sum_res_prod_cov);
	request.set_ip_pcc(sample.ip_pcc);
	request.set_five_t_sum_res_prod_cov(sample.five_t_sum_res_prod_cov);
	request.set_five_t_pcc(sample.five_t_pcc);

	ProcessSampleReply reply;
	grpc::ClientContext context;
	grpc::Status status = stub_->ProcessSample(&context, request, &reply);

	if (status.ok()) {
		return reply.rmse();
	} else {
		std::cerr << status.error_code() << ": " << status.error_message()
				  << std::endl;
		return -1;
	}
}

}  // namespace peregrine