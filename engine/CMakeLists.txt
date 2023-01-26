cmake_minimum_required(VERSION 3.15)
project(peregrine-engine)

include(FetchContent)

FetchContent_Declare(
	gRPC
	GIT_REPOSITORY https://github.com/grpc/grpc
	GIT_TAG        v1.50.0
)

FetchContent_MakeAvailable(gRPC)

set(_PROTOBUF_LIBPROTOBUF libprotobuf)
set(_REFLECTION grpc++_reflection)
set(_GRPC_GRPCPP grpc++)

# I'm not proud of this
set(PROTOC_EXECUTABLE "${CMAKE_CURRENT_BINARY_DIR}/_deps/grpc-build/third_party/protobuf/protoc")
set(GRPC_CPP_PLUGIN "${CMAKE_CURRENT_BINARY_DIR}/_deps/grpc-build/grpc_cpp_plugin")
set(GRPC_PYTHON_PLUGIN "${CMAKE_CURRENT_BINARY_DIR}/_deps/grpc-build/grpc_python_plugin")

# Proto file
set(PROTO_DIR ${CMAKE_CURRENT_SOURCE_DIR}/protos)

get_filename_component(hw_proto "${PROTO_DIR}/kitnet.proto" ABSOLUTE)
get_filename_component(hw_proto_path "${hw_proto}" PATH)

# Generated sources
set(cpp_grpc_srcs "${CMAKE_CURRENT_BINARY_DIR}/kitnet.grpc.pb.cc")
set(cpp_proto_srcs "${CMAKE_CURRENT_BINARY_DIR}/kitnet.pb.cc")

set(cpp_grpc_hdrs "${CMAKE_CURRENT_BINARY_DIR}/kitnet.grpc.pb.h")
set(cpp_proto_hdrs "${CMAKE_CURRENT_BINARY_DIR}/kitnet.pb.h")

set(python_grpc_srcs "${CMAKE_CURRENT_BINARY_DIR}/kitnet.grpc.pb.python")
set(python_proto_srcs "${CMAKE_CURRENT_BINARY_DIR}/kitnet.pb.python")

add_custom_command(
	OUTPUT
		"${cpp_grpc_srcs}"
		"${cpp_proto_srcs}"
		"${cpp_proto_hdrs}"
		"${cpp_grpc_hdrs}"
		"${python_grpc_srcs}"
		"${python_proto_srcs}"
	COMMAND ${PROTOC_EXECUTABLE}
	ARGS --grpc_out "${CMAKE_CURRENT_BINARY_DIR}"
		--cpp_out "${CMAKE_CURRENT_BINARY_DIR}"
		--python_out "${CMAKE_CURRENT_BINARY_DIR}"
		-I "${hw_proto_path}"
		--plugin=protoc-gen-grpc="${GRPC_CPP_PLUGIN}"
		--plugin=protoc-gen-python="${GRPC_PYTHON_PLUGIN}"
		"${hw_proto}"
	DEPENDS "${hw_proto}"
)


# Include generated *.pb.h files
include_directories("${CMAKE_CURRENT_BINARY_DIR}")

# hw_grpc_proto
add_library(hw_grpc_proto
	${cpp_grpc_srcs}
	${cpp_grpc_hdrs}
	${cpp_proto_srcs}
	${cpp_proto_hdrs}
)

target_link_libraries(hw_grpc_proto
	${_REFLECTION}
	${_GRPC_GRPCPP}
	${_PROTOBUF_LIBPROTOBUF}
)

add_executable(engine
	${CMAKE_CURRENT_SOURCE_DIR}/src/engine/engine.cpp
	${CMAKE_CURRENT_SOURCE_DIR}/src/engine/kitnet_client.cpp
	${CMAKE_CURRENT_SOURCE_DIR}/src/engine/listener.cpp
	${PROTO_SRCS}
	${GRPC_SRCS}
)

target_link_libraries(engine
	hw_grpc_proto
    ${_REFLECTION}
    ${_GRPC_GRPCPP}
    ${_PROTOBUF_LIBPROTOBUF}
)
