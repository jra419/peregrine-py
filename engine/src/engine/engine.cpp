#include <iostream>
#include <memory>
#include <string>

#include <grpcpp/grpcpp.h>

#include "../../autogen/kitnet.grpc.pb.h"

class KitNetClient {
public:
	KitNetClient(std::shared_ptr<grpc::Channel> channel)
		: stub_(KitNet::NewStub(channel)) {}

	// Assembles the client's payload, sends it and presents the response back
	// from the server.
	std::string SayHello(const std::string& user) {
		// Data we are sending to the server.
		HelloRequest request;
		request.set_name(user);

		// Container for the data we expect from the server.
		HelloReply reply;

		// Context for the client. It could be used to convey extra information
		// to the server and/or tweak certain RPC behaviors.
		grpc::ClientContext context;

		// The actual RPC.
		grpc::Status status = stub_->SayHello(&context, request, &reply);

		// Act upon its status.
		if (status.ok()) {
			return reply.message();
		} else {
			std::cout << status.error_code() << ": " << status.error_message()
					  << std::endl;
			return "RPC failed";
		}
	}

private:
	std::unique_ptr<KitNet::Stub> stub_;
};

int main(int argc, char** argv) {
	// Instantiate the client. It requires a channel, out of which the actual
	// RPCs are created. This channel models a connection to an endpoint
	// specified by the argument "--target=" which is the only expected
	// argument. We indicate that the channel isn't authenticated (use of
	// Insecuregrpc::ChannelCredentials()).
	std::string target_str;
	std::string arg_str("--target");
	if (argc > 1) {
		std::string arg_val = argv[1];
		size_t start_pos = arg_val.find(arg_str);
		if (start_pos != std::string::npos) {
			start_pos += arg_str.size();
			if (arg_val[start_pos] == '=') {
				target_str = arg_val.substr(start_pos + 1);
			} else {
				std::cout << "The only correct argument syntax is --target="
						  << std::endl;
				return 0;
			}
		} else {
			std::cout << "The only acceptable argument is --target="
					  << std::endl;
			return 0;
		}
	} else {
		target_str = "localhost:50051";
	}
	KitNetClient greeter(
		grpc::CreateChannel(target_str, grpc::InsecureChannelCredentials()));
	std::string user("world");
	std::string reply = greeter.SayHello(user);
	std::cout << "KitNet received: " << reply << std::endl;

	return 0;
}
