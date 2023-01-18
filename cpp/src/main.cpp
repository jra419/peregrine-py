#include <signal.h>
#include <unistd.h>

#include <iostream>
#include <sstream>

#include "peregrine.h"

void signalHandler(int signum) {
	std::cerr << "Exiting\n";
	exit(signum);
}

struct args_t {
	bool model;
	std::string topology_file_path;

	args_t(int argc, char **argv) : model(false) {
		if (argc < 2) {
			std::cerr << "Usage: " << argv[0] << " topology [--model]\n";
			exit(1);
		}

		topology_file_path = std::string(argv[1]);

		if (argc > 2 && strncmp(argv[2], "--model", 7) == 0) {
			model = true;
		}
	}
};

int main(int argc, char **argv) {
	signal(SIGINT, signalHandler);
	args_t args(argc, argv);

	peregrine::init_bf_switchd();
	peregrine::setup_controller(args.topology_file_path, args.model);
	peregrine::run(args.model);

	// main thread sleeps
	std::cerr << "zzzzz...\n";
	while (1) {
		sleep(5);
	}

	return 0;
}