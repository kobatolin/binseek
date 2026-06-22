// Simple C++ self-test for the binseek C API.

#include "binseek.h"

#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>

static const char* INPUT_PATH = "build/test_input.bin";
static const char* OUTPUT_PATH = "build/test_output.bin";

static void write_file(const char* path, const std::vector<uint8_t>& data) {
    std::ofstream f(path, std::ios::binary);
    f.write(reinterpret_cast<const char*>(data.data()), data.size());
}

static std::vector<uint8_t> read_file(const char* path) {
    std::ifstream f(path, std::ios::binary | std::ios::ate);
    auto size = f.tellg();
    f.seekg(0, std::ios::beg);
    std::vector<uint8_t> data(static_cast<size_t>(size));
    f.read(reinterpret_cast<char*>(data.data()), size);
    return data;
}

int main() {
    std::vector<uint8_t> data = {
        0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x20, 0x77, 0x6F,
        0x72, 0x6C, 0x64, 0x21, 0x00, 0x0A
    };
    write_file(INPUT_PATH, data);

    bs_handle_t h = bs_open(INPUT_PATH);
    assert(h != nullptr);

    uint64_t size = 0;
    assert(bs_get_size(h, &size) == 0);
    assert(size == data.size());

    std::vector<uint8_t> chunk(data.size());
    assert(bs_read_chunk(h, 0, data.size(), chunk.data()) == 0);
    assert(chunk == data);

    uint8_t pattern[] = {0x6C, 0x6C}; // "ll"
    bs_match_t results[8] = {};
    uint64_t count = 0;
    assert(bs_search(h, pattern, 2, 0, 8, results, &count) == 0);
    assert(count == 1);
    assert(results[0].offset == 2);
    assert(results[0].length == 2);

    // Replace first "Hello" with "Hallo" (same length).
    uint8_t replacement[] = {0x48, 0x61, 0x6C, 0x6C, 0x6F};
    assert(bs_replace(h, 0, 5, replacement, 5) == 0);

    // Regression: replacing a range that aligns with an internal segment boundary.
    uint8_t replacement2[] = {0xAA, 0xBB, 0xCC, 0xDD};
    assert(bs_replace(h, 0, 4, replacement2, 4) == 0);
    std::vector<uint8_t> chunk2(4);
    assert(bs_read_chunk(h, 0, 4, chunk2.data()) == 0);
    assert(chunk2[0] == 0xAA);
    assert(chunk2[1] == 0xBB);
    assert(chunk2[2] == 0xCC);
    assert(chunk2[3] == 0xDD);

    assert(bs_save(h, OUTPUT_PATH) == 0);
    bs_close(h);

    auto out = read_file(OUTPUT_PATH);
    assert(out.size() == data.size());
    assert(out[0] == 0xAA);
    assert(out[1] == 0xBB);
    assert(out[2] == 0xCC);
    assert(out[3] == 0xDD);
    assert(out[4] == 0x6F);

    std::remove(INPUT_PATH);
    std::remove(OUTPUT_PATH);

    std::puts("C++ tests passed");
    return 0;
}
