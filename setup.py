from setuptools import setup, find_packages

setup(
  name="zeroclone",
  version="0.1.0",
  package_dir={"": "../app"},
  packages=find_packages(where="../app"),
)
