#pragma once

#include <memory>
#include <string>

#include "../sample.h"

namespace peregrine {
struct KitNetClient {
	int sockfd;
	struct sockaddr_in servaddr;

	KitNetClient();
	float ProcessSample(const sample_t& sample);
};
}  // namespace peregrine