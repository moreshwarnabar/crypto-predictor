dev:
	uv run services/trades/src/trades/main.py

push:
	kind load docker-image trades:dev --name crypto-cluster

build:
	docker build -t trades:dev -f docker/trades.Dockerfile .

deploy: build push
	kubectl delete -f deployments/dev/trades/trades.yaml
	kubectl apply -f deployments/dev/trades/trades.yaml

lint:
	ruff check . --fix