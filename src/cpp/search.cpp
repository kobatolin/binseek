#include "search.h"

#include <algorithm>
#include <cctype>
#include <cstring>
#include <vector>

namespace {

inline uint8_t ascii_tolower(uint8_t c) {
    return (c >= 'A' && c <= 'Z') ? static_cast<uint8_t>(c - 'A' + 'a') : c;
}

// Boyer-Moore-Horspool skip table.
class BmHorspool {
public:
    BmHorspool(const uint8_t* pat, uint64_t len, bool case_insensitive)
        : pattern_(pat), len_(len), case_insensitive_(case_insensitive)
    {
        std::fill(std::begin(skip_), std::end(skip_), static_cast<int>(len_));
        if (case_insensitive_) {
            lowered_.reserve(len_);
            for (uint64_t i = 0; i < len_; ++i) {
                lowered_.push_back(ascii_tolower(pat[i]));
            }
            pattern_ = lowered_.data();
            for (uint64_t i = 0; i + 1 < len_; ++i) {
                uint8_t lo = ascii_tolower(pat[i]);
                int dist = static_cast<int>(len_ - 1 - i);
                skip_[lo] = dist;
                if (lo >= 'a' && lo <= 'z') {
                    skip_[lo - ('a' - 'A')] = dist;
                } else if (lo >= 'A' && lo <= 'Z') {
                    skip_[lo + ('a' - 'A')] = dist;
                }
            }
        } else {
            for (uint64_t i = 0; i + 1 < len_; ++i) {
                skip_[pattern_[i]] = static_cast<int>(len_ - 1 - i);
            }
        }
    }

    std::vector<bs_match_t> search(const uint8_t* data, uint64_t size, uint64_t start, uint64_t max_results) const {
        std::vector<bs_match_t> results;
        if (len_ == 0 || size < len_ || start >= size) {
            return results;
        }
        uint64_t limit = size - len_;
        uint64_t i = start;
        while (i <= limit && results.size() < max_results) {
            int j = static_cast<int>(len_) - 1;
            if (case_insensitive_) {
                while (j >= 0 && ascii_tolower(data[i + j]) == pattern_[j]) {
                    --j;
                }
            } else {
                while (j >= 0 && data[i + j] == pattern_[j]) {
                    --j;
                }
            }
            if (j < 0) {
                results.push_back({i, len_});
                if (results.size() >= max_results) break;
                // Advance by 1 to allow overlapping matches.
                ++i;
            } else {
                uint8_t bad = case_insensitive_ ? ascii_tolower(data[i + len_ - 1]) : data[i + len_ - 1];
                i += static_cast<uint64_t>(skip_[bad]);
                if (i <= start) {
                    // Prevent infinite loop for bad skip values.
                    i = start + 1;
                }
                start = i;
            }
        }
        return results;
    }

private:
    const uint8_t* pattern_;
    uint64_t len_;
    bool case_insensitive_;
    int skip_[256];
    std::vector<uint8_t> lowered_;
};

} // namespace

std::vector<bs_match_t> search_all(
    const uint8_t* data,
    uint64_t size,
    const uint8_t* pattern,
    uint64_t pattern_len,
    uint64_t start_offset,
    uint64_t max_results,
    bool case_insensitive)
{
    BmHorspool engine(pattern, pattern_len, case_insensitive);
    return engine.search(data, size, start_offset, max_results);
}
