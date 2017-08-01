
.. _apilow:

Low Level API
=============

The low-level API of :mod:`bare68k` is found in the :mod:`bare68k.api`
module. Here the direct native calls to the ``machine`` extension are
available.

While the :mod:`bare68k.api.cpu` CPU and :mod:`bare68k.api.mem` Memory
module are also used in regular code next to the high level :doc:`api`,
all other low level calls are typically wrapped by the high level API.

CPU Access
----------

The functions allow to read and write the current CPU state. All data
``d0-d7`` and address registers ``a0-a7`` are available. Additionally,
special registers like ``USP`` user space stack pointer and ``VBR``
vector base register can be read and written.

.. automodule:: bare68k.api.cpu
   :members:
