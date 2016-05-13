
VASM=vasmm68k_mot

OUTPUT=unpack.bin

$(OUTPUT): stub.s rnc_1.s
	$(VASM) -Fbin -o $(OUTPUT) stub.s
