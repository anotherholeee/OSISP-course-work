#define _POSIX_C_SOURCE 200809L

#include "trash_common.h"

#include <ctype.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <pwd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

static int mkdir_p(const char *path, mode_t mode) {
    char tmp[PATH_MAX];
    size_t len = 0;
    size_t i = 0;

    if (!path || !*path) {
        errno = EINVAL;
        return -1;
    }

    len = strnlen(path, sizeof(tmp));
    if (len == 0 || len >= sizeof(tmp)) {
        errno = ENAMETOOLONG;
        return -1;
    }

    memcpy(tmp, path, len + 1);

    if (tmp[len - 1] == '/') {
        tmp[len - 1] = '\0';
    }

    for (i = 1; tmp[i] != '\0'; ++i) {
        if (tmp[i] == '/') {
            tmp[i] = '\0';
            if (mkdir(tmp, mode) == -1 && errno != EEXIST) {
                return -1;
            }
            tmp[i] = '/';
        }
    }

    if (mkdir(tmp, mode) == -1 && errno != EEXIST) {
        return -1;
    }

    return 0;
}

int trash_get_home(char *buf, size_t size) {
    const char *home = getenv("HOME");
    struct passwd *pw = NULL;

    if (!buf || size == 0) {
        errno = EINVAL;
        return -1;
    }

    if (!home || !*home) {
        pw = getpwuid(getuid());
        if (!pw || !pw->pw_dir) {
            errno = ENOENT;
            return -1;
        }
        home = pw->pw_dir;
    }

    if (snprintf(buf, size, "%s", home) >= (int)size) {
        errno = ENAMETOOLONG;
        return -1;
    }
    return 0;
}

int trash_paths(char *trash_root, size_t root_sz, char *files_dir, size_t files_sz,
                char *info_dir, size_t info_sz) {
    char home[PATH_MAX];

    if (trash_get_home(home, sizeof(home)) != 0) {
        return -1;
    }

    if (snprintf(trash_root, root_sz, "%s/%s", home, TRASH_SUBDIR) >= (int)root_sz) {
        errno = ENAMETOOLONG;
        return -1;
    }
    if (snprintf(files_dir, files_sz, "%s/%s", trash_root, TRASH_FILES_DIR) >= (int)files_sz) {
        errno = ENAMETOOLONG;
        return -1;
    }
    if (snprintf(info_dir, info_sz, "%s/%s", trash_root, TRASH_INFO_DIR) >= (int)info_sz) {
        errno = ENAMETOOLONG;
        return -1;
    }
    return 0;
}

int trash_ensure_layout(void) {
    char root[PATH_MAX];
    char files[PATH_MAX];
    char info[PATH_MAX];

    if (trash_paths(root, sizeof(root), files, sizeof(files), info, sizeof(info)) != 0) {
        return -1;
    }

    if (mkdir_p(root, 0700) != 0) {
        return -1;
    }
    if (mkdir_p(files, 0700) != 0) {
        return -1;
    }
    if (mkdir_p(info, 0700) != 0) {
        return -1;
    }

    return 0;
}

int trash_url_encode_path(const char *src, char *dst, size_t dst_sz) {
    static const char hex[] = "0123456789ABCDEF";
    size_t si = 0;
    size_t di = 0;

    if (!src || !dst || dst_sz == 0) {
        errno = EINVAL;
        return -1;
    }

    while (src[si] != '\0') {
        unsigned char c = (unsigned char)src[si];
        int safe = isalnum(c) || c == '/' || c == '-' || c == '_' || c == '.' || c == '~';
        if (safe) {
            if (di + 1 >= dst_sz) {
                errno = ENAMETOOLONG;
                return -1;
            }
            dst[di++] = (char)c;
        } else {
            if (di + 3 >= dst_sz) {
                errno = ENAMETOOLONG;
                return -1;
            }
            dst[di++] = '%';
            dst[di++] = hex[(c >> 4) & 0x0F];
            dst[di++] = hex[c & 0x0F];
        }
        si++;
    }
    dst[di] = '\0';
    return 0;
}

static int hex_value(char c) {
    if (c >= '0' && c <= '9') {
        return c - '0';
    }
    if (c >= 'a' && c <= 'f') {
        return 10 + (c - 'a');
    }
    if (c >= 'A' && c <= 'F') {
        return 10 + (c - 'A');
    }
    return -1;
}

int trash_url_decode_path(const char *src, char *dst, size_t dst_sz) {
    size_t si = 0;
    size_t di = 0;

    if (!src || !dst || dst_sz == 0) {
        errno = EINVAL;
        return -1;
    }

    while (src[si] != '\0') {
        if (di + 1 >= dst_sz) {
            errno = ENAMETOOLONG;
            return -1;
        }

        if (src[si] == '%' && src[si + 1] != '\0' && src[si + 2] != '\0') {
            int hi = hex_value(src[si + 1]);
            int lo = hex_value(src[si + 2]);
            if (hi >= 0 && lo >= 0) {
                dst[di++] = (char)((hi << 4) | lo);
                si += 3;
                continue;
            }
        }

        dst[di++] = src[si++];
    }

    dst[di] = '\0';
    return 0;
}

int trash_now_iso8601(char *dst, size_t dst_sz) {
    time_t now = time(NULL);
    struct tm tm_buf;

    if (!dst || dst_sz == 0) {
        errno = EINVAL;
        return -1;
    }

    if (localtime_r(&now, &tm_buf) == NULL) {
        return -1;
    }

    if (strftime(dst, dst_sz, "%Y-%m-%dT%H:%M:%S", &tm_buf) == 0) {
        errno = ENAMETOOLONG;
        return -1;
    }
    return 0;
}

int trash_generate_id(const char *path, char *dst, size_t dst_sz) {
    struct timespec ts;
    unsigned long h = 2166136261u;
    size_t i = 0;

    if (!path || !dst || dst_sz == 0) {
        errno = EINVAL;
        return -1;
    }

    if (clock_gettime(CLOCK_REALTIME, &ts) != 0) {
        return -1;
    }

    for (i = 0; path[i] != '\0'; ++i) {
        h ^= (unsigned char)path[i];
        h *= 16777619u;
    }

    if (snprintf(dst, dst_sz, "%ld_%ld_%lu", (long)ts.tv_sec, (long)ts.tv_nsec, h) >= (int)dst_sz) {
        errno = ENAMETOOLONG;
        return -1;
    }
    return 0;
}

int trash_parse_info(const char *info_path, struct trash_entry *entry) {
    FILE *f = NULL;
    char line[TRASH_LINE_BUF];
    char encoded_path[PATH_MAX * 3];
    int got_path = 0;
    int got_date = 0;

    if (!info_path || !entry) {
        errno = EINVAL;
        return -1;
    }

    memset(entry, 0, sizeof(*entry));
    f = fopen(info_path, "r");
    if (!f) {
        return -1;
    }

    while (fgets(line, sizeof(line), f)) {
        if (sscanf(line, "Path=%4095s", encoded_path) == 1) {
            if (trash_url_decode_path(encoded_path, entry->original_path, sizeof(entry->original_path)) == 0) {
                got_path = 1;
            }
            continue;
        }
        if (sscanf(line, "DeletionDate=%63s", entry->deletion_date) == 1) {
            got_date = 1;
            continue;
        }
        (void)sscanf(line, "Mode=%o", &entry->mode);
        (void)sscanf(line, "Uid=%u", &entry->uid);
        (void)sscanf(line, "Gid=%u", &entry->gid);
        (void)sscanf(line, "AtimeSec=%ld", &entry->atime_sec);
        (void)sscanf(line, "AtimeNsec=%ld", &entry->atime_nsec);
        (void)sscanf(line, "MtimeSec=%ld", &entry->mtime_sec);
        (void)sscanf(line, "MtimeNsec=%ld", &entry->mtime_nsec);
    }

    fclose(f);
    if (!got_path || !got_date) {
        errno = EINVAL;
        return -1;
    }
    return 0;
}

int trash_write_info(const char *info_path, const struct trash_entry *entry) {
    FILE *f = NULL;
    char encoded_path[PATH_MAX * 3];

    if (!info_path || !entry) {
        errno = EINVAL;
        return -1;
    }

    if (trash_url_encode_path(entry->original_path, encoded_path, sizeof(encoded_path)) != 0) {
        return -1;
    }

    f = fopen(info_path, "wx");
    if (!f) {
        return -1;
    }

    fprintf(f, "[Trash Info]\n");
    fprintf(f, "Path=%s\n", encoded_path);
    fprintf(f, "DeletionDate=%s\n", entry->deletion_date);
    fprintf(f, "Mode=%o\n", entry->mode);
    fprintf(f, "Uid=%u\n", entry->uid);
    fprintf(f, "Gid=%u\n", entry->gid);
    fprintf(f, "AtimeSec=%ld\n", entry->atime_sec);
    fprintf(f, "AtimeNsec=%ld\n", entry->atime_nsec);
    fprintf(f, "MtimeSec=%ld\n", entry->mtime_sec);
    fprintf(f, "MtimeNsec=%ld\n", entry->mtime_nsec);

    if (fclose(f) != 0) {
        return -1;
    }
    return 0;
}

int trash_resolve_unique_path(const char *base_path, char *dst, size_t dst_sz) {
    int idx = 0;

    if (!base_path || !dst || dst_sz == 0) {
        errno = EINVAL;
        return -1;
    }

    if (snprintf(dst, dst_sz, "%s", base_path) >= (int)dst_sz) {
        errno = ENAMETOOLONG;
        return -1;
    }

    while (access(dst, F_OK) == 0) {
        idx++;
        if (snprintf(dst, dst_sz, "%s.%d", base_path, idx) >= (int)dst_sz) {
            errno = ENAMETOOLONG;
            return -1;
        }
    }

    return 0;
}

off_t trash_dir_size_bytes(const char *path) {
    DIR *dir = NULL;
    struct dirent *ent = NULL;
    off_t total = 0;
    char full[PATH_MAX];
    struct stat st;

    dir = opendir(path);
    if (!dir) {
        return 0;
    }

    while ((ent = readdir(dir)) != NULL) {
        if (strcmp(ent->d_name, ".") == 0 || strcmp(ent->d_name, "..") == 0) {
            continue;
        }
        if (snprintf(full, sizeof(full), "%s/%s", path, ent->d_name) >= (int)sizeof(full)) {
            continue;
        }
        if (lstat(full, &st) != 0) {
            continue;
        }
        if (S_ISDIR(st.st_mode)) {
            total += trash_dir_size_bytes(full);
        } else {
            total += st.st_size;
        }
    }

    closedir(dir);
    return total;
}
