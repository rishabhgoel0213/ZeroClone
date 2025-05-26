#pragma once
#include <array>
#include <deque>
#include <cstdint>
#include <tuple>

using Move = std::tuple<std::tuple<uint8_t,uint8_t,uint8_t,uint8_t>, double>;

struct State {
    std::array<uint8_t,64> board;
    uint8_t turn;               
    uint8_t fifty_move_rule_counter;
    bool w_ck, w_cq, b_ck, b_cq;
    std::deque<Move> hist_white, hist_black;

    State() = default;
    State(const std::array<uint8_t,64>& b, uint8_t t,
          uint8_t f, bool wck, bool wcq, bool bck, bool bcq,
          const std::deque<Move>& hw, const std::deque<Move>& hb): 
          board(b), turn(t), fifty_move_rule_counter(f),
          w_ck(wck), w_cq(wcq), b_ck(bck), b_cq(bcq),
          hist_white(hw), hist_black(hb) {}
};
