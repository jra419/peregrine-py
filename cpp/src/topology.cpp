#include "topology.h"

#include <fstream>
#include <iostream>

#include "json.hpp"

namespace peregrine {
void from_json(const nlohmann::json &j, topo_port_t &topo_port) {
	j.at("port").get_to(topo_port.port);
	j.at("capacity").get_to(topo_port.capacity);
	j.at("comment").get_to(topo_port.comment);
}

void from_json(const nlohmann::json &j, topo_connection_t &topo_connection) {
	j.at("in").get_to(topo_connection.in);
	j.at("out").get_to(topo_connection.out);
}

void from_json(const nlohmann::json &j, topo_pipes_t &topo_pipes) {
	j.at("external").get_to(topo_pipes.external);
	j.at("internal").get_to(topo_pipes.internal);
}

void from_json(const nlohmann::json &j, topology_t &topo_connections) {
	j.at("connections").get_to(topo_connections.connections);
	j.at("pipes").get_to(topo_connections.pipes);
}

topology_t parse_topology_file(const std::string &topology_file_path) {
	auto topology_file = std::ifstream(topology_file_path);

	if (!topology_file.good()) {
		std::cerr << "Error opening \"" << topology_file_path
				  << "\". Exiting.\n";
		exit(1);
	}

	auto data = nlohmann::json::parse(topology_file);
	auto topology = data.get<topology_t>();

	for (auto connection : topology.connections) {
		std::cerr << "Connection:\n";
		std::cerr << "  [in]  port     " << connection.in.port << "\n";
		std::cerr << "  [in]  capacity " << connection.in.capacity << "\n";
		std::cerr << "  [in]  comment  " << connection.in.comment << "\n";

		std::cerr << "  [out] port     " << connection.out.port << "\n";
		std::cerr << "  [out] capacity " << connection.out.capacity << "\n";
		std::cerr << "  [out] comment  " << connection.out.comment << "\n";
	}

	assert(topology.pipes.external.size() == topology.pipes.internal.size());
	return topology;
}
}  // namespace peregrine