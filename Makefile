.PHONY: run build rebuild

run: build
	docker-compose up

build:
	docker-compose build

rebuild:
	docker-compose build --pull --no-cache
