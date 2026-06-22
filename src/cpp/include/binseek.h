#ifndef BINSEEK_H
#define BINSEEK_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#ifdef _WIN32
#define BS_API __declspec(dllexport)
#else
#define BS_API
#endif

typedef void* bs_handle_t;

typedef struct {
    uint64_t offset;
    uint64_t length;
} bs_match_t;

BS_API bs_handle_t bs_open(const char* path);
BS_API void        bs_close(bs_handle_t handle);
BS_API const char* bs_get_error(bs_handle_t handle);
BS_API int         bs_get_size(bs_handle_t handle, uint64_t* size);
BS_API int         bs_read_chunk(bs_handle_t handle, uint64_t offset, uint64_t len, uint8_t* out);

BS_API int bs_search(
    bs_handle_t handle,
    const uint8_t* pattern,
    uint64_t pattern_len,
    uint64_t start_offset,
    uint64_t max_results,
    bs_match_t* results,
    uint64_t* result_count);

BS_API int bs_replace(
    bs_handle_t handle,
    uint64_t offset,
    uint64_t old_len,
    const uint8_t* new_data,
    uint64_t new_len);

BS_API int bs_save(bs_handle_t handle, const char* out_path);

#ifdef __cplusplus
}
#endif

#endif
