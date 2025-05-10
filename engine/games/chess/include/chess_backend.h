#pragma once
#include "state.h"
#include <vector>
#include <map>
#include <string>
#include <pybind11/numpy.h>

struct Position
{
    int row;
    int col;
};

using AttackMap = std::map<char, std::vector<Position>>;

namespace chess 
{
  std::vector<Move> get_legal_moves(const State &state);
  State play_move(const State &state, const Move &m);
  bool check_win(const State &state);
  bool check_draw(const State &state);
  State create_init_state();
  pybind11::array_t<float> state_to_tensor(const State &state);
}