.PHONY: install_dep
install_dep:
	pip install --user pipenv
	cd src && pipenv install

.PHONY: test
test:
	docker build -f Dockerfile.testing .

.PHONY: docker_build_prod
docker_build_prod:
	docker build -t registry.heroku.com/$(HEROKU_APP)/web -f Dockerfile.production .

.PHONY: docker_push
docker_push_prod:
	docker login --username=_ --password="$(HEROKU_TOKEN)" registry.heroku.com && docker push registry.heroku.com/$(HEROKU_APP)/web
