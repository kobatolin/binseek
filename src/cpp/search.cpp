#include "search.h"

#include <algorithm>
#include <cstring>
#include <vector>

namespace {

// Boyer-Moore-Horspool skip table.
class BmHorspool {
public:
    BmHorspool(const uint8_t* pat, uint64_t len)
        : pattern_(pat), len_(len)
    {
        std::fill(std::begin(skip_), std::end(skip_), static_cast<int>(len_));
        for (uint64_t i = 0; i + 1 < len_; ++i) {
            skip_[pattern_[i]] = static_cast<int>(len_ - 1 - i);
        }
    }

    std::vector<uint64_t> search(const uint8_t* data, uint64_t size, uint64_t start, uint64_t max_results) const {
        std::vector<uint64_t> results;
        if (len_ == 0 || size < len_ || start >= size) {
            return results;
        }
        uint64_t limit = size - len_;
        uint64_t i = start;
        while (i <= limit && results.size() < max_results) {
            int j = static_cast<int>(len_) - 1;
            while (j >= 0 && data[i + j] == pattern_[j]) {
                --j;
            }
            if (j < 0) {
                results.push_back(i);
                if (results.size() >= max_results) break;
                // Advance by 1 to allow overlapping matches.
                ++i;
            } else {
                i += static_cast<uint64_t>(skip_[data[i + len_ - 1]]);
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
    int skip_[256];
};

} // namespace

std::vector<uint64_t> search_all(
    const uint8_t* data,
    uint64_t size,
    const uint8_t* pattern,
    uint64_t pattern_len,
    uint64_t start_offset,
    uint64_t max_results)
{
    BmHorspool engine(pattern, pattern_len);
    return engine.search(data, size, start_offset, max_results);
}
