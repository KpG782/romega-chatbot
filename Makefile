.PHONY: help install run api docker-build docker-run docker-stop test clean deploy

help:
	@echo "Romega Chatbot - Available Commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make run          - Run chatbot in interactive mode"
	@echo "  make api          - Run API server locally"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"
	@echo "  make docker-stop  - Stop Docker container"
	@echo "  make test         - Test the API"
	@echo "  make clean        - Clean up Python cache files"
	@echo "  make deploy       - Deploy with docker-compose"

install:
	pip install -r requirements.txt

run:
	cd src && python agent.py

api:
	cd src && python api.py

docker-build:
	docker build -t romega-chatbot:latest .

docker-run:
	docker run -d \
		--name romega-chatbot \
		-p 8000:8000 \
		--env-file .env \
		--restart unless-stopped \
		romega-chatbot:latest

docker-stop:
	docker stop romega-chatbot
	docker rm romega-chatbot

test:
	@echo "Testing API endpoints..."
	@bash test_api.sh

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete

deploy:
	docker-compose up -d --build

logs:
	docker-compose logs -f
