cmake_minimum_required(VERSION 3.15)
project(peregrine-dispatcher)

if(NOT CMAKE_BUILD_TYPE)
	set(CMAKE_BUILD_TYPE Release)
endif()

add_executable(dispatcher
	${CMAKE_CURRENT_SOURCE_DIR}/src/dispatcher.cpp
	${CMAKE_CURRENT_SOURCE_DIR}/src/listener.cpp
	${CMAKE_CURRENT_SOURCE_DIR}/src/packet.cpp
	${CMAKE_CURRENT_SOURCE_DIR}/src/plugins/kitnet_client.cpp
)

target_link_libraries(dispatcher)
