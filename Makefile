
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

UTC_ISO_DATE = $(shell date -u +"%Y-%m-%d%Z")
UTC_ISO_TIME = $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")


.DEFAULT_GOAL := help
.PHONY: help
help: ## Display this message
	@grep -E \
		'^[a-zA-Z\.\$$/]+.*:.*?##\s.*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-38s\033[0m %s\n", $$1, $$2}'

.PHONY: p
p: ## Lazy push to GitHub
	git add -u .
	-git commit -m "update"
	git push origin $(shell git rev-parse --abbrev-ref HEAD)

