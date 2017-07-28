# Makefile helps calling typical python commands

PYTHON = python
PIP = pip
OPEN = open

.PHONY: help init build test
.PHONY: gen clean
.PHONY: sdist release
.PHONY: doc doc_info
.PHONY: pep8 pep8_diff pep8_fix

help:
	@echo "make init      setup dev requirements"
	@echo "make build     build native plugin in-place"
	@echo "make test      run tests"
	@echo
	@echo "make clean     cleanup"
	@echo "make clean     cleanup"
	@echo
	@echo "make sdist     make source dist"
	@echo "make release   build dist and upload"
	@echo
	@echo "make doc       generate docs with sphinx"
	@echo "make doc_info  generate *.rst doc files"
	@echo "make doc_view  generate docs and open in browser"
	@echo
	@echo "make pep8      check source"
	@echo "make pep8_diff show pep8 errors"
	@echo "make pep8_fix  fix pep8 errors"


init:
	$(PIP) install -U -r requirements-dev.txt

build:
	$(PYTHON) setup.py build_ext -i

test:
	$(PYTHON) setup.py test

# ----- code gen -----

gen:
	$(PYTHON) setup.py gen

clean:
	$(PYTHON) setup.py clean

# ----- dist -----

sdist:
	rm -rf dist
	python setup.py sdist

release: sdist
	twine dist/*

# ----- doc -----

doc_info:
	rst2html.py --strict README.rst build/README.thml
	rst2html.py --strict CHANGELOG.rst build/CHANGELOG.html

doc: doc_info
	$(PYTHON) setup.py build_sphinx

doc_view: doc
	$(OPEN) build/sphinx/html/index.html

# ----- pep8 -----

pep8:
	autopep8 -r --diff . | grep +++

pep8_diff:
	autopep8 -r --diff .

pep8_fix:
	autopep8 -r -i .
