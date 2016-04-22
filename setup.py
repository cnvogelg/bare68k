import os
from setuptools import setup, find_packages
from Cython.Build import cythonize
from distutils.extension import Extension

here = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
  return open(os.path.join(here, *parts), 'r').read()


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
    description='A package to create m68k system emulators',
    long_description=read("README.md"),
    version = "0.1.0",
    maintainer = "Christian Vogelgsang",
    maintainer_email = "chris@vogelgsang.org",
    url = "http://github.com/cnvogelg/bare68k",
    classifiers = [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Cython",
        "Programming Language :: C",
        "Programming Language :: Python",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: System :: Emulators",
    ],
    license = "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    packages = ['bare68k'],
    zip_safe = False,
    setup_requires = ['pytest-runner'],
    tests_require=['pytest'],
#    use_scm_version=True,
#    setup_requires=['setuptools_scm'],
    ext_modules = cythonize(extensions) #, output_dir="gen") #, gdb_debug=True)
)

