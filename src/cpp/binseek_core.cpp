#include "binseek.h"
#include "mmap_file.h"
#include "editor.h"
#include "search.h"

#include <algorithm>
#include <cstdint>
#include <cstddef>
#include <cstring>
#include <string>
#include <vector>

struct BsCore {
    MmapFile file;
    Editor editor;
    std::string error;

    explicit BsCore(MmapFile&& f)
        : file(std::move(f)), editor(&file)
    {
    }
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
    MmapFile file;
    if (!file.open(path)) {
        g_last_error = file.error();
        return nullptr;
    }
    return new BsCore(std::move(file));
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
    *size = core->editor.size();
    return 0;
}

int bs_read_chunk(bs_handle_t handle, uint64_t offset, uint64_t len, uint8_t* out) {
    if (!handle || !out) return -1;
    auto* core = as_core(handle);
    if (!core->file.is_open()) {
        core->error = "file not open";
        return -1;
    }
    const uint64_t sz = core->editor.size();
    if (offset > sz || len > sz - offset) {
        core->error = "read out of bounds";
        return -1;
    }
    if (len == 0) {
        return 0;
    }
    core->editor.read(offset, len, out);
    return 0;
}

int bs_search(
    bs_handle_t handle,
    const uint8_t* pattern,
    uint64_t pattern_len,
    uint64_t start_offset,
    uint64_t max_results,
    uint64_t* results,
    uint64_t* result_count)
{
    if (!handle || !pattern || !results || !result_count) return -1;
    auto* core = as_core(handle);
    if (!core->file.is_open()) {
        core->error = "file not open";
        return -1;
    }
    if (pattern_len == 0 || max_results == 0) {
        *result_count = 0;
        return 0;
    }

    auto hits = search_all(
        core->file.data(),
        core->file.size(),
        pattern,
        pattern_len,
        start_offset,
        max_results);

    *result_count = hits.size();
    for (size_t i = 0; i < hits.size(); ++i) {
        results[i] = hits[i];
    }
    return 0;
}

int bs_replace(
    bs_handle_t handle,
    uint64_t offset,
    uint64_t old_len,
    const uint8_t* new_data,
    uint64_t new_len)
{
    if (!handle) return -1;
    auto* core = as_core(handle);
    if (!core->file.is_open()) {
        core->error = "file not open";
        return -1;
    }
    const uint64_t sz = core->editor.size();
    if (offset > sz || old_len > sz - offset) {
        core->error = "replace out of bounds";
        return -1;
    }
    core->editor.replace(offset, old_len, new_data, new_len);
    return 0;
}

int bs_save(bs_handle_t handle, const char* out_path) {
    if (!handle || !out_path) return -1;
    auto* core = as_core(handle);
    if (!core->file.is_open()) {
        core->error = "file not open";
        return -1;
    }
    std::string error;
    if (!core->editor.save(out_path, error)) {
        core->error = error;
        return -1;
    }
    return 0;
}
