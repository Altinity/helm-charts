REPO_ROOT ?= $(shell git rev-parse --show-toplevel)
BUILD_DIR ?= $(dir $(realpath -s $(firstword $(MAKEFILE_LIST))))/build
VERSION ?= $(shell git describe --tags --always --dirty)

$(shell mkdir -p ${BUILD_DIR})

docs:
	helm-docs --template-files=templates/install.gotmpl --template-files=README.md.gotmpl

verify:
	${REPO_ROOT}/scripts/validate.sh
	${REPO_ROOT}/scripts/lint.sh

version:
	@echo ${VERSION}

help:
	@grep -E '^[a-zA-Z_-]+:.*$$' $(MAKEFILE_LIST) | sort

.PHONY: version version help docs
