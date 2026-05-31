.PHONY: help install migrate test test-coverage run clean

help:
	@echo "Covoiturage.Africa - Available commands:"
	@echo ""
	@echo "  make install          - Install dependencies"
	@echo "  make migrate          - Run database migrations"
	@echo "  make test             - Run tests"
	@echo "  make test-coverage   - Run tests with coverage"
	@echo "  make run              - Run development server"
	@echo "  make clean            - Remove temporary files"

install:
	pip install -r requirements.txt

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

test:
	pytest -v

test-coverage:
	pytest --cov=covoiturage --cov-report=html --cov-report=term

test-api:
	pytest covoiturage/tests/test_api.py -v

test-models:
	pytest covoiturage/tests/test_models.py -v

test-views:
	pytest covoiturage/tests/test_views.py -v

run:
	python manage.py runserver

run-production:
	gunicorn carpoolconfig.wsgi:application --bind 0.0.0.0:8000

shell:
	python manage.py shell

admin:
	python manage.py createsuperuser

collectstatic:
	python manage.py collectstatic --noinput

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.egg-info
	rm -rf dist build

lint:
	python -m flake8 covoiturage --max-line-length=100 --ignore=E501,W503
	python -m mypy covoiturage || true

format:
	black covoiturage
	isort covoiturage

deps:
	pip freeze > requirements.txt

docker-build:
	docker build -t covoiturage .

docker-run:
	docker run -p 8000:8000 --env-file .env covoiturage
