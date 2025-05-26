#include "chess_backend.h"
#include "state.h"

#include <vector>
#include <deque>
#include <array>
#include <cctype>
#include <cmath>
#include <algorithm>
#include <sstream>

using namespace chess;
using Move = ::Move;

// ─── Direction tables ───────────────────────────────────────────────────────

static constexpr std::pair<int,int> knight_dirs[] = {
	{-2,-1},{-2, 1},{-1,-2},{-1, 2},
	{ 1,-2},{ 1, 2},{ 2,-1},{ 2, 1}
};
static constexpr std::pair<int,int> bishop_dirs[] = {
	{-1,-1},{-1, 1},{ 1,-1},{ 1, 1}
};
static constexpr std::pair<int,int> rook_dirs[] = {
	{-1, 0},{ 1, 0},{ 0,-1},{ 0, 1}
};
static constexpr std::pair<int,int> queen_dirs[] = {
	{-1,-1},{-1, 1},{ 1,-1},{ 1, 1},
	{-1, 0},{ 1, 0},{ 0,-1},{ 0, 1}
};
static constexpr std::pair<int,int> king_dirs[] = {
	{-1,-1},{-1, 1},{ 1,-1},{ 1, 1},
	{-1, 0},{ 1, 0},{ 0,-1},{ 0, 1}
};

// ─── Tiny inlines ───────────────────────────────────────────────────────────

inline constexpr bool in_bounds(int r,int c)
{
	return (unsigned)r<8 && (unsigned)c<8;
}
inline constexpr bool is_empty(char sq)
{
	return sq==' ' || sq=='\0';
}
inline bool is_opponent(char sq,int turn)
{
	if(is_empty(sq)) return false;
	bool white = std::isupper((unsigned char)sq);
	return (turn==0 ? !white : white);
}
inline int piece_val(char sq)
{
	switch(sq)
	{
		case 'P': case 'p': return 1;
		case 'N': case 'n': return 3;
		case 'B': case 'b': return 3;
		case 'R': case 'r': return 5;
		case 'Q': case 'q': return 9;
		case 'K': case 'k': return 100;
		default:           return 0;
	}
}

// ─── Helper: find the king’s row/col ─────────────────────────────────────────

static void find_king(const State &st,int turn,int &kr,int &kc)
{
	for(int i=0;i<64;i++)
	{
		char sq = st.board[i];
		if(sq == (turn==0 ? 'K' : 'k'))
		{
			kr = i/8;
			kc = i%8;
			return;
		}
	}
	kr = kc = -1;
}

// ─── Check if side-to-move’s king is under attack ───────────────────────────

static bool king_attacked(const State &st,int kr,int kc)
{
	int t = st.turn;
	// Pawn attacks
	if(t==0)
	{
		if(in_bounds(kr-1,kc-1) && st.board[(kr-1)*8+kc-1]=='p') return true;
		if(in_bounds(kr-1,kc+1) && st.board[(kr-1)*8+kc+1]=='p') return true;
	}
	else
	{
		if(in_bounds(kr+1,kc-1) && st.board[(kr+1)*8+kc-1]=='P') return true;
		if(in_bounds(kr+1,kc+1) && st.board[(kr+1)*8+kc+1]=='P') return true;
	}
	// Knights
	for(auto [dr,dc]:knight_dirs)
	{
		int rr = kr+dr, cc = kc+dc;
		if(in_bounds(rr,cc))
		{
			char sq = st.board[rr*8+cc];
			if(sq == (t? 'N' : 'n')) return true;
		}
	}
	// Sliders (rook+queen, bishop+queen)
	struct { const std::pair<int,int>* dirs; int cnt; char p,q; } lines[] = {
		{rook_dirs, 4, t? 'R' : 'r', t? 'Q' : 'q'},
		{bishop_dirs,4, t? 'B' : 'b', t? 'Q' : 'q'}
	};
	for(auto &L: lines)
	{
		for(int i=0;i<L.cnt;i++)
		{
			int rr = kr + L.dirs[i].first;
			int cc = kc + L.dirs[i].second;
			while(in_bounds(rr,cc))
			{
				char sq = st.board[rr*8+cc];
				if(!is_empty(sq))
				{
					if(sq==L.p || sq==L.q) return true;
					break;
				}
				rr += L.dirs[i].first;
				cc += L.dirs[i].second;
			}
		}
	}
	// Adjacent king
	for(auto [dr,dc]:king_dirs)
	{
		int rr = kr+dr, cc = kc+dc;
		if(in_bounds(rr,cc))
		{
			char sq = st.board[rr*8+cc];
			if(sq == (t? 'K' : 'k')) return true;
		}
	}
	return false;
}

// ─── KMP-based repetition helper ────────────────────────────────────────────

inline bool has_repeated_prefix(const std::deque<Move> &L, int min_pattern_len, int min_repeats)
{
	int n = (int)L.size();
	if(n < min_pattern_len * min_repeats)
	{
		return false;
	}
	std::vector<int> pi(n,0);
	int j = 0;
	for(int i=1;i<n;i++)
	{
		while(j>0 && L[i]!=L[j])
		{
			j = pi[j-1];
		}
		if(L[i]==L[j]) ++j;
		pi[i] = j;
	}
	for(int i=0;i<n;i++)
	{
		int length = i+1;
		int p = length - pi[i];
		if(p>=min_pattern_len && length%p==0)
		{
			int reps = length/p;
			if(reps>=min_repeats)
			{
				return true;
			}
		}
	}
	return false;
}

// ─── Generate all legal moves ───────────────────────────────────────────────

std::vector<Move> chess::get_legal_moves(const State &st)
{
	int t = st.turn;
	// Insufficient material?
	int prq=0, minor=0;
	for(char sq: st.board)
	{
		char up = std::toupper((unsigned char)sq);
		if(up=='P'||up=='R'||up=='Q') prq++;
		if(up=='B'||up=='N') minor++;
	}
	if(prq==0 && minor<=1)
	{
		return {};
	}

	std::vector<Move> moves;
	moves.reserve(128);

	for(int idx=0; idx<64; idx++)
	{
		char pc = st.board[idx];
		if(is_empty(pc)) continue;
		bool white_piece = std::isupper((unsigned char)pc);
		if((t==0 && !white_piece)||(t==1 && white_piece)) continue;

		int r = idx/8, c = idx%8;

		// Pawn
		if(pc=='P'||pc=='p')
		{
			int dir = (pc=='P'?-1:1);
			int nr = r+dir, nc = c;
			if(in_bounds(nr,nc) && is_empty(st.board[nr*8+nc]))
			{
				moves.emplace_back(
					std::tuple{std::tuple{(uint8_t)r,(uint8_t)c,(uint8_t)nr,(uint8_t)nc},0.0}
				);
				int sr = (pc=='P'?6:1);
				if(r==sr)
				{
					int nr2 = nr+dir;
					if(in_bounds(nr2,nc) && is_empty(st.board[nr2*8+nc]))
					{
						moves.emplace_back(
							std::tuple{std::tuple{(uint8_t)r,(uint8_t)c,(uint8_t)nr2,(uint8_t)nc},0.0}
						);
					}
				}
			}
			for(int dc:{-1,1})
			{
				int rr = r+dir, cc = c+dc;
				if(in_bounds(rr,cc))
				{
					char os = st.board[rr*8+cc];
					if(is_opponent(os,t) && std::toupper((unsigned char)os)!='K')
					{
						double v = fabs(piece_val(os));
						moves.emplace_back(
							std::tuple{std::tuple{(uint8_t)r,(uint8_t)c,(uint8_t)rr,(uint8_t)cc},v}
						);
					}
				}
			}
			continue;
		}

		// Knight
		if(std::toupper((unsigned char)pc)=='N')
		{
			for(auto [dr,dc]:knight_dirs)
			{
				int rr = r+dr, cc = c+dc;
				if(!in_bounds(rr,cc)) continue;
				char os = st.board[rr*8+cc];
				if(is_empty(os) ||
				   (is_opponent(os,t)&&std::toupper((unsigned char)os)!='K')
				)
				{
					double v = is_opponent(os,t)?fabs(piece_val(os)):0.0;
					moves.emplace_back(
						std::tuple{std::tuple{(uint8_t)r,(uint8_t)c,(uint8_t)rr,(uint8_t)cc},v}
					);
				}
			}
			continue;
		}

		// Bishop/Rook/Queen
		const std::pair<int,int>* dirs = nullptr;
		int dcnt = 0;
		char upc = std::toupper((unsigned char)pc);
		if(upc=='B')
		{
			dirs = bishop_dirs; dcnt = 4;
		}
		else if(upc=='R')
		{
			dirs = rook_dirs;   dcnt = 4;
		}
		else if(upc=='Q')
		{
			dirs = queen_dirs;  dcnt = 8;
		}
		if(dirs)
		{
			for(int i=0;i<dcnt;i++)
			{
				int step = 1;
				int rr = r + dirs[i].first, cc = c + dirs[i].second;
				while(in_bounds(rr,cc))
				{
					char os = st.board[rr*8+cc];
					if(is_empty(os))
					{
						moves.emplace_back(
							std::tuple{std::tuple{(uint8_t)r,(uint8_t)c,(uint8_t)rr,(uint8_t)cc},0.0}
						);
					}
					else
					{
						if(is_opponent(os,t)&&std::toupper((unsigned char)os)!='K')
						{
							moves.emplace_back(
								std::tuple{std::tuple{(uint8_t)r,(uint8_t)c,(uint8_t)rr,(uint8_t)cc},fabs(piece_val(os))}
							);
						}
						break;
					}
					++step;
					rr = r + dirs[i].first * step;
					cc = c + dirs[i].second* step;
				}
			}
			continue;
		}

		// King
		if(upc=='K')
		{
			for(auto [dr,dc]:king_dirs)
			{
				int rr = r+dr, cc = c+dc;
				if(!in_bounds(rr,cc)) continue;
				char os = st.board[rr*8+cc];
				if(is_empty(os) ||
				   (is_opponent(os,t)&&std::toupper((unsigned char)os)!='K')
				)
				{
					double v = is_opponent(os,t)?fabs(piece_val(os)):0.0;
					moves.emplace_back(
						std::tuple{std::tuple{(uint8_t)r,(uint8_t)c,(uint8_t)rr,(uint8_t)cc},v}
					);
				}
			}
			// (castling omitted)
		}
	}

	// filter out moves leaving the mover in check
	std::vector<Move> legal;
	legal.reserve(moves.size());
	for(auto &mv: moves)
	{
		State s2 = play_move(st,mv);
		int mover = st.turn;
		int kr, kc;
		find_king(s2,mover,kr,kc);
		s2.turn = mover;
		if(!king_attacked(s2,kr,kc))
		{
			legal.push_back(mv);
		}
	}
	return legal;
}

// ─── Play a move ────────────────────────────────────────────────────────────

State chess::play_move(const State &state,const Move &m)
{
	std::array<uint8_t,64> bd = state.board;
	uint8_t turn = 1 - state.turn;
	uint8_t fifty = state.fifty_move_rule_counter + 1;
	std::deque<Move> hw = state.hist_white;
	std::deque<Move> hb = state.hist_black;
	bool w_ck = state.w_ck, w_cq = state.w_cq;
	bool b_ck = state.b_ck, b_cq = state.b_cq;

	if(state.turn==0) hw.push_front(m); else hb.push_front(m);

	auto [m2,val] = m;
	auto [fr,fc,tr,tc] = m2;
	char pc = bd[fr*8+fc];
	char trg = bd[tr*8+tc];

	if(pc=='P'||pc=='p'|| !is_empty(trg)) fifty = 0;
	if(pc=='K'||(pc=='R'&&fc==7))   w_ck=false;
	if(pc=='K'||(pc=='R'&&fc==0))   w_cq=false;
	if(pc=='k'||(pc=='r'&&fc==7))   b_ck=false;
	if(pc=='k'||(pc=='r'&&fc==0))   b_cq=false;

	// castling
	if(pc=='K'&&tc-fc==2) { bd[7*8+5]='R'; bd[7*8+7]=' '; }
	if(pc=='k'&&tc-fc==2) { bd[0*8+5]='r'; bd[0*8+7]=' '; }
	if(pc=='K'&&tc-fc==-2){ bd[7*8+3]='R'; bd[7*8+0]=' '; }
	if(pc=='k'&&tc-fc==-2){ bd[0*8+3]='r'; bd[0*8+0]=' '; }

	bd[tr*8+tc] = pc;
	bd[fr*8+fc] = ' ';

	if(tr==0&&pc=='P') bd[tr*8+tc]='Q';
	if(tr==7&&pc=='p') bd[tr*8+tc]='q';

	return State(bd,turn,fifty,w_ck,w_cq,b_ck,b_cq,hw,hb);
}

// ─── Check win ───────────────────────────────────────────────────────────────

bool chess::check_win(const State &state)
{
	auto moves = get_legal_moves(state);
	if(!moves.empty()) return false;

	int kr,kc;
	find_king(state,state.turn,kr,kc);
	return king_attacked(state,kr,kc);
}

// ─── Check draw ──────────────────────────────────────────────────────────────

bool chess::check_draw(const State &state)
{
	auto moves = get_legal_moves(state);
	if(moves.empty())
	{
		int kr,kc;
		find_king(state,state.turn,kr,kc);
		if(!king_attacked(state,kr,kc))
		{
			return true;  // stalemate
		}
	}

	if(state.fifty_move_rule_counter>=50)
	{
		return true;
	}

	if(has_repeated_prefix(state.hist_white,2,3)&&
	   has_repeated_prefix(state.hist_black,2,3))
	{
		return true;
	}

	return false;
}

// ─── Initial position ───────────────────────────────────────────────────────

State chess::create_init_state()
{
	std::array<uint8_t,64> bd;
	const char br[] = {'r','n','b','q','k','b','n','r'};
	for(int i=0;i<8;i++)   bd[i]=br[i];
	for(int i=8;i<16;i++)  bd[i]='p';
	for(int i=16;i<48;i++) bd[i]=' ';
	for(int i=48;i<56;i++) bd[i]='P';
	const char wr[] = {'R','N','B','Q','K','B','N','R'};
	for(int i=56;i<64;i++) bd[i]=wr[i-56];

	return State(bd,0,0,true,true,true,true,{}, {});
}

// ─── State to Tensor ─────────────────────────────────────────────────────────

pybind11::array_t<float> chess::state_to_tensor(const State &st)
{
	constexpr int C=17,H=8,W=8;
	auto arr = pybind11::array_t<float>({C,H,W});
	auto buf = arr.mutable_unchecked<3>();

	for(int c=0;c<C;c++)
	{
		for(int i=0;i<H;i++)
		{
			for(int j=0;j<W;j++)
			{
				buf(c,i,j)=0.0f;
			}
		}
	}

	static constexpr char pieces[12]={
		'P','N','B','R','Q','K',
		'p','n','b','r','q','k'
	};
	for(int idx=0;idx<64;idx++)
	{
		char pc = static_cast<char>(st.board[idx]);
		int r=idx/8,f=idx%8;
		for(int pi=0;pi<12;pi++)
		{
			if(pc==pieces[pi])
			{
				buf(pi,r,f)=1.0f;
				break;
			}
		}
	}

	float tm = (st.turn==0?1.0f:0.0f);
	for(int i=0;i<H;i++)
	{
		for(int j=0;j<W;j++)
		{
			buf(12,i,j)=tm;
		}
	}

	float wck=st.w_ck?1.0f:0.0f;
	float wcq=st.w_cq?1.0f:0.0f;
	float bck=st.b_ck?1.0f:0.0f;
	float bcq=st.b_cq?1.0f:0.0f;
	for(int i=0;i<H;i++)
	{
		for(int j=0;j<W;j++)
		{
			buf(13,i,j)=wck;
			buf(14,i,j)=wcq;
			buf(15,i,j)=bck;
			buf(16,i,j)=bcq;
		}
	}

	return arr;
}

// ─── FEN to State ────────────────────────────────────────────────────────────

State chess::state_from_fen(const std::string &fen)
{
	std::istringstream iss(fen);
	std::string pp,ac,cs,ep;
	int hm, fm;
	iss>>pp>>ac>>cs>>ep>>hm>>fm;

	std::array<uint8_t,64> bd;
	int idx=0;
	for(char c:pp)
	{
		if(c=='/') continue;
		if(std::isdigit((unsigned char)c))
		{
			int cnt=c-'0';
			for(int i=0;i<cnt;i++) bd[idx++]=' ';
		}
		else
		{
			bd[idx++]=c;
		}
	}

	uint8_t turn=(ac=="w"?0:1);
	bool w_ck=false,w_cq=false,b_ck=false,b_cq=false;
	if(cs.find('K')!=std::string::npos) w_ck=true;
	if(cs.find('Q')!=std::string::npos) w_cq=true;
	if(cs.find('k')!=std::string::npos) b_ck=true;
	if(cs.find('q')!=std::string::npos) b_cq=true;

	return State(bd,turn,hm,w_ck,w_cq,b_ck,b_cq,{}, {});
}
