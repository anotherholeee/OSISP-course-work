#define _GNU_SOURCE
#define _POSIX_C_SOURCE 200809L

#include "trash_common.h"

#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

typedef int (*unlink_fn_t)(const char *pathname);
typedef int (*unlinkat_fn_t)(int dirfd, const char *pathname, int flags);

static unlink_fn_t real_unlink = NULL;
static unlinkat_fn_t real_unlinkat = NULL;
static pthread_once_t init_once = PTHREAD_ONCE_INIT;
static __thread int in_hook = 0;

static unlink_fn_t resolve_unlink_symbol(void) {
    unlink_fn_t fn = NULL;
    void *sym = dlsym(RTLD_NEXT, "unlink");
    memcpy(&fn, &sym, sizeof(fn));
    return fn;
}

static unlinkat_fn_t resolve_unlinkat_symbol(void) {
    unlinkat_fn_t fn = NULL;
    void *sym = dlsym(RTLD_NEXT, "unlinkat");
    memcpy(&fn, &sym, sizeof(fn));
    return fn;
}

static void init_real_symbols(void) {
    real_unlink = resolve_unlink_symbol();
    real_unlinkat = resolve_unlinkat_symbol();
}

static int call_real_unlink(const char *path) {
    if (!real_unlink) {
        pthread_once(&init_once, init_real_symbols);
    }
    return real_unlink ? real_unlink(path) : (errno = ENOSYS, -1);
}

static int call_real_unlinkat(int dirfd, const char *path, int flags) {
    if (!real_unlinkat) {
        pthread_once(&init_once, init_real_symbols);
    }
    return real_unlinkat ? real_unlinkat(dirfd, path, flags) : (errno = ENOSYS, -1);
}

static int should_bypass(void) {
    const char *v = getenv("TRASH_HOOK_DISABLE");
    return v && strcmp(v, "0") != 0;
}

static int resolve_absolute_from_dirfd(int dirfd, const char *pathname, char *dst, size_t dst_sz) {
    char proc_link[64];
    char dir_path[PATH_MAX];
    ssize_t n = 0;

    if (!pathname || !dst || dst_sz == 0) {
        errno = EINVAL;
        return -1;
    }

    if (pathname[0] == '/') {
        if (snprintf(dst, dst_sz, "%s", pathname) >= (int)dst_sz) {
            errno = ENAMETOOLONG;
            return -1;
        }
        return 0;
    }

    if (dirfd == AT_FDCWD) {
        if (!getcwd(dir_path, sizeof(dir_path))) {
            return -1;
        }
    } else {
        if (snprintf(proc_link, sizeof(proc_link), "/proc/self/fd/%d", dirfd) >= (int)sizeof(proc_link)) {
            errno = ENAMETOOLONG;
            return -1;
        }
        n = readlink(proc_link, dir_path, sizeof(dir_path) - 1);
        if (n < 0) {
            return -1;
        }
        dir_path[n] = '\0';
    }

    if (snprintf(dst, dst_sz, "%s/%s", dir_path, pathname) >= (int)dst_sz) {
        errno = ENAMETOOLONG;
        return -1;
    }

    return 0;
}

static int safe_copy_file(const char *src, const char *dst, mode_t mode) {
    int in_fd = -1;
    int out_fd = -1;
    ssize_t n = 0;
    char buf[64 * 1024];

    in_fd = open(src, O_RDONLY);
    if (in_fd < 0) {
        return -1;
    }
    out_fd = open(dst, O_WRONLY | O_CREAT | O_EXCL, mode & 07777);
    if (out_fd < 0) {
        close(in_fd);
        return -1;
    }

    while ((n = read(in_fd, buf, sizeof(buf))) > 0) {
        ssize_t written = 0;
        while (written < n) {
            ssize_t wn = write(out_fd, buf + written, (size_t)(n - written));
            if (wn < 0) {
                close(in_fd);
                close(out_fd);
                return -1;
            }
            written += wn;
        }
    }

    if (n < 0) {
        close(in_fd);
        close(out_fd);
        return -1;
    }

    if (close(in_fd) != 0 || close(out_fd) != 0) {
        return -1;
    }
    return 0;
}

static int unlink_to_trash_abs(const char *abs_path) {
    struct stat st;
    struct trash_entry entry;
    char root[PATH_MAX];
    char files_dir[PATH_MAX];
    char info_dir[PATH_MAX];
    char home[PATH_MAX];
    char id[NAME_MAX];
    char target_file_base[PATH_MAX];
    char target_file[PATH_MAX];
    char target_info[PATH_MAX];
    int moved = 0;

    if (!abs_path) {
        errno = EINVAL;
        return -1;
    }

    if (lstat(abs_path, &st) != 0) {
        return -1;
    }

    if (S_ISDIR(st.st_mode)) {
        errno = EISDIR;
        return -1;
    }

    if (trash_get_home(home, sizeof(home)) != 0) {
        return -1;
    }

    if (strncmp(abs_path, home, strlen(home)) != 0) {
        return call_real_unlink(abs_path);
    }

    if (trash_ensure_layout() != 0) {
        return call_real_unlink(abs_path);
    }
    if (trash_paths(root, sizeof(root), files_dir, sizeof(files_dir), info_dir, sizeof(info_dir)) != 0) {
        return call_real_unlink(abs_path);
    }

    if (trash_generate_id(abs_path, id, sizeof(id)) != 0) {
        return call_real_unlink(abs_path);
    }
    if (snprintf(target_file_base, sizeof(target_file_base), "%s/%s", files_dir, id) >= (int)sizeof(target_file_base)) {
        return call_real_unlink(abs_path);
    }
    if (trash_resolve_unique_path(target_file_base, target_file, sizeof(target_file)) != 0) {
        return call_real_unlink(abs_path);
    }

    memset(&entry, 0, sizeof(entry));
    if (realpath(abs_path, entry.original_path) == NULL) {
        if (snprintf(entry.original_path, sizeof(entry.original_path), "%s", abs_path) >= (int)sizeof(entry.original_path)) {
            return call_real_unlink(abs_path);
        }
    }
    entry.mode = st.st_mode & 07777;
    entry.uid = st.st_uid;
    entry.gid = st.st_gid;
    entry.atime_sec = st.st_atim.tv_sec;
    entry.atime_nsec = st.st_atim.tv_nsec;
    entry.mtime_sec = st.st_mtim.tv_sec;
    entry.mtime_nsec = st.st_mtim.tv_nsec;
    if (trash_now_iso8601(entry.deletion_date, sizeof(entry.deletion_date)) != 0) {
        return call_real_unlink(abs_path);
    }

    if (rename(abs_path, target_file) == 0) {
        moved = 1;
    } else if (errno == EXDEV) {
        if (safe_copy_file(abs_path, target_file, st.st_mode) == 0 && call_real_unlink(abs_path) == 0) {
            moved = 1;
        } else {
            unlink(target_file);
        }
    }

    if (!moved) {
        return call_real_unlink(abs_path);
    }

    if (snprintf(target_info, sizeof(target_info), "%s/%s%s", info_dir, strrchr(target_file, '/') + 1, TRASH_INFO_EXT) >=
        (int)sizeof(target_info)) {
        call_real_unlink(target_file);
        errno = ENAMETOOLONG;
        return -1;
    }

    if (trash_write_info(target_info, &entry) != 0) {
        call_real_unlink(target_file);
        return -1;
    }

    return 0;
}

int unlink(const char *pathname) {
    char abs_path[PATH_MAX];

    pthread_once(&init_once, init_real_symbols);

    if (in_hook || should_bypass()) {
        return call_real_unlink(pathname);
    }

    in_hook = 1;
    if (resolve_absolute_from_dirfd(AT_FDCWD, pathname, abs_path, sizeof(abs_path)) != 0) {
        in_hook = 0;
        return call_real_unlink(pathname);
    }
    int rc = unlink_to_trash_abs(abs_path);
    in_hook = 0;
    return rc;
}

int unlinkat(int dirfd, const char *pathname, int flags) {
    char abs_path[PATH_MAX];

    pthread_once(&init_once, init_real_symbols);

    if (flags & AT_REMOVEDIR) {
        return call_real_unlinkat(dirfd, pathname, flags);
    }
    if (in_hook || should_bypass()) {
        return call_real_unlinkat(dirfd, pathname, flags);
    }

    in_hook = 1;
    if (resolve_absolute_from_dirfd(dirfd, pathname, abs_path, sizeof(abs_path)) != 0) {
        in_hook = 0;
        return call_real_unlinkat(dirfd, pathname, flags);
    }
    int rc = unlink_to_trash_abs(abs_path);
    in_hook = 0;
    return rc;
}

int remove(const char *pathname) {
    struct stat st;
    if (!pathname) {
        errno = EFAULT;
        return -1;
    }
    if (lstat(pathname, &st) == 0 && S_ISDIR(st.st_mode)) {
        return rmdir(pathname);
    }
    return unlink(pathname);
}
