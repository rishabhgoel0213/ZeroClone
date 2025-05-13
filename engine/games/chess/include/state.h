#pragma once
#include <array>
#include <vector>
#include <tuple>
#include <cstdint>
#include <deque>


using Move = std::tuple<std::tuple<uint8_t,uint8_t,uint8_t,uint8_t>,double>;

struct State 
{
  std::array<uint8_t,64> board;
  uint8_t turn;
  bool w_ck, w_cq, b_ck, b_cq;
  std::deque<Move> hist_white, hist_black;
  State(const std::array<uint8_t,64>& board_, int turn_, bool w_ck_, bool w_cq_, bool b_ck_, bool b_cq_, const std::deque<Move>& hist_white_, const std::deque<Move>& hist_black_): 
    board(board_)
,   turn(turn_)
,   w_ck(w_ck_)
,   w_cq(w_cq_)
,   b_ck(b_ck_)
,   b_cq(b_cq_)
,   hist_white(hist_white_)
,   hist_black(hist_black_){}
};