# binseek Makefile
# Build the C++ core shared library for Linux (.so) and Windows (.dll).
# Default build environment is WSL with g++ and mingw-w64 installed.

CXX_LINUX  ?= g++
CXX_WIN    ?= x86_64-w64-mingw32-g++
PYTHON     ?= python3

CXXFLAGS      ?= -O3 -std=c++17 -Wall -Wextra -I src/cpp/include
CXXFLAGS_WIN  ?= -O3 -std=c++17 -Wall -Wextra -I src/cpp/include -I third_party/boost-mingw/include

LDFLAGS_LINUX ?= -shared -fPIC -static-libstdc++ -lboost_regex
LDFLAGS_WIN   ?= -shared -static-libgcc -static-libstdc++ -Lthird_party/boost-mingw/lib -lboost_regex

SRC_DIR   = src/cpp
BUILD_DIR = build
OUT_DIR   = binseek

SRCS = \
	$(SRC_DIR)/binseek_core.cpp \
	$(SRC_DIR)/mmap_file.cpp \
	$(SRC_DIR)/search.cpp \
	$(SRC_DIR)/editor.cpp \
	$(SRC_DIR)/regex_search.cpp

OBJS_LINUX = $(patsubst $(SRC_DIR)/%.cpp,$(BUILD_DIR)/linux/%.o,$(SRCS))
OBJS_WIN   = $(patsubst $(SRC_DIR)/%.cpp,$(BUILD_DIR)/win/%.o,$(SRCS))

TEST_SRCS = tests/cpp/test_core.cpp
TEST_BIN  = build/test_core

.PHONY: all linux windows test test-cpp clean

all: linux windows

linux: $(OUT_DIR)/libcore.so

windows: $(OUT_DIR)/libcore.dll

# Linux object files
$(BUILD_DIR)/linux/%.o: $(SRC_DIR)/%.cpp
	@mkdir -p $(dir $@)
	$(CXX_LINUX) $(CXXFLAGS) -fPIC -c $< -o $@

# Windows object files (cross compiled with mingw-w64)
$(BUILD_DIR)/win/%.o: $(SRC_DIR)/%.cpp
	@mkdir -p $(dir $@)
	$(CXX_WIN) $(CXXFLAGS_WIN) -c $< -o $@

$(OUT_DIR)/libcore.so: $(OBJS_LINUX)
	@mkdir -p $(OUT_DIR)
	$(CXX_LINUX) $(LDFLAGS_LINUX) $^ -o $@

$(OUT_DIR)/libcore.dll: $(OBJS_WIN)
	@mkdir -p $(OUT_DIR)
	$(CXX_WIN) $(LDFLAGS_WIN) $^ -o $@
	cp third_party/boost-mingw/lib/libboost_regex.dll $(OUT_DIR)/libboost_regex.dll

# C++ self-test
$(TEST_BIN): $(TEST_SRCS) $(SRCS)
	@mkdir -p $(dir $@)
	$(CXX_LINUX) $(CXXFLAGS) $(TEST_SRCS) $(SRCS) -o $@ -lboost_regex

test-cpp: $(TEST_BIN)
	$(TEST_BIN)

# Python tests
pytest:
	$(PYTHON) -m pytest tests -q

test: test-cpp pytest


clean:
	rm -rf $(BUILD_DIR) $(OUT_DIR)/libcore.so $(OUT_DIR)/libcore.dll $(OUT_DIR)/libboost_regex.dll
