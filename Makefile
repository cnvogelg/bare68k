# Makefile for musashi

BUILD_DIR = build
GEN_DIR = gen

CFLAGS    = -O3

GEN_INPUT = bare68k/musashi/m68k_in.c

GEN_SRC = m68kopdm.c m68kopnz.c m68kops.c
GEN_HDR = m68kops.h
GEN_FILES = $(patsubst %,$(GEN_DIR)/%,$(GEN_SRC) $(GEN_HDR))

GEN_TOOL_SRC = bare68k/musashi/m68kmake.c
GEN_TOOL = m68kmake

PYTHON = python
#PYTHON = python-dbg

.PHONY: all do_gen do_build_inplace clean_gen clean_gen

all: do_build_inplace

do_build_inplace: do_gen
	$(PYTHON) setup.py build_ext -i

do_test: do_gen
	$(PYTHON) setup.py test

clean: clean_gen
	rm -rf $(BUILD_DIR)

do_gen: $(BUILD_DIR)/$(GEN_TOOL) $(GEN_DIR) $(GEN_FILES)

$(BUILD_DIR)/$(GEN_TOOL): $(BUILD_DIR) $(GEN_TOOL_SRC)
	$(CC) $(CFLAGS) -o $@ $(GEN_TOOL_SRC)

$(BUILD_DIR):
	mkdir $(BUILD_DIR)

$(GEN_DIR):
	mkdir $(GEN_DIR)

$(GEN_FILES): $(BUILD_DIR)/$(GEN_TOOL) $(GEN_DIR) $(GEN_INPUT)
	$(BUILD_DIR)/$(GEN_TOOL) gen $(GEN_INPUT)

clean_gen:
	rm -rf $(GEN_DIR) $(GEN_TOOL)

