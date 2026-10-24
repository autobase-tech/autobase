## —— Docker —————————————————————————————————————————————————————————————————————————————————————
TAG ?= local
DOCKER_REGISTRY ?= autobase
DOCKER_BUILD_PLATFORM ?= linux/amd64
DOCKER_PLATFORMS ?= linux/amd64,linux/arm64
DOCKER_BUILDX_BUILDER ?= autobase-builder

# Sanitize the tag by replacing slashes with hyphens for Docker compatibility
SANITIZED_TAG := $(subst /,-,$(TAG))

.PHONY: docker-lint docker-lint-automation
docker-lint: docker-lint-automation ## Lint automation Dockerfile

docker-lint-automation: ## Lint automation Dockerfile
	@echo "Lint automation container Dockerfile"
	docker run --rm -i -v $(PWD)/automation/Dockerfile:/Dockerfile \
	hadolint/hadolint hadolint --ignore DL3002 --ignore DL3008 --ignore DL3013 --ignore DL3059 --ignore DL3066 /Dockerfile

.PHONY: docker-buildx-setup
docker-buildx-setup: ## Set up Docker Buildx builder
	docker buildx inspect $(DOCKER_BUILDX_BUILDER) > /dev/null || docker buildx create --name $(DOCKER_BUILDX_BUILDER)
	docker buildx use $(DOCKER_BUILDX_BUILDER)
	docker buildx inspect --bootstrap > /dev/null

.PHONY: docker-build docker-build-automation
docker-build: ## Build automation Docker image
	$(MAKE) docker-buildx-setup
	$(MAKE) docker-build-automation

docker-build-automation: ## Build automation image
	@echo "Build automation docker image with tag $(TAG) (sanitized as $(SANITIZED_TAG))";
	docker buildx build --no-cache --platform $(DOCKER_BUILD_PLATFORM) --tag automation:$(SANITIZED_TAG) --file automation/Dockerfile --load .

.PHONY: docker-login docker-push docker-push-automation
docker-login: ## Login to Dockerhub
	echo "$(DOCKER_REGISTRY_PASSWORD)" | docker login --username "$(DOCKER_REGISTRY_USER)" --password-stdin

docker-push: ## Build and Push automation image to Dockerhub (example: make docker-push TAG=my_tag DOCKER_REGISTRY=my_repo DOCKER_REGISTRY_USER="my_username" DOCKER_REGISTRY_PASSWORD="my_password")
	$(MAKE) docker-buildx-setup
	$(MAKE) docker-login
	$(MAKE) docker-push-automation

docker-push-automation: ## Build and Push automation to Dockerhub
	@echo "Build and Push automation docker image with tag $(TAG) (sanitized as $(SANITIZED_TAG))";
	docker buildx build --no-cache --platform $(DOCKER_PLATFORMS) --tag $(DOCKER_REGISTRY)/automation:$(SANITIZED_TAG) --file automation/Dockerfile --push .

.PHONY: docker-tests
docker-tests: ## Run tests for docker
	$(MAKE) docker-lint
	$(MAKE) docker-build
