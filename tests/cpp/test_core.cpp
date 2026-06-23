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
    assert(bs_search(h, pattern, 2, 0, 8, 0, results, &count) == 0);
    assert(count == 1);
    assert(results[0].offset == 2);
    assert(results[0].length == 2);

    // Case-insensitive ASCII search.
    uint8_t ci_pattern[] = {0x57, 0x4F, 0x52, 0x4C, 0x44}; // "WORLD"
    bs_match_t ci_results[8] = {};
    uint64_t ci_count = 0;
    assert(bs_search(h, ci_pattern, 5, 0, 8, 1, ci_results, &ci_count) == 0);
    assert(ci_count == 1);
    assert(ci_results[0].offset == 6);
    assert(ci_results[0].length == 5);

    // ASCII regex search.
    bs_match_t re_results[8] = {};
    uint64_t re_count = 0;
    assert(bs_search_regex(h, "H.llo", 0, 8, 0, re_results, &re_count) == 0);
    assert(re_count == 1);
    assert(re_results[0].offset == 0);
    assert(re_results[0].length == 5);

    // Case-insensitive ASCII regex.
    re_count = 0;
    assert(bs_search_regex(h, "wOrLd", 0, 8, BS_SEARCH_REGEX_ICASE, re_results, &re_count) == 0);
    assert(re_count == 1);
    assert(re_results[0].offset == 6);
    assert(re_results[0].length == 5);

    // HEX regex: exact byte.
    bs_match_t hex_results[8] = {};
    uint64_t hex_count = 0;
    assert(bs_search_regex(h, "6C", 0, 8, BS_SEARCH_REGEX_HEX, hex_results, &hex_count) == 0);
    assert(hex_count == 3);
    assert(hex_results[0].offset == 2);
    assert(hex_results[0].length == 1);

    // HEX regex: nibble wildcard.
    hex_count = 0;
    assert(bs_search_regex(h, "6.", 0, 8, BS_SEARCH_REGEX_HEX, hex_results, &hex_count) == 0);
    assert(hex_count == 7);

    // HEX regex: '?' whole-byte wildcard.
    hex_count = 0;
    assert(bs_search_regex(h, "48 ? 6C 6C", 0, 8, BS_SEARCH_REGEX_HEX, hex_results, &hex_count) == 0);
    assert(hex_count == 1);
    assert(hex_results[0].offset == 0);
    assert(hex_results[0].length == 4);

    // HEX regex: character class for address range.
    // Data: 0x00 0x0A at the end; pattern "0[0-A]?" won't match, use a simple class test.
    hex_count = 0;
    assert(bs_search_regex(h, "[0-7][0-F]", 0, 8, BS_SEARCH_REGEX_HEX, hex_results, &hex_count) == 0);
    assert(hex_count >= 1);

    // Invalid HEX regex returns error.
    int rc = bs_search_regex(h, "[", 0, 8, BS_SEARCH_REGEX_HEX, hex_results, &hex_count);
    assert(rc == -1);

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
