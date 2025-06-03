#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <random>
#include <cmath>
#include "mcts.h"

namespace py = pybind11;

struct Node 
{
    py::object state;
    std::vector<py::object> moves;
    std::vector<int> Na;
    std::vector<double> Wa;
    std::vector<double> Qa;
    std::vector<Node*> children;
    std::vector<int> untried;
    Node* parent;
    int parent_action_idx;
    int N;

    Node(py::object st, const py::list& move_list, Node* p=nullptr, int idx=-1): state(st), parent(p), parent_action_idx(idx), N(0) 
    {
        for (auto m : move_list) moves.push_back(py::reinterpret_borrow<py::object>(m));
        size_t n = moves.size();
        Na.assign(n, 0);
        Wa.assign(n, 0.0);
        Qa.assign(n, 0.0);
        children.assign(n, nullptr);
        for (size_t i=0;i<n;++i) untried.push_back(i);
    }
    ~Node() 
    {
        for (Node* child : children) delete child;
    }
};

static double UCT(const Node* node, int a, double c) 
{
    if (node->Na[a] == 0) return std::numeric_limits<double>::infinity();
    return node->Qa[a] + c * std::sqrt(std::log((double)node->N) / node->Na[a]);
}

static Node* select(Node* node, double c) 
{
    while (node) 
    {
        if (!node->untried.empty()) return node;
        int best = -1; double best_val=-1e100;
        for (size_t i=0;i<node->children.size();++i) 
        {
            if (!node->children[i]) continue;
            double v = UCT(node, i, c);
            if (v > best_val) { best_val = v; best = (int)i; }
        }
        if (best == -1) return node;
        node = node->children[best];
    }
    return node;
}

static Node* expand(Node* node, py::object backend, py::object policy) 
{
    py::list untried_moves;
    for (int idx : node->untried) untried_moves.append(node->moves[idx]);
    py::object action = policy(untried_moves);
    int local_idx = untried_moves.attr("index")(action).cast<int>();
    int move_idx = node->untried[local_idx];
    node->untried.erase(node->untried.begin()+local_idx);
    py::object new_state = backend.attr("play_move")(node->state, action);
    py::list new_moves = backend.attr("get_legal_moves")(new_state);
    Node* child = new Node(new_state, new_moves, node, move_idx);
    node->children[move_idx] = child;
    return child;
}

static void backprop(Node* node, double result) 
{
    while (node) 
    {
        node->N += 1;
        if (node->parent) 
        {
            int a = node->parent_action_idx;
            Node* parent = node->parent;
            parent->Na[a] += 1;
            parent->Wa[a] -= result;
            parent->Qa[a] = parent->Wa[a] / parent->Na[a];
            node = parent;
            result = -result;
        } 
        else 
        {
            break;
        }
    }
}

py::object get_move(py::object state, py::object value, py::object policy, py::object backend, int simulations, double c, int batch_size) 
{
    py::list moves = backend.attr("get_legal_moves")(state);
    Node* root = new Node(state, moves);
    std::vector<Node*> pending_nodes;
    std::vector<py::object> pending_states;
    auto flush = [&]() 
    {
        if (pending_nodes.empty()) return;
        py::gil_scoped_acquire gil;
        py::list states;
        for (auto& s : pending_states) states.append(s);
        py::object vals_obj = value.attr("batch")(states, py::arg("backend")=backend);
        auto vals = vals_obj.cast<py::list>();
        for (size_t i=0;i<pending_nodes.size();++i) 
        {
            double v = vals[i].cast<double>();
            backprop(pending_nodes[i], v);
        }
        pending_nodes.clear();
        pending_states.clear();
    };

    for (int i=0;i<simulations;i++) 
    {
        Node* node = select(root, c);
        Node* leaf;
        if (!node->untried.empty()) 
        {
            py::gil_scoped_acquire gil;
            leaf = expand(node, backend, policy);
        } 
        else 
        {
            leaf = node;
        }
        pending_nodes.push_back(leaf);
        pending_states.push_back(leaf->state);
        if ((int)pending_nodes.size() >= batch_size) 
        {
            flush();
        }
    }
    flush();
    int best_idx=-1; int best_N=-1;
    for (size_t i=0;i<root->children.size();++i) 
    {
        Node* child = root->children[i];
        if (child && child->N > best_N) { best_N = child->N; best_idx = (int)i; }
    }
    py::object best_move = root->moves[best_idx];
    delete root;
    return best_move;
}

