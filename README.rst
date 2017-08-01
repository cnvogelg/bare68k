bare68k
=======

|travis| |appveyor| |rtfd| |coverall|

|pypi-v| |wheel| |pyver| |status|

bare68k allows you to write **m68k system emulators** in Python 2 or 3.  It
consists of a **CPU emulation** for 68000/68020/68EC020 provided by the
`Musashi`_ engine written in native C. A **memory map** with RAM, ROM,
special function is added and you can start the CPU emulation of your system.
You can intercept the running code with a trap mechanism and use powerful
diagnose functions,

written by Christian Vogelgsang <chris@vogelgsang.org>

under the GNU Public License V2

.. _Musashi: https://github.com/kstenerud/Musashi
.. |travis| image:: https://travis-ci.org/cnvogelg/bare68k.svg?branch=master
   :target: https://travis-ci.org/cnvogelg/bare68k
.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/cnvogelg/bare68k?branch=master&svg=true
   :target: https://ci.appveyor.com/project/cnvogelg/bare68k/branch/master
.. |rtfd| image:: https://readthedocs.org/projects/bare68k/badge/?version=latest
   :target: https://readthedocs.org/projects/bare68k
.. |coverall| image:: https://coveralls.io/repos/github/cnvogelg/bare68k/badge.svg?branch=master
   :target: https://coveralls.io/github/cnvogelg/bare68k?branch=master
.. |pypi-v| image:: https://img.shields.io/pypi/v/bare68k.svg
   :target: https://pypi.python.org/pypi/bare68k
.. |wheel| image:: https://img.shields.io/pypi/wheel/bare68k.svg
.. |pyver| image:: https://img.shields.io/pypi/pyversions/bare68k.svg
.. |status| image:: https://img.shields.io/pypi/status/bare68k.svg

Features
--------

* all emulation code written in C for fast speed
* runs on Python 2.7 and Python 3.5
* emulates CPU 68000, 68020, and 68EC020
* use a 24 or 32 bit memory map
* define memory regions for RAM and ROM with page granularity (64k)
* special memory regions that call your code for each read/write operation
* intercept m68k code by placing ALINE-opcode based traps to call your code
* event-based CPU emulation frontend does always return to Python first
* provide Python handlers for all CPU emulation events

  * RESET opcode
  * ALINE trap opcode
  * invalid memory access (e.g. write in ROM region)
  * out of memory bounds (e.g. read above memory map)
  * control interrupt acknowledgement
  * watch and break points
  * custom timers based on CPU cycles

* extensive diagnose functions

  * instruction trace
  * memory access for both CPU and Python API
  * register dump
  * memory labels to mark memory regions with arbitrary Python data
  * all bare68k components use Python logging

* rich API to configure memory and CPU state
* store/restore CPU context

Installation
------------

* use pip::

  $ pip install bare68k

* or checkout github repository and install::

  $ python setup.py install

* use dev setup::

  $ python setup.py develop --user

Documentation
-------------

* the full documentation is hosted at `ReadTheDocs`_

.. _ReadTheDocs: https://bare68k.readthedocs.io/en/latest/
