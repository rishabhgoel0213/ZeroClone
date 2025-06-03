from setuptools import setup, Extension
import pybind11

ext = Extension(
    'mcts_cpp',
    sources=['src/bindings_mcts.cpp', 'src/mcts.cpp'],
    include_dirs=[pybind11.get_include()],
    language='c++',
    extra_compile_args=['-O3', '-std=c++17', '-march=native', '-funroll-loops', '-ffast-math'],
)

setup(
    name='mcts_cpp',
    install_requires=['numpy<2.0', 'pybind11'],
    ext_modules=[ext]
)
