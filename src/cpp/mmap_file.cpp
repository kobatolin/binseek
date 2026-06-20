#include "mmap_file.h"

#include <utility>

#ifdef _WIN32
#include <windows.h>
#else
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <cerrno>
#include <cstring>
#endif

namespace {
#ifdef _WIN32
std::string win_error() {
    DWORD err = GetLastError();
    if (err == 0) return "unknown error";
    LPSTR msg = nullptr;
    size_t size = FormatMessageA(
        FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
        nullptr, err, 0, reinterpret_cast<LPSTR>(&msg), 0, nullptr);
    std::string s(msg, size);
    LocalFree(msg);
    return s;
}
#endif
} // namespace

MmapFile::MmapFile()
    : error_()
#ifdef _WIN32
    , hFile_(INVALID_HANDLE_VALUE)
    , hMapping_(nullptr)
#else
    , fd_(-1)
#endif
    , addr_(nullptr)
    , size_(0)
{
}

MmapFile::MmapFile(MmapFile&& other) noexcept
    : error_(std::move(other.error_))
#ifdef _WIN32
    , hFile_(other.hFile_)
    , hMapping_(other.hMapping_)
#else
    , fd_(other.fd_)
#endif
    , addr_(other.addr_)
    , size_(other.size_)
{
#ifdef _WIN32
    other.hFile_ = INVALID_HANDLE_VALUE;
    other.hMapping_ = nullptr;
#else
    other.fd_ = -1;
#endif
    other.addr_ = nullptr;
    other.size_ = 0;
}

MmapFile& MmapFile::operator=(MmapFile&& other) noexcept {
    if (this != &other) {
        close();
        error_ = std::move(other.error_);
#ifdef _WIN32
        hFile_ = other.hFile_;
        hMapping_ = other.hMapping_;
#else
        fd_ = other.fd_;
#endif
        addr_ = other.addr_;
        size_ = other.size_;
#ifdef _WIN32
        other.hFile_ = INVALID_HANDLE_VALUE;
        other.hMapping_ = nullptr;
#else
        other.fd_ = -1;
#endif
        other.addr_ = nullptr;
        other.size_ = 0;
    }
    return *this;
}

MmapFile::~MmapFile() {
    close();
}

bool MmapFile::open(const char* path) {
    close();

#ifdef _WIN32
    hFile_ = CreateFileA(
        path,
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        nullptr,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        nullptr);
    if (hFile_ == INVALID_HANDLE_VALUE) {
        error_ = win_error();
        return false;
    }

    LARGE_INTEGER li;
    if (!GetFileSizeEx(hFile_, &li)) {
        error_ = win_error();
        close();
        return false;
    }
    size_ = static_cast<uint64_t>(li.QuadPart);

    if (size_ == 0) {
        // Empty file: no mapping needed.
        return true;
    }

    hMapping_ = CreateFileMapping(hFile_, nullptr, PAGE_READONLY, 0, 0, nullptr);
    if (!hMapping_) {
        error_ = win_error();
        close();
        return false;
    }

    addr_ = MapViewOfFile(hMapping_, FILE_MAP_READ, 0, 0, 0);
    if (!addr_) {
        error_ = win_error();
        close();
        return false;
    }
#else
    fd_ = ::open(path, O_RDONLY);
    if (fd_ < 0) {
        error_ = std::strerror(errno);
        return false;
    }

    struct stat st;
    if (::fstat(fd_, &st) < 0) {
        error_ = std::strerror(errno);
        close();
        return false;
    }
    size_ = static_cast<uint64_t>(st.st_size);

    if (size_ == 0) {
        return true;
    }

    addr_ = ::mmap(nullptr, size_, PROT_READ, MAP_PRIVATE, fd_, 0);
    if (addr_ == MAP_FAILED) {
        addr_ = nullptr;
        error_ = std::strerror(errno);
        close();
        return false;
    }
#endif
    return true;
}

void MmapFile::close() {
    if (addr_) {
#ifdef _WIN32
        UnmapViewOfFile(addr_);
#else
        ::munmap(addr_, size_);
#endif
        addr_ = nullptr;
    }
#ifdef _WIN32
    if (hMapping_) {
        CloseHandle(hMapping_);
        hMapping_ = nullptr;
    }
    if (hFile_ != INVALID_HANDLE_VALUE) {
        CloseHandle(hFile_);
        hFile_ = INVALID_HANDLE_VALUE;
    }
#else
    if (fd_ >= 0) {
        ::close(fd_);
        fd_ = -1;
    }
#endif
    size_ = 0;
    error_.clear();
}

bool MmapFile::is_open() const {
#ifdef _WIN32
    return hFile_ != INVALID_HANDLE_VALUE;
#else
    return fd_ >= 0;
#endif
}

uint64_t MmapFile::size() const {
    return size_;
}

const uint8_t* MmapFile::data() const {
    return static_cast<const uint8_t*>(addr_);
}

const std::string& MmapFile::error() const {
    return error_;
}
