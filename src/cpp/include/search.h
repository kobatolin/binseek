#ifndef SEARCH_H
#define SEARCH_H

#include "binseek.h"

#include <cstdint>
#include <cstddef>
#include <vector>

// Search [data, data + size) for pattern starting at or after start_offset.
// Returns at most max_results match ranges in ascending order.
std::vector<bs_match_t> search_all(
    const uint8_t* data,
    uint64_t size,
    const uint8_t* pattern,
    uint64_t pattern_len,
    uint64_t start_offset,
    uint64_t max_results);

#endif
