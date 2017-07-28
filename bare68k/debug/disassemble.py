import bare68k.api.disasm as disasm
import bare68k.api.cpu as cpu
from bare68k.label import LabelFormatter


class InstrLine(object):
    """the disassebmler creates a line info object with all extracted parameters
       for a single instruction line"""

    def __init__(self, pc, words, opcode, args,
                 label=None, annotation=None, cycles=None):
        self.pc = pc
        self.words = words
        self.opcode = opcode
        self.args = args
        self.label = label
        self.annotation = annotation
        self.cycles = cycles

    def __repr__(self):
        return "InstrLine(pc={:08x},words={},opcode={!r}" \
               ",args={!r},label={},annotation={},cycles={})".format(
                   self.pc, self.words, self.opcode, self.args, self.label,
                   self.annotation, self.cycles)


class InstrLineFormatter(object):
    """convert a line info into a string for output"""

    def __init__(self, label_width=20,
                 with_labels=True, with_cycles=True, with_words=True,
                 label_formatter=None):
        self.label_width = label_width
        self.with_cycles = with_cycles
        self.with_words = with_words
        self.with_labels = with_labels
        # setup label formatter
        if label_formatter is None:
            self.label_formatter = LabelFormatter()
        else:
            self.label_formatter = label_formatter

    def __repr__(self):
        return "InstrLineFormatter(label_width={}, with_labels={}," \
            " with_cycles={}, with_words={})".format(
                self.label_width, self.with_labels,
                self.with_cycles, self.with_words)

    def format(self, li):
        """pass a line info and return a formatted string"""
        res = []
        # cycles
        if self.with_cycles and li.cycles is not None:
            res.append(self.get_cycles_str(li.cycles))
        # pc
        pc = "@{:08x}".format(li.pc)
        res.append(pc)
        # label
        if self.with_labels:
            label = li.label
            if label is None:
                txt = ""
            else:
                txt = self.label_formatter.format(label, li.pc)
            f = "{{:{}}}".format(self.label_width)
            label_txt = f.format(txt)
            res.append(label_txt)
        # words
        if self.with_words:
            words = map(lambda x: "{:04x}".format(x), li.words)
            w = "{:14}".format(" ".join(words))
            res.append(w)
        # opcode
        opc = "{:8}".format(li.opcode)
        res.append(opc)
        # args
        args = li.args
        if args is None:
            args = ""
        args = "{:20}".format(args)
        res.append(args)
        # annotation?
        anno = li.annotation
        if anno is not None:
            res.append(anno)
        # result
        return "  ".join(res)

    def get_cycles_str(self, cycles):
        sub_cycles = cycles % 1000000
        top_cycles = cycles / 1000000
        return "%08d.%08d" % (top_cycles, sub_cycles)


class Disassembler(object):
    """a high-level disassembler using musashi's disassembler at its core
       and enriches its output"""

    def __init__(self, buf=None, addr_offset=0,
                 label_mgr=None, annotator=None):
        """disassemble either direct system memory (buffer=None) or
           an external buffer (buf, addr_offset)"""
        self._label_mgr = label_mgr
        self._annotator = annotator
        self._buffer = buf
        # setup disassembler source
        if buf is not None:
            disasm.disassemble_buffer(buf, addr_offset)
        else:
            disasm.disassemble_memory()

    def shutdown(self):
        """free resources and unbind buffer"""
        if self._buffer is not None:
            # revert to memory disassemble
            disasm.disassemble_memory()

    def set_label_mgr(self, label_mgr):
        """set (optional) label manager to show location with label"""
        self._label_mgr = label_mgr

    def set_annotator(self, annotator):
        """the annotator is a callable that gets a line info passed in and
           returns an annotation

           def callable(line_info) -> annotation
        """
        self._annotator = annotator

    def disassemble_str(self, pc):
        """get raw instruction at given pc in memory
           return (opcode,args/None,next_pc)
        """
        pc, words, line = disasm.disassemble(pc)
        opcode, args = self._sanitize_line(line)
        next_pc = pc + len(words) * 2
        return opcode, args, next_pc

    def disassemble(self, pc, cycles=None):
        """return a dictionary with all disassemble information"""
        pc, words, line = disasm.disassemble(pc)
        opcode, args = self._sanitize_line(line)
        next_pc = pc + len(words) * 2
        # add label?
        if self._label_mgr is not None:
            label = self._label_mgr.find_label(pc)
        else:
            label = None
        # add annotation?
        li = InstrLine(pc, words, opcode, args, label, cycles=cycles)
        if self._annotator is not None:
            li.annotation = self._annotator(li)
        # create line info
        return li, next_pc

    def _sanitize_line(self, line):
        """do some transformations of musashi's disassembler output.
           e.g replace a-line calls"""
        # extract opcode and args
        elements = line.split()
        n = len(elements)
        if n < 1:
            raise ValueError("invalid disasm line: " + line)
        opcode = elements[0]
        if n == 1:
            args = None
        elif n == 2:
            args = elements[1]
        else:
            args = "".join(elements[1:])
        # remove comment
        if args is not None:
            pos = args.find(';')
            if pos != -1:
                args = args[:pos]
        # replace (invalid) opcodes
        if opcode == 'dc.w':
            if len(args) == 5 and args[0] == '$':
                opc = int(args[1:], 16)
                # aline
                if opc & 0xf000 == 0xa000:
                    args = "#$%03x" % (opc & 0xfff)
                    opcode = "aline"
        # return result
        return opcode, args
