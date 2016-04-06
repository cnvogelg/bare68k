# Makefile for musashi

BUILD_DIR = build
GEN_DIR = gen

#CFLAGS    = -O0 -ggdb3
CFLAGS    = -O3

GEN_INPUT = musashi/m68k_in.c

GEN_SRC = m68kopdm.c m68kopnz.c m68kops.c
GEN_HDR = m68kops.h
GEN_FILES = $(patsubst %,$(GEN_DIR)/%,$(GEN_SRC) $(GEN_HDR))
GEN_OBJ = $(patsubst %.c,$(BUILD_DIR)/%.o,$(GEN_SRC))

GEN_TOOL_SRC = musashi/m68kmake.c
GEN_TOOL = m68kmake

PLUGIN = emu.so

DEPS := binding/cpu.c binding/cpu.h
DEPS += binding/mem.c binding/mem.h
DEPS += binding/traps.c binding/traps.h
DEPS += cpu.pxd mem.pxd musashi.pxd
DEPS += machine.pyx

PYTHON = python
#PYTHON = python-dbg

all: $(PLUGIN)

$(PLUGIN): $(GEN_FILES) $(DEPS)
	$(PYTHON) setup.py build_ext -i

do_gen: $(BUILD_DIR)/$(GEN_TOOL) $(GEN_DIR) $(GEN_OBJ)

$(BUILD_DIR)/$(GEN_TOOL): $(BUILD_DIR) $(GEN_TOOL_SRC)
	$(CC) $(CFLAGS) -o $@ $(GEN_TOOL_SRC)

$(BUILD_DIR):
	mkdir $(BUILD_DIR)

$(GEN_DIR):
	mkdir $(GEN_DIR)

$(GEN_FILES): $(BUILD_DIR)/$(GEN_TOOL) $(GEN_DIR) $(GEN_INPUT)
	$(BUILD_DIR)/$(GEN_TOOL) gen $(GEN_INPUT)

clean: clean_gen
	rm -rf $(BUILD_DIR)
	rm -f $(PLUGIN)

clean_gen:
	rm -rf $(GEN_DIR)

