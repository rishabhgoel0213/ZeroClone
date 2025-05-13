from setuptools import setup, Extension
import pybind11

ext = Extension(
  'chess_backend',
  sources=['src/bindings_chess.cpp', 'src/chess_backend.cpp'],
  include_dirs=[pybind11.get_include(), 'include'],
  language='c++',
  extra_compile_args=[
    "-O3",
    "-march=native",
],
)
setup(
    name='chess_backend', 
    install_requires=["numpy<2.0", "pybind11"],
    ext_modules=[ext]
  )