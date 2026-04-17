CC := gcc
CFLAGS := -std=c11 -Wall -Wextra -Wpedantic -O2 -fPIC
LDFLAGS :=

COMMON_OBJ := trash_common.o

all: libtrashhook.so trash-util

libtrashhook.so: trash_hook.o $(COMMON_OBJ)
	$(CC) -shared -o $@ $^ -ldl -lpthread

trash-util: trash_util.o $(COMMON_OBJ)
	$(CC) $(LDFLAGS) -o $@ $^

trash_hook.o: trash_hook.c trash_common.h
	$(CC) $(CFLAGS) -c $< -o $@

trash_util.o: trash_util.c trash_common.h
	$(CC) $(CFLAGS) -c $< -o $@

trash_common.o: trash_common.c trash_common.h
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f *.o libtrashhook.so trash-util

.PHONY: all clean
