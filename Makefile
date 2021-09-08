all: help

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  lint                        to lint backend code (flake8)"
	@echo "  test                        to run test suite"


install:
	pip-sync && pip3 install -e .

lint:
	flake8 timefliptt --max-line-length=120 --ignore=N802