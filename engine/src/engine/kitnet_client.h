#pragma once

#include <memory>
#include <string>

#include <grpcpp/grpcpp.h>
#include "../../autogen/kitnet.grpc.pb.h"

#include "sample.h"

namespace peregrine {
class KitNetClient {
public:
	KitNetClient(std::shared_ptr<grpc::Channel> channel)
		: stub_(KitNet::NewStub(channel)) {}

	float ProcessSample(const sample_t& sample);

private:
	std::unique_ptr<KitNet::Stub> stub_;
};
}  // namespace peregrine