#include <pybind11/pybind11.h>
#include "mcts.h"

namespace py = pybind11;

PYBIND11_MODULE(mcts, m) 
{
    m.doc() = "MCTS algorithm implemented in C++";
    m.def("get_move", &get_move, py::arg("state"), py::arg("value"),
      py::arg("policy"), py::arg("backend"), py::arg("simulations")=1000,
      py::arg("c")=1.4, py::arg("batch_size")=32, py::call_guard<py::gil_scoped_release>());
}
