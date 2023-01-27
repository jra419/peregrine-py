#pragma once

#include "packet.h"
#include "sample.h"

#include <assert.h>
#include <vector>
#include <fstream>
#include <iostream>

namespace peregrine {

struct report_entry_t {
	mac_t mac_src;
	ipv4_t ip_src;
	ipv4_t ip_dst;
	uint8_t ip_proto;
	port_t port_src;
	port_t port_dst;
	float rmse;

	report_entry_t(const report_entry_t& _report)
		: ip_src(_report.ip_src),
		  ip_dst(_report.ip_dst),
		  ip_proto(_report.ip_proto),
		  port_src(_report.port_src),
		  port_dst(_report.port_dst),
		  rmse(_report.rmse) {
		assert(sizeof(mac_src) == sizeof(_report.mac_src));
		for (auto byte = 0u; byte < sizeof(mac_src); byte++) {
			mac_src[byte] = _report.mac_src[byte];
		}
	}

	report_entry_t(const sample_t& _sample, float _rmse)
		: ip_src(_sample.ip_src),
		  ip_dst(_sample.ip_dst),
		  ip_proto(_sample.ip_proto),
		  port_src(_sample.port_src),
		  port_dst(_sample.port_dst),
		  rmse(_rmse) {
		assert(sizeof(mac_src) == sizeof(_sample.mac_src));
		for (auto byte = 0u; byte < sizeof(mac_src); byte++) {
			mac_src[byte] = _sample.mac_src[byte];
		}
	}
};

struct report_t {
	std::vector<report_entry_t> entries;

	void add(const sample_t& sample, float rmse) {
		entries.emplace_back(sample, rmse);
	}

	void dump(const std::string& report_filename) const {
		auto ofs = std::ofstream(report_filename);

		ofs << "#src mac\tsrc ip\tdst ip\tproto\tsrc port\tdst port\trmse\n";

		if (!ofs.is_open()) {
			std::cerr << "ERROR: couldn't write to \"" << report_filename
					  << "\n";
			exit(1);
		}

		for (auto entry : entries) {
			ofs << mac_to_str(entry.mac_src);
			ofs << "\t";
			ofs << ip_to_str(entry.ip_src);
			ofs << "\t";
			ofs << ip_to_str(entry.ip_dst);
			ofs << "\t";
			ofs << int(entry.ip_proto);
			ofs << "\t";
			ofs << port_to_str(entry.port_src);
			ofs << "\t";
			ofs << port_to_str(entry.port_dst);
			ofs << "\t";
			ofs << entry.rmse;
			ofs << "\n";
		}

		ofs.close();
	}
};

}  // namespace peregrine
