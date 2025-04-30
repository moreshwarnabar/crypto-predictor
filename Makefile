dev:
	uv run services/${service}/src/${service}/main.py

build-dev:
	docker build -t ${service}:dev --build-arg SERVICE=${service} -f docker/${name}.Dockerfile .

push-dev:
	kind load docker-image ${service}:dev --name crypto-cluster

deploy-dev: build-dev push-dev
	kubectl delete -f deployments/dev/${service}/${service}.yaml --ignore-not-found=true
	kubectl apply -f deployments/dev/${service}/${service}.yaml

lint:
	ruff check . --fix

build-push-prod:
	@BUILD_DATE=$$(date +%s) && \
	docker buildx build --push \
		--platform linux/amd64 \
		-t ghcr.io/moreshwarnabar/crypto-${service}:0.1.1-beta.$$BUILD_DATE \
		-f docker/${service}.Dockerfile .

deploy-prod:
	kubectl delete -f deployments/prod/${service}/${service}.yaml --ignore-not-found=true
	kubectl apply -f deployments/prod/${service}/${service}.yaml