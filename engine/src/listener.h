#pragma once

#include <string>

#include "packet.h"
#include "sample.h"

namespace peregrine {
class Listener {
private:
	int sock_recv;
	uint8_t* buffer;

public:
	Listener(const std::string& iface);

	sample_t receive_sample();
	~Listener();
};
}  // namespace peregrine