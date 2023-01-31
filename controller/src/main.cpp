#include <signal.h>
#include <unistd.h>

#include <iostream>
#include <sstream>
#include <fstream>

#include "peregrine.h"

#define REPORT_FILE "peregrine-controller.tsv"

struct args_t {
	std::string topology_file_path;
	bool use_tofino_model;
	bool bf_prompt;

	args_t(int argc, char **argv) : use_tofino_model(false), bf_prompt(false) {
		if (argc < 2) {
			help(argc, argv);
		}

		parse_help(argc, argv);

		topology_file_path = std::string(argv[1]);

		parse_model_flag(argc, argv);
		parse_bf_prompt_flag(argc, argv);
	}

	void help(int argc, char **argv) {
		std::cerr << "Usage: " << argv[0]
				  << " topology  [--bf-prompt] [--model] [-h|--help]\n";
		exit(0);
	}

	void parse_model_flag(int argc, char **argv) {
		std::string target = "--model";

		for (auto i = 1; i < argc; i++) {
			auto arg = std::string(argv[i]);
			if (arg.compare(target) == 0) {
				use_tofino_model = true;
				return;
			}
		}
	}

	void parse_bf_prompt_flag(int argc, char **argv) {
		std::string target = "--bf-prompt";

		for (auto i = 1; i < argc; i++) {
			auto arg = std::string(argv[i]);
			if (arg.compare(target) == 0) {
				bf_prompt = true;
				return;
			}
		}
	}

	void parse_help(int argc, char **argv) {
		auto targets = std::vector<std::string>{"-h", "--help"};

		for (auto i = 1; i < argc; i++) {
			auto arg = std::string(argv[i]);
			for (auto target : targets) {
				if (arg.compare(target) == 0) {
					help(argc, argv);
					return;
				}
			}
		}
	}

	void dump() const {
		std::cout << "\n";
		std::cout << "Configuration:\n";
		std::cout << "  topology:      " << topology_file_path << "\n";
		std::cout << "  model:         " << use_tofino_model << "\n";
		std::cout << "  bf prompt:     " << bf_prompt << "\n";
	}
};

void signalHandler(int signum) {
	auto topology = peregrine::Controller::controller->get_topology();
	auto use_tofino_model =
		peregrine::Controller::controller->get_use_tofino_model();

	auto ofs = std::ofstream(REPORT_FILE);

	ofs << "#port\trx\ttx\n";

	if (!ofs.is_open()) {
		std::cerr << "ERROR: couldn't write to \"" << REPORT_FILE << "\n";
		exit(1);
	}

	for (auto connection : topology.connections) {
		auto in_port = connection.in.port;

		if (!use_tofino_model) {
			in_port =
				peregrine::Controller::controller->get_dev_port(in_port, 0);
		}

		auto rx = peregrine::Controller::controller->get_port_rx(in_port);
		auto tx = peregrine::Controller::controller->get_port_tx(in_port);

		ofs << in_port << "\t" << rx << "\t" << tx << "\n";
	}

	auto stats_port = topology.stats.port;

	if (!use_tofino_model) {
		stats_port =
			peregrine::Controller::controller->get_dev_port(stats_port, 0);
	}

	auto rx = peregrine::Controller::controller->get_port_rx(stats_port);
	auto tx = peregrine::Controller::controller->get_port_tx(stats_port);

	ofs << stats_port << "\t" << rx << "\t" << tx << "\n";
	ofs.close();

	std::cout << "Report generated at \"" << REPORT_FILE << "\". Exiting.\n";

	exit(signum);
}

int main(int argc, char **argv) {
	signal(SIGINT, signalHandler);
	signal(SIGQUIT, signalHandler);
	signal(SIGTERM, signalHandler);

	args_t args(argc, argv);

	peregrine::init_bf_switchd(args.use_tofino_model, args.bf_prompt);
	peregrine::setup_controller(args.topology_file_path, args.use_tofino_model);

	args.dump();

	std::cerr << "\nPeregrine controller is ready.\n";

	// main thread sleeps
	while (1) {
		sleep(5);
	}

	return 0;
}