#include "binseek.h"
#include "mmap_file.h"

#include <cstdint>
#include <cstddef>
#include <cstring>
#include <string>

struct BsCore {
    MmapFile file;
    std::string error;
};

namespace {
    thread_local std::string g_last_error;

    BsCore* as_core(bs_handle_t h) {
        return static_cast<BsCore*>(h);
    }
}

bs_handle_t bs_open(const char* path) {
    if (!path) {
        g_last_error = "null path";
        return nullptr;
    }
    auto* core = new BsCore();
    if (!core->file.open(path)) {
        g_last_error = core->file.error();
        delete core;
        return nullptr;
    }
    return core;
}

void bs_close(bs_handle_t handle) {
    if (handle) {
        delete as_core(handle);
    }
}

const char* bs_get_error(bs_handle_t handle) {
    if (!handle) {
        return g_last_error.c_str();
    }
    auto* core = as_core(handle);
    if (!core->error.empty()) {
        return core->error.c_str();
    }
    if (!core->file.error().empty()) {
        return core->file.error().c_str();
    }
    return "";
}

int bs_get_size(bs_handle_t handle, uint64_t* size) {
    if (!handle || !size) return -1;
    auto* core = as_core(handle);
    if (!core->file.is_open()) {
        core->error = "file not open";
        return -1;
    }
    *size = core->file.size();
    return 0;
}

int bs_read_chunk(bs_handle_t handle, uint64_t offset, uint64_t len, uint8_t* out) {
    if (!handle || !out) return -1;
    auto* core = as_core(handle);
    if (!core->file.is_open()) {
        core->error = "file not open";
        return -1;
    }
    const uint64_t sz = core->file.size();
    if (offset > sz || len > sz - offset) {
        core->error = "read out of bounds";
        return -1;
    }
    if (len == 0) {
        return 0;
    }
    std::memcpy(out, core->file.data() + offset, static_cast<size_t>(len));
    return 0;
}
