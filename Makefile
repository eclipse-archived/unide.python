# Copyright (c) 2017 Contact Software.
#
# All rights reserved. This program and the accompanying materials are
# made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution.
#
# The Eclipse Public License is available at
#     http://www.eclipse.org/legal/epl-v10.html

PKGNAME = unide-python
VENV = env

ifeq ($(OS),Windows_NT)
	ENV = ./$(VENV)/Scripts
    EGGLINK = $(VENV)/lib/site-packages/$(PKGNAME).egg-link
else
	ENV = ./$(VENV)/bin
    EGGLINK = $(VENV)/lib/python2.7/site-packages/$(PKGNAME).egg-link
endif

FLAKE = $(ENV)/flake8
PYLINT = $(ENV)/pylint
YAPF = $(ENV)/yapf
XENON = $(ENV)/xenon
PYROMA = $(ENV)/pyroma
PYTEST = $(ENV)/pytest
COVERALLS = $(ENV)/coveralls
PYTHON = $(ENV)/python
PIP = $(ENV)/pip
TOX = $(ENV)/tox
TWINE = $(ENV)/twine
PYHTON = $(ENV)/python



.PHONY: all tests dist tox clean docs ci yapf

all: tests docs tox dist

$(EGGLINK): $(VENV)
	$(PIP) install -q -e .

tests: $(VENV) $(EGGLINK)
	$(FLAKE) src tests samples
	$(PYLINT) src/unide
	$(XENON) -bB src
	$(PYTEST) --cov tests
	@# FIXME [bgu 20-09-2017]: some coverage functionality from nose is still missing

yapf:
	$(YAPF) -ir src

ci: tests
	$(COVERALLS)

dist: $(VENV)
	$(PYROMA) .
	$(PYTHON) setup.py -q bdist_wheel --universal

publish:
	$(TWINE) upload dist/*

tox: $(VENV)
	pyenv install -s 2.7.13
	pyenv install -s 3.4.6
	pyenv install -s 3.5.3
	pyenv install -s 3.6.2
	pyenv local 2.7.13 3.4.6 3.5.3 3.6.2
	$(TOX)

docs: $(VENV) $(EGGLINK)
	$(PYTHON) -msphinx -M html ./doc ./doc/build -q

clean:
	rm -rf .coverage .tox *~ cover build dist doc/build $(VENV) $(EGGLINK) .python-version

$(VENV): tools.txt additional.txt
	virtualenv -q $(VENV)
	$(PIP) install -q -r tools.txt
	$(PIP) install -q -r additional.txt
