.PHONY: all zip ankiweb run clean format check tests
all: ankiweb zip

zip:
	python -m ankibuild --type package --install --qt all

ankiweb:
	python -m ankibuild --type ankiweb --install --qt all

run: zip
	python -m ankirun

format:
	python -m black src/ tests/

check:
	python -m mypy src/ tests/

tests:
	python -m unittest

clean:
	rm -rf build/
