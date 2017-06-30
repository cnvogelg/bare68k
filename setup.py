from __future__ import print_function

import sys
import os
import subprocess

from setuptools import setup, find_packages
from distutils.extension import Extension
from distutils.command.build_ext import build_ext
from distutils.command.clean import clean
import distutils.ccompiler as ccompiler
from distutils.core import Command
from distutils.dir_util import remove_tree
from distutils import log

# has cython?
try:
  from Cython.Build import cythonize
  has_cython = True
except ImportError:
  has_cython = False

# use cython?
use_cython = has_cython
if '--no-cython' in sys.argv:
  use_cython = False
  sys.argv.remove('--no-cython')
print("use_cython:", use_cython)

here = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
  return open(os.path.join(here, *parts), 'r').read()

gen_src = [
  'gen/m68kopac.c',
  'gen/m68kopdm.c',
  'gen/m68kopnz.c',
  'gen/m68kops.c'
]

gen_tool = "build/m68kmake"
gen_tool_src = "bare68k/musashi/m68kmake.c"
gen_tool_obj = "build/bare68k/musashi/m68kmake.o"
gen_input = "bare68k/musashi/m68k_in.c"
gen_dir = "gen"
build_dir = "build"


class my_build_ext(build_ext):
  """overwrite build_ext to generate code first"""
  def run(self):
    self.run_command('gen')
    build_ext.run(self)


class my_clean(clean):
  """overwrite clean to clean_gen first"""
  def run(self):
    self.run_command('clean_gen')
    clean.run(self)


class GenCommand(Command):
  """my custom code generation command"""
  description = "generate code for Musashi CPU emulator"
  user_options = []
  def initialize_options(self):
    pass
  def finalize_options(self):
    pass
  def run(self):
    # ensure dir exists
    if not os.path.isdir(gen_dir):
      log.info("creating '{}' dir".format(gen_dir))
      os.mkdir(gen_dir)
    if not os.path.isdir(build_dir):
      log.info("creating '{}' dir".format(build_dir))
      os.mkdir(build_dir)
    # build tool first?
    if not os.path.exists(gen_tool):
      log.info("building '{}' tool".format(gen_tool))
      cc = ccompiler.new_compiler()
      cc.compile(sources=[gen_tool_src], output_dir=build_dir)
      cc.link_executable(objects=[gen_tool_obj], output_progname=gen_tool)
      os.remove(gen_tool_obj)
    # generate source?
    if not os.path.exists(gen_src[0]):
      log.info("generating source files")
      cmd = [gen_tool, gen_dir, gen_input]
      subprocess.check_call(cmd)


class CleanGenCommand(Command):
  """my custom code generation cleanup command"""
  description = "remove generated code for Musashi CPU emulator"
  user_options = []
  def initialize_options(self):
    pass
  def finalize_options(self):
    pass
  def run(self):
    if os.path.exists(gen_dir):
      remove_tree(gen_dir, dry_run=self.dry_run)
    # remove tool
    if os.path.exists(gen_tool):
      os.remove(gen_tool)


cmdclass = {
  'gen' : GenCommand,
  'clean_gen' : CleanGenCommand,
  'build_ext' : my_build_ext,
  'clean' : my_clean
}

if use_cython:
  cython_src = 'bare68k/cython/machine.pyx'
else:
  cython_src = 'bare68k/cython/machine.c'

sourcefiles = gen_src + [
  cython_src,

  'bare68k/binding/cpu.c',
  'bare68k/binding/mem.c',
  'bare68k/binding/traps.c',
  'bare68k/binding/tools.c',
  'bare68k/binding/label.c',

  'bare68k/musashi/m68kcpu.c',
  'bare68k/musashi/m68kdasm.c',
]
depends = [
  'bare68k/cython/cpu.pxd',
  'bare68k/cython/mem.pxd',
  'bare68k/cython/traps.pxd',
  'bare68k/cython/tools.pxd',
  'bare68k/cython/label.pxd',

  'bare68k/cython/cpu.pyx',
  'bare68k/cython/mem.pyx',
  'bare68k/cython/traps.pyx',
  'bare68k/cython/tools.pyx',
  'bare68k/cython/disasm.pyx',
  'bare68k/cython/label.pyx',

  'bare68k/binding/cpu.h',
  'bare68k/binding/mem.h',
  'bare68k/binding/traps.h',
  'bare68k/binding/tools.h'
]
inc_dirs = [
  'bare68k/musashi', 'bare68k/binding', 'bare68k', 'gen'
]

extensions = [Extension("bare68k.machine", sourcefiles, depends=depends, include_dirs=inc_dirs)]
if use_cython:
  extensions = cythonize(extensions)

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
    ext_modules = extensions,
    cmdclass = cmdclass
)

