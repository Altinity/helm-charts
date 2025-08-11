REPO_ROOT ?= $(shell git rev-parse --show-toplevel)
BUILD_DIR ?= $(dir $(realpath -s $(firstword $(MAKEFILE_LIST))))/build
VERSION ?= $(shell git describe --tags --always --dirty)

$(shell mkdir -p ${BUILD_DIR})

docs:
	# Generate docs for clickhouse chart with custom template
	helm-docs --chart-search-root=charts/clickhouse --ignore-file=/dev/null --template-files=templates/clickhouse-README.md.gotmpl
	# Generate docs for clickhouse-eks chart with install template (no deprecation notice)
	helm-docs --chart-search-root=charts/clickhouse-eks --ignore-file=/dev/null --template-files=templates/install.gotmpl --template-files=templates/eks-README.md.gotmpl
	# Trim whitespace from generated README files
	for file in $$(find charts -name "README.md"); do \
		sed -i -e '1,2{/^[[:space:]]*$$/d;}' -e 's/[[:space:]]*$$//' "$$file"; \
	done

verify:
	${REPO_ROOT}/scripts/validate.sh
	${REPO_ROOT}/scripts/lint.sh

version:
	@echo ${VERSION}

help:
	@grep -E '^[a-zA-Z_-]+:.*$$' $(MAKEFILE_LIST) | sort

.PHONY: version version help docs
