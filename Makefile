.PHONY: all forms zip clean format check tests
all: forms zip

forms: src/import_dialog.py
zip: arq_importer.ankiaddon

src/import_dialog.py: designer/import_dialog.ui
	pyuic5 $^ > $@

arq_importer.ankiaddon: src/*
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
	rm -f arq_importer.ankiaddon
