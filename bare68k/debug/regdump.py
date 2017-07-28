import bare68k.api.cpu as cpu


class RegisterDump(object):

    def __init__(self, regs=None):
        if regs is None:
            self.regs = cpu.get_regs()
        else:
            self.regs = regs

    def get_regs(self):
        """return the registers object directly"""
        return self.regs

    def get_str_lines(self):
        """format the register dump as an array of string lines"""
        return self.regs.get_lines()
