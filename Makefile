# This Makefile helps perform some developer tasks, like linting or testing.
# Run `make` or `make help` to see a list of tasks.

# Override the environment variables to hide the values from the test drivers
unexport MFLAGS
unexport MAKEFLAGS

# Set a variable if it's empty or provided by `make`.
# usage: $(call set_sensible_default, NAME, value)
set_sensible_default = $(if $(filter undefined default,$(origin $(1))),$(2),$(value $(1)))

PYTHON := $(call set_sensible_default,PYTHON,python3)

override AVAILABLE_CC := gcc-5 gcc-6 gcc-8

# Setting CXX and GCOV depending on CC. Only CC has to be set to a specific version.
# If using GitHub actions on Windows, gcc-8 is set but gcc is used, so we override it.
CC := $(call set_sensible_default,CC,gcc-5)
export CC := $(CC)
CXX := $(call set_sensible_default,CXX,$(subst gcc,g++,$(CC)))
export CXX := $(CXX)
GCOV := $(call set_sensible_default,GCOV,$(subst gcc,gcov,$(CC)))

# Get the version of GCC. This is because of #325 (Windows with CC=gcc)
ifeq ($(subst gcc-,,$(CC)),$(CC))
override CC_VERSION := $(shell $(CC) --version | grep -E '^gcc.*\s\(.+\)\s.+$$')
override CC_VERSION := $(word $(words $(CC_VERSION)),$(CC_VERSION))
override CC_VERSION := gcc-$(word 1,$(subst ., ,$(CC_VERSION)))
else
override CC_VERSION := $(CC)
endif
ifeq ($(filter $(CC_VERSION),$(AVAILABLE_CC)),)
$(error Unsupported version of GCC used. CC points to $(CC_VERSION) but must point to one of: $(AVAILABLE_CC))
endif
export CC_VERSION := $(CC_VERSION)

USERID  := $(shell id -u $(USER))
QA_CONTAINER ?= gcovr-qa-$(CC)-uid_$(USERID)
TEST_OPTS ?=
ifeq ($(USE_COVERAGE),true)
override TEST_OPTS += --cov=gcovr --cov-branch
endif

.PHONY: help setup-dev qa lint test doc docker-qa docker-qa-build

help:
	@echo "select one of the following targets:"
	@echo "  help       print this message"
	@echo "  setup-dev  prepare a development environment"
	@echo "  qa         run all QA tasks (lint, test, doc)"
	@echo "  lint       run the flake8 linter"
	@echo "  test       run all tests"
	@echo "  doc        render the docs"
	@echo "  docker-qa  run qa in the docker container"
	@echo "  docker-qa-build"
	@echo "             build the qa docker container"
	@echo ""
	@echo "environment variables:"
	@echo "  PYTHON     Python executable to use [current: $(PYTHON)]"
	@echo "  CC, CXX, GCOV"
	@echo "             the gcc version to use [current: CC=$(CC) CXX=$(CXX) GCOV=$(GCOV)]"
	@echo "  TEST_OPTS  additional flags for pytest [current: $(TEST_OPTS)]"
	@echo "  USE_COVERAGE  if true extend TEST_OPTS with flags for generating coverage data"
	@echo "  QA_CONTAINER"
	@echo "             tag for the qa docker container [current: $(QA_CONTAINER)]"

setup-dev:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt -r doc/requirements.txt
	$(PYTHON) -m pip install -e .
	$(PYTHON) --version
	$(CC) --version
	$(CXX) --version
	$(GCOV) --version

qa: lint black test doc

lint:
	$(PYTHON) -m flake8 doc gcovr

black:
	$(PYTHON) -m black --diff doc gcovr

test: export GCOVR_TEST_SUITE := 1
test: export CC := $(CC)
test: export CXX := $(CXX)
test: export GCOV := $(GCOV)

test:
	$(PYTHON) -m pytest -v --doctest-modules $(TEST_OPTS) -- gcovr doc/examples

doc:
	cd doc && make html O=-W

docker-qa: export TEST_OPTS := $(TEST_OPTS)
docker-qa: export GCOVR_ISOLATED_TEST := zkQEVaBpXF1i

docker-qa: | docker-qa-build
	docker run --rm -e TEST_OPTS -e GCOVR_ISOLATED_TEST -v `pwd`:/gcovr $(QA_CONTAINER)

docker-qa-build: admin/Dockerfile.qa requirements.txt doc/requirements.txt
	docker build --tag $(QA_CONTAINER) \
		--build-arg USERID=$(USERID) \
		--build-arg CC=$(CC) --build-arg CXX=$(CXX) --file $< .
