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

GRPC_AUTOGEN   = $(foreach obj,$(patsubst %.proto, %.pb.cc, $(GRPC_SERVICES)),$(AUTO_GEN)/$(shell basename -- $(obj)))
GRPC_AUTOGEN  += $(foreach obj,$(patsubst %.proto, %.grpc.pb.cc, $(GRPC_SERVICES)),$(AUTO_GEN)/$(shell basename -- $(obj)))
GRPC_AUTOGEN  += $(foreach obj,$(patsubst %.proto, %.pb.python, $(GRPC_SERVICES)),$(AUTO_GEN)/$(shell basename -- $(obj)))
GRPC_AUTOGEN  += $(foreach obj,$(patsubst %.proto, %.grpc.pb.python, $(GRPC_SERVICES)),$(AUTO_GEN)/$(shell basename -- $(obj)))

GRPC_OBJS      = $(foreach obj,$(patsubst %.proto, %.pb.o, $(GRPC_SERVICES)),$(OUT_DIR)/$(shell basename -- $(obj)))
GRPC_OBJS     += $(foreach obj,$(patsubst %.proto, %.grpc.pb.o, $(GRPC_SERVICES)),$(OUT_DIR)/$(shell basename -- $(obj)))

ENGINE_OBJS   += $(GRPC_OBJS)

CC       = g++
CFLAGS   = -std=c++14
CFLAGS  += -g -O0 -DDEBUG
# CFLAGS  += -O3

LDFLAGS  = -L/usr/local/include                               \
			-lgrpc++ -lgrpc -lgpr -lz -lprotobuf -pthread -lz \
			-lgrpc++_reflection                               \
			-pthread -lpcap -ldl

PROTOC                  = protoc
GRPC_CPP_PLUGIN         = grpc_cpp_plugin
GRPC_PYTHON_PLUGIN      = grpc_python_plugin
GRPC_CPP_PLUGIN_PATH    = `which $(GRPC_CPP_PLUGIN)`
GRPC_PYTHON_PLUGIN_PATH = `which $(GRPC_PYTHON_PLUGIN)`

vpath %.proto $(PROTOS_DIR)

all: build-dirs $(ENGINE_EXE)

build-dirs:
	@ mkdir -p $(OUT_DIR)
	@ mkdir -p $(AUTO_GEN)

###########################
#         Engine          #
###########################

$(ENGINE_EXE): $(GRPC_AUTOGEN) $(ENGINE_OBJS)
	$(CC) $(CFLAGS) -o $@ $(ENGINE_OBJS) $(LDFLAGS)

$(OUT_DIR)/%.o: $(ENGINE_DIR)/%.cpp $(ENGINE_HEADERS)
	$(CC) $(CFLAGS) -c $< -o $@ $(LDFLAGS)

#######################################
#   Compiling gRPC autogen sources    #
#######################################

$(OUT_DIR)/%.grpc.pb.o: $(AUTO_GEN)/%.grpc.pb.cc $(HEADERS)
	$(CC) $(CFLAGS) -c $< -o $@ $(LDFLAGS)

$(OUT_DIR)/%.pb.o: $(AUTO_GEN)/%.pb.cc $(HEADERS)
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

.PRECIOUS: %.grpc.pb.python
$(AUTO_GEN)/%.grpc.pb.python: %.proto
	$(PROTOC) -I $(PROTOS_DIR) --grpc_out=$(AUTO_GEN) --plugin=protoc-gen-grpc=$(GRPC_PYTHON_PLUGIN_PATH) $<

.PRECIOUS: %.pb.python
$(AUTO_GEN)/%.pb.python: %.proto
	$(PROTOC) -I $(PROTOS_DIR) --python_out=$(AUTO_GEN) $<

clean:
	rm -rf $(ENGINE_EXE) $(OUT_DIR) $(AUTO_GEN)
