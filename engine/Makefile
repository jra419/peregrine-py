CUR_DIR    = $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
SRC_DIR    = $(CUR_DIR)/src
PROTOS_DIR = $(CUR_DIR)/protos
OUT_DIR    = $(CUR_DIR)/build
AUTO_GEN   = $(CUR_DIR)/autogen
ENGINE_DIR = $(SRC_DIR)/engine
MODELS_DIR = $(SRC_DIR)/models

ENGINE_HDRS = $(shell find $(ENGINE_DIR) -name "*.h")
ENGINE_SRCS = $(shell find $(ENGINE_DIR) -name "*.cpp")
ENGINE_OBJS = $(foreach obj,$(patsubst %.cpp, %.o, $(ENGINE_SRCS)),$(OUT_DIR)/$(shell basename -- $(obj)))
ENGINE_EXE  = $(OUT_DIR)/engine

GRPC_SERVICES  = $(shell find $(PROTOS_DIR) -name "*.proto")
GRPC_OBJS      = $(foreach obj,$(patsubst %.proto, %.pb.o, $(GRPC_SERVICES)),$(OUT_DIR)/$(shell basename -- $(obj)))
GRPC_OBJS     += $(foreach obj,$(patsubst %.proto, %.grpc.pb.o, $(GRPC_SERVICES)),$(OUT_DIR)/$(shell basename -- $(obj)))

KITNET_DIR     = $(MODELS_DIR)/kitnet
KITNET_HEADERS = $(shell find $(KITNET_DIR) -name "*.h")
KITNET_SRCS    = $(shell find $(KITNET_DIR) -name "*.cpp")
KITNET_OBJS    = $(foreach obj,$(patsubst %.cpp, %.o, $(KITNET_SRCS)),$(OUT_DIR)/$(shell basename -- $(obj)))
KITNET_EXE     = $(OUT_DIR)/kitnet

CC       = g++
CFLAGS   = -std=c++14
CFLAGS  += -g -O0 -DDEBUG
# CFLAGS  += -O3

LDFLAGS  = -L/usr/local/include                               \
			-lgrpc++ -lgrpc -lgpr -lz -lprotobuf -pthread -lz \
			-lgrpc++_reflection                               \
			-pthread -lpcap -ldl

PROTOC               = protoc
GRPC_CPP_PLUGIN      = grpc_cpp_plugin
GRPC_CPP_PLUGIN_PATH = `which $(GRPC_CPP_PLUGIN)`

vpath %.proto $(PROTOS_DIR)

all: build-dirs $(ENGINE_EXE) $(KITNET_EXE)

build-dirs:
	@ mkdir -p $(OUT_DIR)
	@ mkdir -p $(AUTO_GEN)

###########################
#         Engine          #
###########################

$(ENGINE_EXE): $(GRPC_OBJS) $(ENGINE_OBJS)
	$(CC) $(CFLAGS) -o $@ $(ENGINE_OBJS) $(GRPC_OBJS) $(LDFLAGS)

$(OUT_DIR)/%.o: $(ENGINE_DIR)/%.cpp $(ENGINE_HEADERS)
	$(CC) $(CFLAGS) -c $< -o $@ $(LDFLAGS)

###########################
#      KitNet model       #
###########################

GRPC_OBJS_KITNET = $(OUT_DIR)/kitnet.grpc.pb.o $(OUT_DIR)/kitnet.pb.o

$(KITNET_EXE): $(KITNET_OBJS) $(GRPC_OBJS_KITNET)
	$(CC) $(CFLAGS) -o $@ $(KITNET_OBJS) $(GRPC_OBJS_KITNET) $(LDFLAGS)

$(OUT_DIR)/%.o: $(KITNET_DIR)/%.cpp $(KITNET_HEADERS)
	$(CC) $(CFLAGS) -c $< -o $@ $(LDFLAGS)

$(OUT_DIR)/kitnet.grpc.pb.o: $(AUTO_GEN)/kitnet.grpc.pb.cc $(HEADERS)
	$(CC) $(CFLAGS) -c $< -o $@ $(LDFLAGS)

$(OUT_DIR)/kitnet.pb.o: $(AUTO_GEN)/kitnet.pb.cc $(HEADERS)
	$(CC) $(CFLAGS) -c $< -o $@ $(LDFLAGS)

###########################
#     Protobuf & gRPC     #
###########################

.PRECIOUS: %.grpc.pb.cc
$(AUTO_GEN)/%.grpc.pb.cc: %.proto
	$(PROTOC) -I $(PROTOS_DIR) --grpc_out=$(AUTO_GEN) --plugin=protoc-gen-grpc=$(GRPC_CPP_PLUGIN_PATH) $<

.PRECIOUS: %.pb.cc
$(AUTO_GEN)/%.pb.cc: %.proto
	$(PROTOC) -I $(PROTOS_DIR) --cpp_out=$(AUTO_GEN) $<

clean:
	rm -rf $(ENGINE_EXE) $(OUT_DIR) $(AUTO_GEN)
