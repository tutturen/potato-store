LINTFILES += ./src/products/admin.py
LINTFILES += ./src/products/apps.py
LINTFILES += ./src/products/models.py
LINTFILES += ./src/products/schema.py
LINTFILES += ./src/products/tests.py
LINTFILES += ./src/products/views.py

.PHONY: test
test:
	docker build -f Dockerfile.testing .

.PHONY: docker_build_prod
docker_build_prod:
	docker build -t registry.heroku.com/$(HEROKU_APP)/web -f Dockerfile.production .

.PHONY: docker_push
docker_push_prod:
	docker login --username=_ --password="$(HEROKU_TOKEN)" registry.heroku.com && docker push registry.heroku.com/$(HEROKU_APP)/web

.PHONY: lint
lint: $(LINTFILES)
	pip install pycodestyle
	pycodestyle $^
