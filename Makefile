# Makefile helps calling typical python commands

PYTHON = python2.7
PIP = pip2.7
OPEN = open

.PHONY: help init build test
.PHONY: gen clean clean_all
.PHONY: sdist bdist release upload
.PHONY: doc doc_info
.PHONY: pep8 pep8_diff pep8_fix codestyle

help:
	@echo "make init      setup dev requirements"
	@echo "make init_py   setup python versions via pyenv"
	@echo "make build     build native plugin in-place"
	@echo "make test      run tests"
	@echo
	@echo "make clean     cleanup"
	@echo "make clean_all cleanup all including cython"
	@echo
	@echo "make sdist     make source dist"
	@echo "make bdist     make binary dist (wheel)"
	@echo "make release   build dist and upload"
	@echo "make upload    upload release to pypi"
	@echo
	@echo "make doc       generate docs with sphinx"
	@echo "make doc_info  generate *.rst doc files"
	@echo "make doc_view  generate docs and open in browser"
	@echo
	@echo "make pep8      check source"
	@echo "make pep8_diff show pep8 errors"
	@echo "make pep8_fix  fix pep8 errors"
	@echo "make codestyle check coding style with pycodestyle"


init:
	$(PIP) install -U -r requirements-dev.txt

init_py:
	pyenv install -s 2.7.13
	pyenv install -s 3.4.6
	pyenv install -s 3.5.3
	pyenv install -s 3.6.2
	pyenv local 2.7.13 3.4.6 3.5.3 3.6.2

build:
	$(PYTHON) setup.py build_ext -i

test:
	$(PYTHON) setup.py test

# ----- code gen -----

gen:
	$(PYTHON) setup.py gen

clean:
	$(PYTHON) setup.py clean

clean_all:
	rm -rf bare68k/machine*.so
	rm -f bare68k/machine.c
	rm -rf build dist

# ----- dist -----

sdist:
	python setup.py sdist

bdist:
	python setup.py bdist_wheel

release: clean_all sdist bdist

upload:
	twine upload dist/*

# ----- doc -----

doc_info:
	rst2html.py --strict README.rst build/README.html
	rst2html.py --strict CHANGELOG.rst build/CHANGELOG.html

doc: doc_info
	$(PYTHON) setup.py build_sphinx

doc_view: doc
	$(OPEN) build/sphinx/html/index.html

# ----- pep8 -----

pep8:
	-autopep8 -r --diff . | grep +++

pep8_diff:
	autopep8 -r --diff .

pep8_fix:
	autopep8 -r -i .

codestyle:
	pycodestyle bare68k --ignore=E501
