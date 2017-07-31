
def disassemble(uint32_t pc):
  cdef char line[80]
  cdef unsigned int num_bytes
  cdef unsigned int i
  num_bytes = musashi.m68k_disassemble(line, pc, cpu.cpu_get_type())
  words = []
  for i in range(num_bytes/2):
    words.append(mem.m68k_read_disassembler_16(pc+i*2))
  return (pc, words, <str>line)

def disassemble_range(uint32_t start, uint32_t end):
  cdef uint32_t pc = start
  cdef tuple d
  cdef list result = []
  while pc < end:
    d = disassemble(pc)
    words = d[1]
    num_words = len(words)
    pc += num_words * 2
    result.append(d)
  return result

def disassemble_buffer(bytes buf, uint32_t offset=0):
  cdef const uint8_t *ptr = buf
  cdef unsigned int size = len(buf)
  mem.mem_disasm_buffer(ptr, size, offset)

def disassemble_memory():
  mem.mem_disasm_memory()

def disassemble_is_valid(uint16_t opcode):
  return <bint>musashi.m68k_is_valid_instruction(opcode, cpu.cpu_get_type())
