#include "chess_backend.h"
#include "state.h"

#include <vector>
#include <set>
#include <tuple>
#include <cctype>
#include <cmath>
#include <deque>
#include <iostream>

using namespace chess;
using Move = ::Move;

static constexpr std::pair<int,int> pawn_dirs_P[] = {{-1, 0}, {-1,-1}, {-1, 1}};
static constexpr std::pair<int,int> pawn_dirs_p[] = {{ 1, 0}, { 1,-1}, { 1, 1}};
static constexpr std::pair<int,int> knight_dirs[]  = {{-2,-1},{-2, 1},{-1,-2},{-1, 2},{ 1,-2},{ 1, 2},{ 2,-1},{ 2, 1}};
static constexpr std::pair<int,int> bishop_dirs[]  = {{-1,-1},{-1, 1},{ 1,-1},{ 1, 1}};
static constexpr std::pair<int,int> rook_dirs[]    = {{-1, 0},{ 1, 0},{ 0,-1},{ 0, 1}};
static constexpr std::pair<int,int> queen_dirs[]   = {{-1,-1},{-1, 1},{ 1,-1},{ 1, 1},{-1, 0},{ 1, 0},{ 0,-1},{ 0, 1}};
static constexpr std::pair<int,int> king_dirs[]    = {{-1,-1},{-1, 1},{ 1,-1},{ 1, 1},{-1, 0},{ 1, 0},{ 0,-1},{ 0, 1}};

inline int piece_value(char sq) 
{
    switch (sq) 
    {
        case 'P': return  1; case 'N': return  3;
        case 'B': return  3; case 'R': return  5;
        case 'Q': return  9; case 'K': return 100;
        case 'p': return  -1; case 'n': return  -3;
        case 'b': return  -3; case 'r': return  -5;
        case 'q': return  -9; case 'k': return -100;
        default:  return  0;
    }
}

inline bool in_bounds(int row, int col) 
{
    return row >= 0 && row < 8 && col >= 0 && col < 8;
}

inline bool is_square_empty(char sq) 
{
    return sq == ' ' || sq == '\0';
}

inline bool is_opponent(char sq, int turn) 
{
    if (is_square_empty(sq)) return false;
    bool white_piece = std::isupper(static_cast<unsigned char>(sq));
    return turn == 0 ? !white_piece : white_piece;
}

inline AttackMap attacks_on_square(const State &state, int r, int c) 
{
    AttackMap attack_map;
    char target = state.board[r*8 + c];
    if (is_square_empty(target)) return attack_map;
    int turn = std::isupper(static_cast<unsigned char>(target)) ? 0 : 1;

    // Pawn attacks
    for (auto [dr, dc] : pawn_dirs_P) 
    {
        if(dr == 0 || dc == 0)
            continue;
        int nr = r - dr, nc = c - dc;
        if (in_bounds(nr, nc)) {
            char occ = state.board[nr*8 + nc];
            if (occ == 'P' && is_opponent(occ, turn))
                attack_map['P'].push_back({nr, nc});
        }
    }
    for (auto [dr, dc] : pawn_dirs_p) 
    {
        if(dr == 0 || dc == 0)
            continue;
        int nr = r - dr, nc = c - dc;
        if (in_bounds(nr, nc)) 
        {
            char occ = state.board[nr*8 + nc];
            if (occ == 'p' && is_opponent(occ, turn))
                attack_map['p'].push_back({nr, nc});
        }
    }

    // Knight attacks
    for (auto [dr, dc] : knight_dirs) 
    {
        int nr = r + dr, nc = c + dc;
        if (in_bounds(nr, nc)) 
        {
            char occ = state.board[nr*8 + nc];
            if ((occ == 'N' || occ == 'n') && is_opponent(occ, turn))
                attack_map[occ].push_back({nr, nc});
        }
    }

    // King attacks
    for (auto [dr, dc] : king_dirs) 
    {
        int nr = r + dr, nc = c + dc;
        if (in_bounds(nr, nc)) 
        {
            char occ = state.board[nr*8 + nc];
            if ((occ == 'K' || occ == 'k') && is_opponent(occ, turn))
                attack_map[occ].push_back({nr, nc});
        }
    }

    // Bishop/Queen diagonal attacks
    for (auto [dr, dc] : bishop_dirs) 
    {
        int nr = r + dr, nc = c + dc;
        while (in_bounds(nr, nc)) 
        {
            char occ = state.board[nr*8 + nc];
            if (!is_square_empty(occ)) 
            {
                char up = std::toupper(static_cast<unsigned char>(occ));
                if ((up == 'B' || up == 'Q') && is_opponent(occ, turn))
                    attack_map[occ].push_back({nr, nc});
                break;
            }
            nr += dr; nc += dc;
        }
    }

    // Rook/Queen straight attacks
    for (auto [dr, dc] : rook_dirs) 
    {
        int nr = r + dr, nc = c + dc;
        while (in_bounds(nr, nc)) 
        {
            char occ = state.board[nr*8 + nc];
            if (!is_square_empty(occ)) 
            {
                char up = std::toupper(static_cast<unsigned char>(occ));
                if ((up == 'R' || up == 'Q') && is_opponent(occ, turn))
                    attack_map[occ].push_back({nr, nc});
                break;
            }
            nr += dr; nc += dc;
        }
    }

    return attack_map;
}

inline bool king_under_attack(const State &state, int player) 
{
    for (int idx = 0; idx < 64; ++idx) 
    {
        char sq = state.board[idx];
        if ((sq=='K' && player==0) || (sq=='k' && player==1)) 
        {
            int r = idx / 8;
            int c = idx % 8;
            auto atk = attacks_on_square(state, r, c);
            // if (!atk.empty()) 
            // {
            //     std::cerr << "Attackers on king: ";
            //     for (auto& [pc, vec] : atk) std::cerr << pc << ' ';
            //     std::cerr << '\n';
            // }
            return !atk.empty();
        }
    }
    return false;
}

inline bool has_repeated_prefix(const std::deque<Move> &L, int min_pattern_len, int min_repeats)
{
    int n = (int)L.size();
    if (n < min_pattern_len * min_repeats)
        return false;

    std::vector<int> pi(n, 0);
    int j = 0;
    for (int i = 1; i < n; ++i) 
    {
        while (j > 0 && L[i] != L[j])
            j = pi[j - 1];
        if (L[i] == L[j])
            ++j;
        pi[i] = j;
    }

    for (int i = 0; i < n; ++i) 
    {
        int length = i + 1;
        int p = length - pi[i];
        if (p >= min_pattern_len && length % p == 0) 
        {
            int repeats = length / p;
            if (repeats >= min_repeats)
                return true;
        }
    }
    return false;
}

inline bool is_repeat_draw(const State &s)
{
    return has_repeated_prefix(s.hist_white, 2, 3) && has_repeated_prefix(s.hist_black, 2, 3);
}


std::vector<Move> chess::get_legal_moves(const State &state) 
{
    int turn = state.turn;
    // Detect draw by insufficient material
    int pawn_rook_queen = 0;
    int minor_count = 0;
    for (int i = 0; i < 64; ++i) 
    {
        char sq = state.board[i];
        switch (std::toupper(static_cast<unsigned char>(sq))) 
        {
            case 'P': case 'R': case 'Q':
                pawn_rook_queen++;
                break;
            case 'B': case 'N':
                minor_count++;
                break;
            default:
                break;
        }
    }
    if (pawn_rook_queen == 0 && minor_count <= 1) 
    {
        return {};
    }

    turn = state.turn;
    std::set<Move> moves_set, invalid;

    for (int r = 0; r < 8; ++r) 
    {
        for (int c = 0; c < 8; ++c) 
        {
            char pc = state.board[r*8 + c];
            if (is_square_empty(pc)) continue;
            if ((turn == 0 && !std::isupper(static_cast<unsigned char>(pc))) ||
                (turn == 1 && !std::islower(static_cast<unsigned char>(pc)))) continue;

            const std::pair<int,int>* dirs = nullptr;
            int dir_count = 0;
            switch (pc) 
            {
                case 'P': dirs = pawn_dirs_P; dir_count = 3; break;
                case 'p': dirs = pawn_dirs_p; dir_count = 3; break;
                case 'N': case 'n': dirs = knight_dirs;  dir_count = 8; break;
                case 'B': case 'b': dirs = bishop_dirs;  dir_count = 4; break;
                case 'R': case 'r': dirs = rook_dirs;    dir_count = 4; break;
                case 'Q': case 'q': dirs = queen_dirs;   dir_count = 8; break;
                case 'K': case 'k': dirs = king_dirs;    dir_count = 8; break;
                default:  continue;
            }

            for (int i = 0; i < dir_count; ++i) 
            {
                int nr = r + dirs[i].first;
                int nc = c + dirs[i].second;
                if (!in_bounds(nr, nc)) continue;
                char occ = state.board[nr*8 + nc];

                // Pawn logic
                if (pc == 'P' || pc == 'p') 
                {
                    if (dirs[i].second == 0) 
                    {
                        if (is_square_empty(occ)) 
                        {
                            moves_set.insert({{r, c, nr, nc}, 0.0});
                            int start = (pc == 'P' ? 6 : 1);
                            if (r == start) 
                            {
                                int nr2 = r + dirs[i].first * 2;
                                if (in_bounds(nr2, nc) && is_square_empty(state.board[nr2*8 + nc])) 
                                {
                                    moves_set.insert({{r, c, nr2, nc}, 0.0});
                                }
                            }
                        }
                    } 
                    else if (is_opponent(occ, turn) && std::toupper(static_cast<unsigned char>(occ)) != 'K') 
                    {
                        double val = std::abs(piece_value(occ));
                        moves_set.insert({{r, c, nr, nc}, val});
                    }
                }
                // Sliding pieces
                else if (pc=='B'||pc=='b'||pc=='R'||pc=='r'||pc=='Q'||pc=='q') 
                {
                    int step = 0;
                    while (in_bounds(nr, nc)) 
                    {
                        char o2 = state.board[nr*8 + nc];
                        if (is_square_empty(o2)) 
                        {
                            moves_set.insert({{r, c, nr, nc}, 0.0});
                        } 
                        else 
                        {
                            if (is_opponent(o2, turn) && std::toupper(static_cast<unsigned char>(o2)) != 'K') 
                            {
                                double val = std::abs(piece_value(o2));
                                moves_set.insert({{r, c, nr, nc}, val});
                            }
                            break;
                        }
                        ++step;
                        nr = r + dirs[i].first * (step + 1);
                        nc = c + dirs[i].second * (step + 1);
                    }
                }
                // King or Knight
                else 
                {
                    if (is_square_empty(occ)) 
                    {
                        moves_set.insert({{r, c, nr, nc}, 0.0});
                    } 
                    else if (is_opponent(occ, turn) && std::toupper(static_cast<unsigned char>(occ)) != 'K') 
                    {
                        double val = std::abs(piece_value(occ));
                        moves_set.insert({{r, c, nr, nc}, val});
                    }
                }
            }
        }
    }

    // Filter illegal moves
    for (auto &m : moves_set) 
    {
        State s2 = play_move(state, m);
        if (king_under_attack(s2, turn)) invalid.insert(m);
    }
    for (auto &m : invalid) moves_set.erase(m);

    return std::vector<Move>(moves_set.begin(), moves_set.end());
}

State chess::play_move(const State &state, const Move &m) 
{
    std::array<uint8_t,64> bd = state.board;
    uint8_t turn = 1 - state.turn;
    std::deque<Move> hw = state.hist_white;
    std::deque<Move> hb = state.hist_black;
    bool w_ck=state.w_ck, w_cq=state.w_cq, b_ck=state.b_ck, b_cq=state.b_cq;

    if (state.turn == 0) hw.push_front(m); else hb.push_front(m);

    auto [m2, val] = m;
    auto [fr, fc, tr, tc] = m2;
    char pc = bd[fr*8 + fc];
    if (pc == 'K' || (pc == 'R' && fc == 7)) w_ck = false;
    if (pc == 'K' || (pc == 'R' && fc == 0)) w_cq = false;
    if (pc == 'k' || (pc == 'r' && fc == 7)) b_ck = false;
    if (pc == 'k' || (pc == 'r' && fc == 0)) b_cq = false;

    // Castling
    if (pc=='K' && tc-fc==2) { bd[7*8+5]='R'; bd[7*8+7]=' '; }
    if (pc=='k' && tc-fc==2) { bd[0*8+5]='r'; bd[0*8+7]=' '; }
    if (pc=='K' && tc-fc==-2){ bd[7*8+3]='R'; bd[7*8+0]=' '; }
    if (pc=='k' && tc-fc==-2){ bd[0*8+3]='r'; bd[0*8+0]=' '; }

    bd[tr*8+tc] = pc;
    bd[fr*8+fc] = ' ';

    if (tr==0 && pc=='P') bd[tr*8+tc] = 'Q';
    if (tr==7 && pc=='p') bd[tr*8+tc] = 'q';

    return State(bd, turn, w_ck, w_cq, b_ck, b_cq, hw, hb);
}

bool chess::check_win(const State &state)
{
    return get_legal_moves(state).empty() && king_under_attack(state, state.turn);
}

bool chess::check_draw(const State &state)
{
    return (get_legal_moves(state).empty() && !king_under_attack(state, state.turn)) || is_repeat_draw(state);
}

State chess::create_init_state()
{
    std::array<uint8_t,64> bd;

    const char br[] = {'r','n','b','q','k','b','n','r'};
    for (int c = 0; c < 8; ++c) bd[c] = static_cast<uint8_t>(br[c]);
    for (int c = 0; c < 8; ++c) bd[8 + c] = static_cast<uint8_t>('p');
    for (int i = 16; i < 48; ++i) bd[i] = static_cast<uint8_t>(' ');
    for (int c = 0; c < 8; ++c) bd[48 + c] = static_cast<uint8_t>('P');
    const char wr[] = {'R','N','B','Q','K','B','N','R'};
    for (int c = 0; c < 8; ++c) bd[56 + c] = static_cast<uint8_t>(wr[c]);

    return State(bd, 0, true, true, true, true, std::deque<Move>{}, std::deque<Move>{});
}


pybind11::array_t<float> chess::state_to_tensor(const State &state) 
{
    constexpr int C = 17, H = 8, W = 8;
    auto arr = pybind11::array_t<float>({C, H, W});
    auto buf = arr.mutable_unchecked<3>();

    for (int c = 0; c < C; ++c)
        for (int i = 0; i < H; ++i)
            for (int j = 0; j < W; ++j)
                buf(c,i,j) = 0.0f;

    static constexpr char pieces[12] = 
    {
        'P','N','B','R','Q','K',
        'p','n','b','r','q','k'
    };
    for (int idx = 0; idx < 64; ++idx) 
    {
        char pc = static_cast<char>(state.board[idx]);
        int r = idx / 8, f = idx % 8;
        for (int pi = 0; pi < 12; ++pi) 
        {
            if (pc == pieces[pi]) 
            {
                buf(pi, r, f) = 1.0f;
                break;
            }
        }
    }

    float tm = (state.turn == 0 ? 1.0f : 0.0f);
    for (int i = 0; i < H; ++i)
        for (int j = 0; j < W; ++j)
            buf(12, i, j) = tm;

    float wck = state.w_ck ? 1.0f : 0.0f;
    float wcq = state.w_cq ? 1.0f : 0.0f;
    float bck = state.b_ck ? 1.0f : 0.0f;
    float bcq = state.b_cq ? 1.0f : 0.0f;
    for (int i = 0; i < H; ++i)
        for (int j = 0; j < W; ++j) 
        {
            buf(13, i, j) = wck;
            buf(14, i, j) = wcq;
            buf(15, i, j) = bck;
            buf(16, i, j) = bcq;
        }

    return arr;
}

State chess::state_from_fen(const std::string &fen) {
    // Board array to fill
    std::array<uint8_t,64> bd;

    // Split FEN fields
    std::istringstream iss(fen);
    std::string piece_placement, active_color, castling, enpassant;
    int halfmove_clock = 0, fullmove_number = 1;
    iss >> piece_placement >> active_color >> castling >> enpassant \
        >> halfmove_clock >> fullmove_number;

    // 1) Parse piece placement (ranks 8→1, files a→h)
    int idx = 0;
    for (char c : piece_placement) {
        if (c == '/') {
            continue;
        }
        if (std::isdigit(static_cast<unsigned char>(c))) {
            int empty_cnt = c - '0';
            for (int i = 0; i < empty_cnt; ++i) {
                bd[idx++] = static_cast<uint8_t>(' ');
            }
        } else {
            bd[idx++] = static_cast<uint8_t>(c);
        }
    }

    // 2) Active color
    uint8_t turn = (active_color == "w") ? 0 : 1;

    // 3) Castling rights
    bool w_ck = false, w_cq = false, b_ck = false, b_cq = false;
    if (castling.find('K') != std::string::npos) w_ck = true;
    if (castling.find('Q') != std::string::npos) w_cq = true;
    if (castling.find('k') != std::string::npos) b_ck = true;
    if (castling.find('q') != std::string::npos) b_cq = true;

    // 4) We ignore en passant, halfmove and fullmove for now.
    //    Future work could store enpassant square in State.

    // 5) Empty move history
    std::deque<Move> hist_w, hist_b;

    return State(bd, turn, w_ck, w_cq, b_ck, b_cq, hist_w, hist_b);
}
