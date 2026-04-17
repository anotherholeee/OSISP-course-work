#ifndef TRASH_COMMON_H
#define TRASH_COMMON_H

#define _POSIX_C_SOURCE 200809L

#include <limits.h>
#include <sys/types.h>

#define TRASH_SUBDIR ".local/share/Trash"
#define TRASH_FILES_DIR "files"
#define TRASH_INFO_DIR "info"
#define TRASH_INFO_EXT ".trashinfo"

#define TRASH_LINE_BUF 4096

struct trash_entry {
    char id[NAME_MAX];
    char original_path[PATH_MAX];
    char deletion_date[64];
    mode_t mode;
    uid_t uid;
    gid_t gid;
    long atime_sec;
    long atime_nsec;
    long mtime_sec;
    long mtime_nsec;
};

int trash_get_home(char *buf, size_t size);
int trash_paths(char *trash_root, size_t root_sz, char *files_dir, size_t files_sz,
                char *info_dir, size_t info_sz);
int trash_ensure_layout(void);
int trash_url_encode_path(const char *src, char *dst, size_t dst_sz);
int trash_url_decode_path(const char *src, char *dst, size_t dst_sz);
int trash_now_iso8601(char *dst, size_t dst_sz);
int trash_generate_id(const char *path, char *dst, size_t dst_sz);
int trash_parse_info(const char *info_path, struct trash_entry *entry);
int trash_write_info(const char *info_path, const struct trash_entry *entry);
int trash_resolve_unique_path(const char *base_path, char *dst, size_t dst_sz);
off_t trash_dir_size_bytes(const char *path);

#endif
