from distutils.core import setup
from Cython.Build import cythonize
from distutils.extension import Extension

sourcefiles = [
  'machine.pyx',
  'binding/cpu.c',
  'binding/mem.c',
  'binding/traps.c',
  'musashi/m68kcpu.c',
  'musashi/m68kdasm.c',
  # gen src
  'gen/m68kopac.c',
  'gen/m68kopdm.c',
  'gen/m68kopnz.c',
  'gen/m68kops.c'
]
depends = [
  'cpu.pyx', 'mem.pyx', 'traps.pyx',
  'binding/cpu.h', 'binding/mem.h', 'binding/traps.h'
]
inc_dirs = [
  'musashi', 'gen', 'binding'
]

extensions = [Extension("machine", sourcefiles, depends=depends, include_dirs=inc_dirs)]

setup(
    ext_modules = cythonize(extensions) #, output_dir="gen") #, gdb_debug=True)
)
