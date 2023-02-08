#include <iostream>

#include "kitnet_client.h"
#include "constants.h"

#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <linux/ip.h>
#include <linux/udp.h>

namespace peregrine {

KitNetClient::KitNetClient() {
	sockfd = socket(AF_INET, SOCK_DGRAM, 0);

	// Creating socket file descriptor
	if (sockfd < 0) {
		perror("socket creation failed");
		exit(EXIT_FAILURE);
	}

	memset(&servaddr, 0, sizeof(servaddr));
	servaddr.sin_family = AF_INET;
	servaddr.sin_port = htons(PLUGIN_PORT);
	servaddr.sin_addr.s_addr = inet_addr(PLUGIN_HOST);
}

float KitNetClient::ProcessSample(const sample_t& sample) {
	auto buffer = sample.serialize();

	auto sent_len =
		sendto(sockfd, (const char*)buffer.data(), buffer.size(), MSG_CONFIRM,
			   (const struct sockaddr*)&servaddr, sizeof(servaddr));

	if (sent_len != buffer.size()) {
		fprintf(stderr, "Truncated packet.\n");
		exit(EXIT_FAILURE);
	}

	struct sockaddr_in src_addr;
	socklen_t socklen = sizeof(src_addr);
	float rmse;
	ssize_t len = recvfrom(sockfd, &rmse, sizeof(rmse), 0,
						   (struct sockaddr*)&src_addr, &socklen);

	if (len > 0) {
#ifndef NDEBUG
		std::cout << "rmse " << rmse << "\n";
#endif
		return rmse;
	} else {
		std::cerr << "Failed to receive response from KitNet." << std::endl;
		return -1;
	}
}

}  // namespace peregrine