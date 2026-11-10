[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "hvac-takeoff-app"
version = "0.1.0"
description = "Desktop HVAC takeoff application for estimating duct, pipe, fittings, equipment, and labor."
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
  "openpyxl>=3.1.2",
  "reportlab>=4.2.2",
]

[tool.setuptools]
packages = ["hvac_takeoff"]
