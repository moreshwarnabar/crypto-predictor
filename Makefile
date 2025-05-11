dev:
	uv run services/${service}/src/${service}/main.py

build-and-push:
	./scripts/build-and-push-image.sh ${service} ${env}

deploy:
	./scripts/deploy-service.sh ${service} ${env}

lint:
	ruff check . --fix

migrate-table:
	psql -h localhost -p 4567 -d dev -U root -f services/technical_indicators/migration.sql
