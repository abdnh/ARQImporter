.PHONY: all forms zip clean format check tests
all: zip

forms: src/import_dialog.py
zip: forms ARQImporter.ankiaddon

src/import_dialog.py: designer/import_dialog.ui
	pyuic5 $^ > $@

ARQImporter.ankiaddon: $(shell find src/ -type f)
	rm -f $@
	rm -f src/meta.json
	rm -rf src/__pycache__
	( cd src/; zip -r ../$@ * )

format:
	python -m black src/ tests/

check:
	python -m mypy src/ tests/

tests:
	python -m unittest

clean:
	rm -f *.pyc
	rm -f src/*.pyc
	rm -f src/__pycache__
	rm -f src/import_dialog.py
	rm -f ARQImporter.ankiaddon
