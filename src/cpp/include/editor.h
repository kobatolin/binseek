#ifndef EDITOR_H
#define EDITOR_H

#include <cstdint>
#include <cstddef>
#include <vector>
#include <string>

class MmapFile;

class Editor {
public:
    struct Segment {
        enum Type { Base, Literal } type;
        // Base segment references [base_offset, base_offset + base_len) in the original file.
        uint64_t base_offset = 0;
        uint64_t base_len = 0;
        // Literal segment stores its own bytes.
        std::vector<uint8_t> data;

        static Segment base(uint64_t offset, uint64_t len) {
            Segment s; s.type = Base; s.base_offset = offset; s.base_len = len; return s;
        }
        static Segment literal(const uint8_t* bytes, uint64_t len) {
            Segment s; s.type = Literal; s.data.assign(bytes, bytes + len); return s;
        }
        uint64_t length() const { return type == Base ? base_len : data.size(); }
    };

    explicit Editor(const MmapFile* file);

    // Replace [offset, offset + old_len) logical bytes with new_data.
    void replace(uint64_t offset, uint64_t old_len, const uint8_t* new_data, uint64_t new_len);

    uint64_t size() const;

    void read(uint64_t offset, uint64_t len, uint8_t* out) const;

    bool save(const char* path, std::string& error) const;

private:
    const MmapFile* file_;
    std::vector<Segment> segments_;

    void split_at(uint64_t logical_offset);
    void rebuild_size();
};

#endif
