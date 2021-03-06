#!/usr/bin/env bash

set -e

. venv/bin/activate

pip install -U -r requirements.txt
rstcheck --report warning README.rst
cd docs
make html
touch _build/html/.nojekyll
cp -rf _build/html/* ../../gcpdns-docs/
cd ..
flake8 gcpdns 
rm -rf dist/ build/
python3 setup.py sdist
python3 setup.py bdist_wheel
