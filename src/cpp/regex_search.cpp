#include "regex_search.h"

#include <algorithm>
#include <cctype>
#include <sstream>
#include <stdexcept>
#include <string>

#include <boost/regex.hpp>

namespace {

struct NibbleMask {
    // Bit i set means nibble value i (0-15) is allowed.
    uint16_t bits = 0;

    bool matches(uint8_t value) const {
        return (bits & (static_cast<uint16_t>(1) << value)) != 0;
    }
};

struct ByteMask {
    NibbleMask high;
    NibbleMask low;

    bool matches(uint8_t byte) const {
        uint8_t h = byte >> 4;
        uint8_t l = byte & 0x0F;
        return high.matches(h) && low.matches(l);
    }
};

class HexRegexParser {
public:
    explicit HexRegexParser(const std::string& s) : s_(s), pos_(0) {
        // Remove whitespace up front so indexing is simple.
        cleaned_.reserve(s_.size());
        for (char c : s_) {
            if (!std::isspace(static_cast<unsigned char>(c))) {
                cleaned_.push_back(c);
            }
        }
    }

    std::vector<ByteMask> parse() {
        std::vector<ByteMask> result;
        while (pos_ < cleaned_.size()) {
            if (cleaned_[pos_] == '?') {
                result.push_back(anyByte());
                ++pos_;
                continue;
            }
            ByteMask bm;
            bm.high = parseNibble();
            bm.low = parseNibble();
            result.push_back(bm);
        }
        return result;
    }

private:
    static ByteMask anyByte() {
        ByteMask bm;
        bm.high.bits = 0xFFFF;
        bm.low.bits = 0xFFFF;
        return bm;
    }

    static int hexValue(char c) {
        if (c >= '0' && c <= '9') return c - '0';
        if (c >= 'A' && c <= 'F') return c - 'A' + 10;
        if (c >= 'a' && c <= 'f') return c - 'a' + 10;
        return -1;
    }

    static bool isHex(char c) {
        return hexValue(c) != -1;
    }

    NibbleMask parseNibble() {
        if (pos_ >= cleaned_.size()) {
            throw std::invalid_argument("incomplete hex byte");
        }
        char c = cleaned_[pos_];
        if (c == '.') {
            ++pos_;
            NibbleMask mask;
            mask.bits = 0xFFFF;
            return mask;
        }
        if (c == '[') {
            return parseClass();
        }
        if (isHex(c)) {
            ++pos_;
            NibbleMask mask;
            mask.bits = static_cast<uint16_t>(1) << hexValue(c);
            return mask;
        }
        std::ostringstream oss;
        oss << "unexpected character '" << c << "' in hex regex";
        throw std::invalid_argument(oss.str());
    }

    NibbleMask parseClass() {
        // Skip '['.
        ++pos_;
        NibbleMask mask;
        mask.bits = 0;
        if (pos_ >= cleaned_.size()) {
            throw std::invalid_argument("unclosed hex character class");
        }
        while (pos_ < cleaned_.size() && cleaned_[pos_] != ']') {
            char a = cleaned_[pos_];
            if (!isHex(a)) {
                std::ostringstream oss;
                oss << "invalid hex digit '" << a << "' in character class";
                throw std::invalid_argument(oss.str());
            }
            // Look for a range like "0-7".
            if (pos_ + 2 < cleaned_.size() && cleaned_[pos_ + 1] == '-' && isHex(cleaned_[pos_ + 2])) {
                char b = cleaned_[pos_ + 2];
                int va = hexValue(a);
                int vb = hexValue(b);
                if (va > vb) {
                    throw std::invalid_argument("invalid hex range (start > end)");
                }
                for (int v = va; v <= vb; ++v) {
                    mask.bits |= static_cast<uint16_t>(1) << v;
                }
                pos_ += 3;
            } else {
                mask.bits |= static_cast<uint16_t>(1) << hexValue(a);
                ++pos_;
            }
        }
        if (pos_ >= cleaned_.size() || cleaned_[pos_] != ']') {
            throw std::invalid_argument("unclosed hex character class");
        }
        ++pos_; // skip ']'
        return mask;
    }

    const std::string& s_;
    std::string cleaned_;
    size_t pos_;
};

std::vector<bs_match_t> search_hex_regex(
    const uint8_t* data,
    uint64_t size,
    const std::string& pattern,
    uint64_t start_offset,
    uint64_t max_results,
    std::string* error)
{
    std::vector<bs_match_t> results;
    HexRegexParser parser(pattern);
    std::vector<ByteMask> masks;
    try {
        masks = parser.parse();
    } catch (const std::exception& e) {
        if (error) {
            *error = e.what();
        }
        return results;
    }

    if (masks.empty()) {
        if (error) {
            *error = "empty hex regex";
        }
        return results;
    }
    if (max_results == 0) {
        return results;
    }
    const uint64_t len = masks.size();
    if (size < len || start_offset > size - len) {
        return results;
    }

    const uint64_t limit = size - len;
    for (uint64_t i = start_offset; i <= limit && results.size() < max_results; ++i) {
        bool ok = true;
        for (uint64_t j = 0; j < len; ++j) {
            if (!masks[j].matches(data[i + j])) {
                ok = false;
                break;
            }
        }
        if (ok) {
            results.push_back({i, len});
        }
    }
    return results;
}

std::vector<bs_match_t> search_ascii_regex(
    const uint8_t* data,
    uint64_t size,
    const std::string& pattern,
    uint64_t start_offset,
    uint64_t max_results,
    bool case_insensitive,
    std::string* error)
{
    std::vector<bs_match_t> results;
    if (pattern.empty()) {
        if (error) {
            *error = "empty regex";
        }
        return results;
    }
    if (max_results == 0 || start_offset >= size) {
        return results;
    }

    boost::regex::flag_type flags = boost::regex::perl;
    if (case_insensitive) {
        flags |= boost::regex::icase;
    }

    boost::regex re;
    try {
        re.assign(pattern, flags);
    } catch (const boost::regex_error& e) {
        if (error) {
            *error = e.what();
        }
        return results;
    }

    const char* base = reinterpret_cast<const char*>(data);
    const char* start = base + start_offset;
    const char* end = base + size;

    while (start <= end && results.size() < max_results) {
        boost::cmatch match;
        if (!boost::regex_search(start, end, match, re, boost::match_default)) {
            break;
        }
        uint64_t offset = static_cast<uint64_t>(match[0].first - base);
        uint64_t length = static_cast<uint64_t>(match[0].length());
        results.push_back({offset, length});
        if (length == 0) {
            // Zero-width match: advance by one byte to avoid an infinite loop.
            ++start;
        } else {
            start = match[0].second;
        }
    }
    return results;
}

} // namespace

std::vector<bs_match_t> search_regex_all(
    const uint8_t* data,
    uint64_t size,
    const std::string& pattern,
    uint64_t start_offset,
    uint64_t max_results,
    bool hex_mode,
    bool case_insensitive,
    std::string* error)
{
    if (hex_mode) {
        return search_hex_regex(data, size, pattern, start_offset, max_results, error);
    }
    return search_ascii_regex(data, size, pattern, start_offset, max_results, case_insensitive, error);
}
