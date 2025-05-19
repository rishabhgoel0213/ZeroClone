from setuptools import setup, find_packages

setup(
  name="game-engine",
  version="0.1.0",
  packages=find_packages(include=["engine=", "model="]),
  exclude_package_data("": ["configs/*", "server/*", "scripts/*", "tests/*"])
)
