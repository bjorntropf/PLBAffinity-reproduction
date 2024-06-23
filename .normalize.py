#!/usr/bin/env python3

# pylint: disable=C0103

import glob
import nbformat

for notebook_path in glob.glob("*.ipynb"):
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    nb = nbformat.v4.upgrade(nb)
    nbformat.validate(nb)

    with open(notebook_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
