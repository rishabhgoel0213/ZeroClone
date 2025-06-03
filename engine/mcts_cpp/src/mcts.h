#pragma once
#include <pybind11/pybind11.h>
pybind11::object get_move(pybind11::object state, pybind11::object value, pybind11::object policy, pybind11::object backend, int simulations, double c, int batch_size);
