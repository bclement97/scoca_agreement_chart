build:
	docker-compose build

rebuild:
	docker-compose build --pull --no-cache

run: build
	docker-compose up
