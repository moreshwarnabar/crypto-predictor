dev:
	uv run services/${service}/src/${service}/main.py

build-and-push:
	./scripts/build-and-push-image.sh ${service} ${env}

deploy:
	./scripts/deploy-service.sh ${service} ${env}

lint:
	ruff check . --fix