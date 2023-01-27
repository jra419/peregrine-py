#include <iostream>
#include <memory>
#include <string>

#include "kitnet_client.h"
#include "listener.h"

#define DEFAULT_MODEL_GRPC_TARGET "localhost:50051"

void print_header() {
	std::cerr << "\n";
	std::cerr << "*******************************************\n";
	std::cerr << "*                                         *\n";
	std::cerr << "*           PEREGRINE ENGINE              *\n";
	std::cerr << "*                                         *\n";
	std::cerr << "*******************************************\n";
	std::cerr << "\n";
}

struct args_t {
	std::string iface;
	std::string grpc_target;

	args_t(int argc, char** argv) : grpc_target(DEFAULT_MODEL_GRPC_TARGET) {
		if (argc < 3) {
			usage(argv);
		}

		parse_help(argc, argv);
		parse_iface(argc, argv);
		parse_grpc_port(argc, argv);
	}

	void usage(char** argv) const {
		std::cerr << "Usage: " << argv[0]
				  << " -i iface [-t target] [-h|--help]\n";
		std::cerr << "Default values:\n";
		std::cerr << "  target=" << DEFAULT_MODEL_GRPC_TARGET << "\n";
		exit(1);
	}

	void parse_help(int argc, char** argv) {
		auto args_str = std::vector<std::string>{
			std::string("-h"),
			std::string("--help"),
		};

		for (auto argi = 1u; argi < argc - 1; argi++) {
			auto arg = std::string(argv[argi]);

			for (auto arg_str : args_str) {
				auto cmp = arg.compare(arg_str);

				if (cmp == 0) {
					usage(argv);
				}
			}
		}
	}

	void parse_iface(int argc, char** argv) {
		auto arg_str = std::string("-i");

		for (auto argi = 1u; argi < argc - 1; argi++) {
			auto arg = std::string(argv[argi]);
			auto cmp = arg.compare(arg_str);

			if (cmp == 0) {
				iface = std::string(argv[argi + 1]);
				return;
			}
		}

		std::cerr << "Option -i not found.\n";
		usage(argv);
	}

	void parse_grpc_port(int argc, char** argv) {
		std::string arg_str("-t");

		for (auto argi = 1u; argi < argc - 1; argi++) {
			auto arg = std::string(argv[argi]);
			auto cmp = arg.compare(arg_str);

			if (cmp == 0) {
				grpc_target = std::string(argv[argi + 1]);
				return;
			}
		}
	}

	void dump() const {
		std::cerr << "Configuration:\n";
		std::cerr << "  iface:       " << iface << "\n";
		std::cerr << "  grpc target: " << grpc_target << "\n";
		std::cerr << "\n";
	}
};

int main(int argc, char** argv) {
	auto args = args_t(argc, argv);

	print_header();
	args.dump();

	auto kitnet = peregrine::KitNetClient(grpc::CreateChannel(
		args.grpc_target, grpc::InsecureChannelCredentials()));

	auto listener = peregrine::Listener(args.iface);

	while (1) {
		auto sample = listener.receive_sample();
		auto reply = kitnet.ProcessSample(sample);
		std::cerr << "reply: " << reply << "\n";
	}

	return 0;
}
