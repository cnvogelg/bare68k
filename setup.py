from setuptools import setup, find_packages
from Cython.Build import cythonize
from distutils.extension import Extension

sourcefiles = [
  'bare68k/cython/machine.pyx',
  'bare68k/binding/cpu.c',
  'bare68k/binding/mem.c',
  'bare68k/binding/traps.c',
  'bare68k/musashi/m68kcpu.c',
  'bare68k/musashi/m68kdasm.c',
  # gen src
  'gen/m68kopac.c',
  'gen/m68kopdm.c',
  'gen/m68kopnz.c',
  'gen/m68kops.c'
]
depends = [
  'bare68k/cython/cpu.pxd',
  'bare68k/cython/mem.pxd',
  'bare68k/cython/traps.pxd',

  'bare68k/binding/cpu.h',
  'bare68k/binding/mem.h',
  'bare68k/binding/traps.h'
]
inc_dirs = [
  'bare68k/musashi', 'bare68k/binding', 'bare68k', 'gen'
]

extensions = [Extension("bare68k.machine", sourcefiles, depends=depends, include_dirs=inc_dirs)]

setup(
    name = "bare68k",
    version = "0.1",
    packages = find_packages(),
    setup_requires = ['pytest-runner'],
    tests_require=['pytest'],
#    use_scm_version=True,
#    setup_requires=['setuptools_scm'],
    ext_modules = cythonize(extensions) #, output_dir="gen") #, gdb_debug=True)
)

