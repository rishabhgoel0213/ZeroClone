#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "chess_backend.h"
#include "state.h"

namespace py = pybind11;

PYBIND11_MODULE(chess_backend, m) 
{
      m.doc() = "Chess backend exposed from C++ via pybind11";

      // Bind State struct
      py::class_<State>(m, "State")
            .def
            (
            py::init<
                  const std::array<uint8_t,64>&,
                  uint8_t, uint8_t, bool, bool, bool, bool,
                  const std::deque<Move>&,
                  const std::deque<Move>&
            >(),
            py::arg("board"),
            py::arg("turn"),
            py::arg("fifty_move_rule_counter"),
            py::arg("w_ck"),
            py::arg("w_cq"),
            py::arg("b_ck"),
            py::arg("b_cq"),
            py::arg("hist_white"),
            py::arg("hist_black")
            )
            .def_readwrite("board", &State::board)
            .def_readwrite("turn", &State::turn)
            .def_readwrite("fifty_move_rule_counter", &State::fifty_move_rule_counter)
            .def_readwrite("w_ck", &State::w_ck)
            .def_readwrite("w_cq", &State::w_cq)
            .def_readwrite("b_ck", &State::b_ck)
            .def_readwrite("b_cq", &State::b_cq)
            .def_readwrite("hist_white", &State::hist_white)
            .def_readwrite("hist_black", &State::hist_black)
            ;

      // Expose core chess functions
      m.def("get_legal_moves", &chess::get_legal_moves, py::arg("state"),
            "Generate all legal moves for a given state");
      m.def("state_to_tensor", &chess::state_to_tensor, py::arg("state"),
            "Convert a State into a NumPy tensor (C×8×8)");
      m.def("play_move", &chess::play_move, py::arg("state"), py::arg("move"),
            "Apply a move to a state and return the new state");
      m.def("check_win", &chess::check_win, py::arg("state"),
            "Return true if last move resulted in victory for that player");
      m.def("check_draw", &chess::check_draw, py::arg("state"),
            "Return true is last move resulted in a draw");
      m.def("create_init_state", &chess::create_init_state,
            "Return a fresh State in the standard starting chess position");
      m.def("state_from_fen", &chess::state_from_fen, py::arg("fen"),
            "Create a chess State from a FEN string");

}