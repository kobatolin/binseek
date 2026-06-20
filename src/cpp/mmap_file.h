#ifndef MMAP_FILE_H
#define MMAP_FILE_H

#include <cstdint>
#include <cstddef>
#include <string>

class MmapFile {
public:
    MmapFile();
    ~MmapFile();

    MmapFile(const MmapFile&) = delete;
    MmapFile& operator=(const MmapFile&) = delete;

    bool open(const char* path);
    void close();

    bool is_open() const;
    uint64_t size() const;
    const uint8_t* data() const;
    const std::string& error() const;

private:
    std::string error_;
#ifdef _WIN32
    void* hFile_;
    void* hMapping_;
#else
    int fd_;
#endif
    void* addr_;
    uint64_t size_;
};

#endif
