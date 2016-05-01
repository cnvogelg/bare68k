# Makefile helps calling typical python commands

PYTHON = python

.PHONY: all do_build_inplace do_test do_gen do_clean

all: do_build_inplace

do_build_inplace:
	$(PYTHON) setup.py build_ext -i

do_test:
	$(PYTHON) setup.py test

do_gen:
	$(PYTHON) setup.py gen

do_clean:
	$(PYTHON) setup.py clean
