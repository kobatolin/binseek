#include "editor.h"
#include "mmap_file.h"

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

namespace {

constexpr uint64_t WRITE_CHUNK = 1024 * 1024; // 1 MiB

} // namespace

Editor::Editor(const MmapFile* file)
    : file_(file)
{
    if (file_ && file_->size() > 0) {
        segments_.push_back(Segment::base(0, file_->size()));
    }
}

uint64_t Editor::size() const {
    uint64_t total = 0;
    for (const auto& seg : segments_) {
        total += seg.length();
    }
    return total;
}

void Editor::split_at(uint64_t logical_offset) {
    uint64_t pos = 0;
    for (size_t i = 0; i < segments_.size(); ++i) {
        uint64_t seg_len = segments_[i].length();
        if (logical_offset == pos + seg_len) {
            // Split point is exactly at a segment boundary.
            return;
        }
        if (logical_offset > pos && logical_offset < pos + seg_len) {
            uint64_t split = logical_offset - pos;
            Segment orig = segments_[i];
            segments_.erase(segments_.begin() + i);
            if (orig.type == Segment::Base) {
                Segment left = Segment::base(orig.base_offset, split);
                Segment right = Segment::base(orig.base_offset + split, orig.base_len - split);
                segments_.insert(segments_.begin() + i, right);
                segments_.insert(segments_.begin() + i, left);
            } else {
                Segment left = Segment::literal(orig.data.data(), split);
                Segment right = Segment::literal(orig.data.data() + split, orig.data.size() - split);
                segments_.insert(segments_.begin() + i, right);
                segments_.insert(segments_.begin() + i, left);
            }
            return;
        }
        pos += seg_len;
    }
}

void Editor::replace(uint64_t offset, uint64_t old_len, const uint8_t* new_data, uint64_t new_len) {
    split_at(offset);
    split_at(offset + old_len);

    // Now remove every segment fully inside [offset, offset + old_len)
    // and insert the replacement literal at offset.
    uint64_t pos = 0;
    size_t insert_index = segments_.size();
    for (auto it = segments_.begin(); it != segments_.end(); ) {
        uint64_t seg_len = it->length();
        if (pos >= offset && pos + seg_len <= offset + old_len) {
            it = segments_.erase(it);
        } else {
            if (pos == offset) {
                insert_index = static_cast<size_t>(it - segments_.begin());
            }
            ++it;
            pos += seg_len;
        }
    }

    if (new_len > 0) {
        Segment lit = Segment::literal(new_data, new_len);
        segments_.insert(segments_.begin() + insert_index, std::move(lit));
    }
}

void Editor::read(uint64_t offset, uint64_t len, uint8_t* out) const {
    if (len == 0) return;
    uint64_t written = 0;
    uint64_t pos = 0;
    for (const auto& seg : segments_) {
        uint64_t seg_len = seg.length();
        uint64_t seg_end = pos + seg_len;
        if (seg_end <= offset) {
            pos = seg_end;
            continue;
        }
        if (pos >= offset + len) {
            break;
        }
        uint64_t src_start = (offset > pos) ? (offset - pos) : 0;
        uint64_t dst_start = (pos < offset) ? 0 : (pos - offset);
        uint64_t copy_len = std::min(seg_len - src_start, len - dst_start);

        if (seg.type == Segment::Base) {
            const uint8_t* src = file_->data() + seg.base_offset + src_start;
            std::memcpy(out + dst_start, src, static_cast<size_t>(copy_len));
        } else {
            const uint8_t* src = seg.data.data() + src_start;
            std::memcpy(out + dst_start, src, static_cast<size_t>(copy_len));
        }
        written += copy_len;
        if (written >= len) break;
        pos = seg_end;
    }
}

bool Editor::save(const char* path, std::string& error) const {
    std::FILE* f = std::fopen(path, "wb");
    if (!f) {
        error = "failed to open output file";
        return false;
    }

    for (const auto& seg : segments_) {
        if (seg.type == Segment::Base) {
            uint64_t remaining = seg.base_len;
            uint64_t off = seg.base_offset;
            while (remaining > 0) {
                uint64_t chunk = std::min(remaining, WRITE_CHUNK);
                size_t written = std::fwrite(file_->data() + off, 1, static_cast<size_t>(chunk), f);
                if (written != static_cast<size_t>(chunk)) {
                    error = "write error";
                    std::fclose(f);
                    return false;
                }
                off += chunk;
                remaining -= chunk;
            }
        } else {
            if (!seg.data.empty()) {
                size_t written = std::fwrite(seg.data.data(), 1, seg.data.size(), f);
                if (written != seg.data.size()) {
                    error = "write error";
                    std::fclose(f);
                    return false;
                }
            }
        }
    }

    if (std::fclose(f) != 0) {
        error = "close error";
        return false;
    }
    return true;
}
