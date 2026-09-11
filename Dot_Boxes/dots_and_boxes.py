from flask import Flask, request, jsonify
from flask_cors import CORS
import math
import copy
import random

app = Flask(__name__)
CORS(app)
# ─────────────────────────────────────────────
# Game Logic (same as your code)
# ─────────────────────────────────────────────

def new_state():
    return {
        "h_lines": [[False] * 3 for _ in range(4)],
        "v_lines": [[False] * 4 for _ in range(3)],
        "boxes":   [[None]  * 3 for _ in range(3)],
        "scores":  {"H": 0, "A": 0},
        "turn":    "H",
        "difficulty": "medium",
        "hints_left": 2
    }

state = new_state() 


def get_all_moves(state):
    moves = []
    for r in range(4):
        for c in range(3):
            if not state["h_lines"][r][c]:
                moves.append(("h", r, c))
    for r in range(3):
        for c in range(4):
            if not state["v_lines"][r][c]:
                moves.append(("v", r, c))
    return moves


def is_terminal(state):
    return len(get_all_moves(state)) == 0


def check_boxes(state, player):
    completed = 0
    for r in range(3):
        for c in range(3):
            if state["boxes"][r][c] is None:
                top    = state["h_lines"][r][c]
                bottom = state["h_lines"][r + 1][c]
                left   = state["v_lines"][r][c]
                right  = state["v_lines"][r][c + 1]
                if top and bottom and left and right:
                    state["boxes"][r][c] = player
                    state["scores"][player] += 1
                    completed += 1
    return completed


def apply_move(state, move, player):
    new = copy.deepcopy(state)
    mtype, r, c = move

    if mtype == "h":
        new["h_lines"][r][c] = True
    else:
        new["v_lines"][r][c] = True

    completed = check_boxes(new, player)

    if completed > 0:
        new["turn"] = player
    else:
        new["turn"] = "A" if player == "H" else "H"

    return new


def evaluate(state):
    return state["scores"]["A"] - state["scores"]["H"]


def minimax(state, depth, alpha, beta, maximizing):
    if is_terminal(state) or depth == 0:
        return evaluate(state), None

    moves = get_all_moves(state)
    if not moves:
     return evaluate(state), None
    best_move = None
    player = "A" if maximizing else "H"

    if maximizing:
        best_val = -math.inf
        for move in moves:
            new = apply_move(state, move, player)
            still_max = (new["turn"] == "A")
            val, _ = minimax(new, depth - 1, alpha, beta, still_max)
            if val > best_val:
                best_val = val
                best_move = move
            alpha = max(alpha, best_val)
            if beta <= alpha:
                break
        return best_val, best_move

    else:
        best_val = math.inf
        for move in moves:
            new = apply_move(state, move, player)
            still_min = (new["turn"] == "H")
            val, _ = minimax(new, depth - 1, alpha, beta, not still_min)
            if val < best_val:
                best_val = val
                best_move = move
            beta = min(beta, best_val)
            if beta <= alpha:
                break
        return best_val, best_move


def ai_move(state, depth=6):
    _, move = minimax(state, depth, -math.inf, math.inf, True)
    return move


# ─────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────

@app.route("/new-game", methods=["POST"])
def new_game():
    global state
    data = request.json or {}

    state = new_state()
    state["difficulty"] = data.get("difficulty", "medium")

    return jsonify(state)


@app.route("/state", methods=["GET"])
def get_state():
    return jsonify(state)


@app.route("/player-move", methods=["POST"])
def player_move():
    global state
    data = request.json

    move = (data["type"], data["row"], data["col"])

    if state["turn"] != "H":
        return jsonify({"error": "Not player's turn"}), 400

    state = apply_move(state, move, "H")
    return jsonify(state)


@app.route("/ai-move", methods=["POST"])
def ai_move_route():
    global state

    if state["turn"] != "A":
        return jsonify({"error": "Not AI turn"}), 400

    difficulty = state.get("difficulty", "medium")

    if difficulty == "easy":
        moves = get_all_moves(state)
        # 80% random (very weak), 20% shallow AI
        if random.random() < 0.8:
            move = random.choice(moves)
        else:
            move = ai_move(state, depth=1)

    elif difficulty == "medium":
        move = ai_move(state, depth=4)

    elif difficulty == "hard":
        move = ai_move(state, depth=5)

    else:
        move = ai_move(state, depth=4)

    state = apply_move(state, move, "A")

    return jsonify({
        "move": move,
        "state": state
    })

@app.route("/hint", methods=["POST"])
def get_hint():
    global state

    if state["hints_left"] <= 0:
        return jsonify({"error": "No hints left"}), 400

    if state["turn"] != "H":
        return jsonify({"error": "Not player's turn"}), 400

    # Use strong AI for hint
    move = ai_move(state, depth=5)

    state["hints_left"] -= 1

    return jsonify({
        "move": move,
        "hints_left": state["hints_left"]
    })

# ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)