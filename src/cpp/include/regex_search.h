#ifndef REGEX_SEARCH_H
#define REGEX_SEARCH_H

#include "binseek.h"

#include <cstdint>
#include <string>
#include <vector>

// Search [data, data + size) for a lightweight regex pattern starting at or
// after start_offset. Returns at most max_results match ranges in ascending
// order.
//
// hex_mode:
//   true  -> pattern is a hex regex (see below).
//   false -> pattern is an ASCII regex interpreted by boost::regex.
//
// case_insensitive is only meaningful for ASCII regex.
//
// Hex regex syntax (one byte per token, spaces ignored):
//   "12"         exact byte 0x12
//   "1." / ".2" high/low nibble wildcard
//   ".." / "?"  any byte
//   "[0-7]"      nibble character class/range (one nibble position)
// Examples:
//   ".[048C] ? [0-3]. 08" matches 4-byte aligned addresses in the range
//   0x08000000 ~ 0x083FFFFC.
std::vector<bs_match_t> search_regex_all(
    const uint8_t* data,
    uint64_t size,
    const std::string& pattern,
    uint64_t start_offset,
    uint64_t max_results,
    bool hex_mode = false,
    bool case_insensitive = false,
    std::string* error = nullptr);

#endif
