all: deps lint test

deps:
	@python3 -m pip install --upgrade pip && pip3 install -r requirements-dev.txt

black:
	@black --line-length 120 pytest_mongo_docker tests

isort:
	@isort --line-length 120 --use-parentheses --multi-line 3 --combine-as --trailing-comma pytest_mongo_docker tests

flake8:
	@flake8 --max-line-length 120 --ignore C901,C812,E203,E704 --extend-ignore W503 pytest_mongo_docker tests

mypy:
	@mypy --strict --ignore-missing-imports pytest_mongo_docker tests

lint: black isort flake8 mypy

test:
	@python3 -m pytest -vv --rootdir tests .

pyenv:
	echo pytest_mongo_docker > .python-version && pyenv install -s 3.13 && pyenv virtualenv -f 3.13 pytest_mongo_docker

pyenv-delete:
	pyenv virtualenv-delete -f pytest_mongo_docker


dists:
	python setup.py sdist bdist_wheel
	twine check dist/*
