#include "peregrine.h"

#include <iostream>
#include <sstream>
#include <signal.h>
#include <unistd.h>

void signalHandler(int signum) {
	std::cerr << "Exiting\n";
	exit(signum);
}

int main(int argc, char **argv) {
	signal(SIGINT, signalHandler);

	bool model = false;

	if (argc > 1 && strncmp(argv[1], "--model", 7) == 0) {
		model = true;
	}

	peregrine::init_bf_switchd();
	peregrine::setup_controller();
	peregrine::run(model);

	// // main thread sleeps
	// std::cerr << "zzzzz...\n";
	// while (1) {
	// 	sleep(5);
	// }

	return 0;
}