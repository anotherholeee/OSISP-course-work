#define _XOPEN_SOURCE 700
#define _POSIX_C_SOURCE 200809L

#include "trash_common.h"

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <ftw.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

static int ensure_parent_dirs(const char *path) {
    char tmp[PATH_MAX];
    char *p = NULL;

    if (!path) {
        errno = EINVAL;
        return -1;
    }
    if (snprintf(tmp, sizeof(tmp), "%s", path) >= (int)sizeof(tmp)) {
        errno = ENAMETOOLONG;
        return -1;
    }
    p = strrchr(tmp, '/');
    if (!p) {
        return 0;
    }
    *p = '\0';
    if (tmp[0] == '\0') {
        return 0;
    }

    for (char *it = tmp + 1; *it; ++it) {
        if (*it == '/') {
            *it = '\0';
            if (mkdir(tmp, 0700) == -1 && errno != EEXIST) {
                return -1;
            }
            *it = '/';
        }
    }
    if (mkdir(tmp, 0700) == -1 && errno != EEXIST) {
        return -1;
    }
    return 0;
}

static int list_entries(void) {
    DIR *dir = NULL;
    struct dirent *ent = NULL;
    char root[PATH_MAX], files_dir[PATH_MAX], info_dir[PATH_MAX];
    int count = 0;

    if (trash_paths(root, sizeof(root), files_dir, sizeof(files_dir), info_dir, sizeof(info_dir)) != 0) {
        perror("trash paths");
        return 1;
    }

    dir = opendir(info_dir);
    if (!dir) {
        if (errno == ENOENT) {
            puts("Корзина пуста.");
            return 0;
        }
        perror("opendir info");
        return 1;
    }

    puts("ID | Дата удаления | Исходный путь");
    puts("---------------------------------------------------------------");
    while ((ent = readdir(dir)) != NULL) {
        char info_path[PATH_MAX];
        struct trash_entry entry;
        char id[NAME_MAX];
        size_t n = 0;

        if (strcmp(ent->d_name, ".") == 0 || strcmp(ent->d_name, "..") == 0) {
            continue;
        }
        n = strlen(ent->d_name);
        if (n <= strlen(TRASH_INFO_EXT) || strcmp(ent->d_name + n - strlen(TRASH_INFO_EXT), TRASH_INFO_EXT) != 0) {
            continue;
        }

        if (snprintf(info_path, sizeof(info_path), "%s/%s", info_dir, ent->d_name) >= (int)sizeof(info_path)) {
            continue;
        }
        if (trash_parse_info(info_path, &entry) != 0) {
            continue;
        }

        memcpy(id, ent->d_name, n - strlen(TRASH_INFO_EXT));
        id[n - strlen(TRASH_INFO_EXT)] = '\0';

        printf("%s | %s | %s\n", id, entry.deletion_date, entry.original_path);
        count++;
    }

    if (count == 0) {
        puts("Корзина пуста.");
    }
    closedir(dir);
    return 0;
}

static int remove_cb(const char *fpath, const struct stat *sb, int typeflag, struct FTW *ftwbuf) {
    (void)sb;
    (void)ftwbuf;

    if (typeflag == FTW_DP) {
        return rmdir(fpath);
    }
    return unlink(fpath);
}

static int purge_entries(void) {
    char root[PATH_MAX], files_dir[PATH_MAX], info_dir[PATH_MAX];

    if (trash_paths(root, sizeof(root), files_dir, sizeof(files_dir), info_dir, sizeof(info_dir)) != 0) {
        perror("trash paths");
        return 1;
    }

    if (nftw(files_dir, remove_cb, 64, FTW_DEPTH | FTW_PHYS) != 0 && errno != ENOENT) {
        perror("purge files");
        return 1;
    }
    if (nftw(info_dir, remove_cb, 64, FTW_DEPTH | FTW_PHYS) != 0 && errno != ENOENT) {
        perror("purge info");
        return 1;
    }

    if (trash_ensure_layout() != 0) {
        perror("recreate trash layout");
        return 1;
    }

    puts("Корзина очищена.");
    return 0;
}

static int info_entries(void) {
    DIR *dir = NULL;
    struct dirent *ent = NULL;
    char root[PATH_MAX], files_dir[PATH_MAX], info_dir[PATH_MAX];
    size_t count = 0;
    off_t bytes = 0;

    if (trash_paths(root, sizeof(root), files_dir, sizeof(files_dir), info_dir, sizeof(info_dir)) != 0) {
        perror("trash paths");
        return 1;
    }

    bytes = trash_dir_size_bytes(files_dir);
    dir = opendir(info_dir);
    if (dir) {
        while ((ent = readdir(dir)) != NULL) {
            size_t n = strlen(ent->d_name);
            if (n > strlen(TRASH_INFO_EXT) &&
                strcmp(ent->d_name + n - strlen(TRASH_INFO_EXT), TRASH_INFO_EXT) == 0) {
                count++;
            }
        }
        closedir(dir);
    }

    printf("Файлов в корзине: %zu\n", count);
    printf("Занято места: %lld байт\n", (long long)bytes);
    return 0;
}

static int restore_entry(const char *id) {
    char root[PATH_MAX], files_dir[PATH_MAX], info_dir[PATH_MAX];
    char src_path[PATH_MAX], info_path[PATH_MAX];
    struct trash_entry entry;
    char dst[PATH_MAX], unique_dst[PATH_MAX];
    struct stat st;
    struct timespec tv[2];

    if (!id) {
        errno = EINVAL;
        return 1;
    }

    if (trash_paths(root, sizeof(root), files_dir, sizeof(files_dir), info_dir, sizeof(info_dir)) != 0) {
        perror("trash paths");
        return 1;
    }

    if (snprintf(src_path, sizeof(src_path), "%s/%s", files_dir, id) >= (int)sizeof(src_path) ||
        snprintf(info_path, sizeof(info_path), "%s/%s%s", info_dir, id, TRASH_INFO_EXT) >= (int)sizeof(info_path)) {
        fputs("Слишком длинный путь.\n", stderr);
        return 1;
    }

    if (access(src_path, F_OK) != 0) {
        fprintf(stderr, "Элемент с ID '%s' не найден в files.\n", id);
        return 1;
    }
    if (trash_parse_info(info_path, &entry) != 0) {
        perror("parse info");
        return 1;
    }

    if (snprintf(dst, sizeof(dst), "%s", entry.original_path) >= (int)sizeof(dst)) {
        fputs("Слишком длинный исходный путь.\n", stderr);
        return 1;
    }

    if (ensure_parent_dirs(dst) != 0) {
        perror("create parent dirs");
        return 1;
    }

    if (access(dst, F_OK) == 0) {
        if (trash_resolve_unique_path(dst, unique_dst, sizeof(unique_dst)) != 0) {
            perror("resolve unique path");
            return 1;
        }
        if (rename(src_path, unique_dst) != 0) {
            perror("restore rename");
            return 1;
        }
        printf("Конфликт: восстановлено как %s\n", unique_dst);
        if (lstat(unique_dst, &st) == 0) {
            chmod(unique_dst, entry.mode);
            chown(unique_dst, entry.uid, entry.gid);
            tv[0].tv_sec = entry.atime_sec;
            tv[0].tv_nsec = entry.atime_nsec;
            tv[1].tv_sec = entry.mtime_sec;
            tv[1].tv_nsec = entry.mtime_nsec;
            utimensat(AT_FDCWD, unique_dst, tv, 0);
        }
    } else {
        if (rename(src_path, dst) != 0) {
            perror("restore rename");
            return 1;
        }
        chmod(dst, entry.mode);
        chown(dst, entry.uid, entry.gid);
        tv[0].tv_sec = entry.atime_sec;
        tv[0].tv_nsec = entry.atime_nsec;
        tv[1].tv_sec = entry.mtime_sec;
        tv[1].tv_nsec = entry.mtime_nsec;
        utimensat(AT_FDCWD, dst, tv, 0);
        printf("Восстановлено: %s\n", dst);
    }

    if (unlink(info_path) != 0) {
        perror("remove info metadata");
    }
    return 0;
}

static void print_help(const char *argv0) {
    printf("Использование:\n");
    printf("  %s list\n", argv0);
    printf("  %s restore <ID>\n", argv0);
    printf("  %s purge\n", argv0);
    printf("  %s info\n", argv0);
    printf("  %s menu\n", argv0);
}

static int run_menu(void) {
    char line[128];
    char id[NAME_MAX];

    for (;;) {
        puts("\n=== trash-util menu ===");
        puts("1) Показать содержимое корзины (list)");
        puts("2) Восстановить файл по ID (restore)");
        puts("3) Показать статистику (info)");
        puts("4) Очистить корзину (purge)");
        puts("0) Выход");
        printf("Выберите пункт: ");
        fflush(stdout);

        if (!fgets(line, sizeof(line), stdin)) {
            puts("\nЗавершение (EOF).");
            return 0;
        }

        if (line[0] == '1') {
            (void)list_entries();
        } else if (line[0] == '2') {
            printf("Введите ID для восстановления: ");
            fflush(stdout);
            if (!fgets(id, sizeof(id), stdin)) {
                puts("\nВвод прерван.");
                return 1;
            }
            id[strcspn(id, "\n")] = '\0';
            if (id[0] == '\0') {
                puts("ID пустой, операция отменена.");
                continue;
            }
            (void)restore_entry(id);
        } else if (line[0] == '3') {
            (void)info_entries();
        } else if (line[0] == '4') {
            char confirm[16];
            printf("Подтвердите очистку (yes/no): ");
            fflush(stdout);
            if (!fgets(confirm, sizeof(confirm), stdin)) {
                puts("\nВвод прерван.");
                return 1;
            }
            confirm[strcspn(confirm, "\n")] = '\0';
            if (strcmp(confirm, "yes") == 0) {
                (void)purge_entries();
            } else {
                puts("Очистка отменена.");
            }
        } else if (line[0] == '0') {
            puts("Выход из меню.");
            return 0;
        } else {
            puts("Неизвестный пункт меню.");
        }
    }
}

int main(int argc, char **argv) {
    if (argc < 2) {
        return run_menu();
    }

    if (strcmp(argv[1], "list") == 0) {
        return list_entries();
    }
    if (strcmp(argv[1], "restore") == 0) {
        if (argc < 3) {
            fputs("Нужно указать ID для восстановления.\n", stderr);
            return 1;
        }
        return restore_entry(argv[2]);
    }
    if (strcmp(argv[1], "purge") == 0) {
        return purge_entries();
    }
    if (strcmp(argv[1], "info") == 0) {
        return info_entries();
    }
    if (strcmp(argv[1], "menu") == 0) {
        return run_menu();
    }

    print_help(argv[0]);
    return 1;
}
