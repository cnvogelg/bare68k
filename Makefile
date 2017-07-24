# Makefile helps calling typical python commands

PYTHON = python

.PHONY: all dev build test gen clean doc doc_upload

help:
	@echo "make dev       dev setup package"
	@echo "make build     build native plugin in-place"
	@echo "make test      run tests"
	@echo "make clean     cleanup"
	@echo "make doc       generate docs with sphinx"

dev:
	$(PYTHON) setup.py develop --user

build:
	$(PYTHON) setup.py build_ext -i

test:
	$(PYTHON) setup.py test

gen:
	$(PYTHON) setup.py gen

clean:
	$(PYTHON) setup.py clean

doc:
	$(PYTHON) setup.py build_sphinx

doc_upload: doc
	python setup.py upload_docs --upload-dir=site
