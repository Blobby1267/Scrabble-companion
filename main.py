import streamlit as st
import os

BOARD_SIZE = 15

LETTER_SCORES = {
    **dict.fromkeys(list("aeilnorstu"), 1),
    **dict.fromkeys(list("dg"), 2),
    **dict.fromkeys(list("bcmp"), 3),
    **dict.fromkeys(list("fhvwy"), 4),
    "k": 5,
    **dict.fromkeys(list("jx"), 8),
    **dict.fromkeys(list("qz"), 10),
}

def load_dictionary(path="Oxford5000.txt"):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return set(w.strip().lower() for w in f if w.strip())
    return {"hello", "world", "scrabble", "python", "play"}

ENGLISH_WORDS = load_dictionary()

def create_board():
    return [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

def place_word(board, word, row, col, direction):
    word = word.upper()
    for i, ch in enumerate(word):
        r = row + i if direction.upper() == "V" else row
        c = col + i if direction.upper() == "H" else col
        board[r][c] = ch
    return board

def undo_word(previous_board):
    return [r.copy() for r in previous_board]

def find_anchor_squares(board):
    anchors = set()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != ".":
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    rr, cc = r+dr, c+dc
                    if 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE and board[rr][cc] == ".":
                        anchors.add((rr,cc))
    return anchors if anchors else {(BOARD_SIZE//2, BOARD_SIZE//2)}

def possible_words(rack, must_include=None):
    rack = rack.upper()
    results = []
    for word in ENGLISH_WORDS:
        word = word.upper()
        temp_rack = list(rack)
        can_make = True
        for ch in word:
            if ch in temp_rack:
                temp_rack.remove(ch)
            elif ch != must_include:
                can_make = False
                break
        if can_make and (must_include is None or must_include in word):
            results.append((word, len(word)))
    return results

def can_place(board, word, row, col, direction):
    board_size = len(board)
    word_len = len(word)
    
    # Check if word fits on board
    if direction == "H":
        if col + word_len > board_size:
            return False
    else:
        if row + word_len > board_size:
            return False
    
    # Check for conflicts with existing letters
    for i, ch in enumerate(word):
        r = row + (i if direction == "V" else 0)
        c = col + (i if direction == "H" else 0)
        if board[r][c] != "." and board[r][c] != ch:
            return False
    
    # Check adjacent tiles
    for i in range(-1, word_len + 1):
        if direction == "H":
            r, c = row, col + i
        else:
            r, c = row + i, col
        
        if 0 <= r < board_size and 0 <= c < board_size:
            if i == -1 or i == word_len:
                if board[r][c] != ".":
                    return False
    return True

def word_score(word):
    return sum(LETTER_SCORES.get(ch.lower(), 0) for ch in word)

def generate_moves(board, rack):
    results = []
    seen = set()
    anchors = find_anchor_squares(board)
    
    for r, c in anchors:
        anchor_letter = board[r][c] if board[r][c] != "." else None
        for word, _ in possible_words(rack, must_include=anchor_letter):
            for direction in ("H", "V"):
                for i, ch in enumerate(word):
                    row = r - (i if direction == "V" else 0)
                    col = c - (i if direction == "H" else 0)
                    if row < 0 or col < 0:
                        continue
                    if can_place(board, word, row, col, direction):
                        move_key = (word, row, col, direction)
                        if move_key not in seen:
                            score = word_score(word)
                            results.append((move_key, score))
                            seen.add(move_key)
    
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:10]

# Initialize session state
if "board" not in st.session_state:
    st.session_state.board = create_board()
    st.session_state.move_history = []
if "moves" not in st.session_state:
    st.session_state.moves = []

# UI Layout
st.title("Scrabble Helper 2")

# Board Display
st.subheader("Current Board")
st.table(st.session_state.board)

# Word Placement Form
with st.form("place_word_form"):
    word = st.text_input("Word to place").upper()
    row = st.number_input("Row", min_value=0, max_value=BOARD_SIZE-1, value=7)
    col = st.number_input("Column", min_value=0, max_value=BOARD_SIZE-1, value=7)
    direction = st.radio("Direction", ["H", "V"])
    if st.form_submit_button("Place Word") and word:
        prev_board = [r.copy() for r in st.session_state.board]
        st.session_state.board = place_word(st.session_state.board, word, row, col, direction)
        st.session_state.move_history.append((word, row, col, direction, prev_board))
        st.session_state.moves = []  # Clear previous moves when placing new word

# Undo Button
if st.button("Undo Last Move") and st.session_state.move_history:
    _, _, _, _, prev_board = st.session_state.move_history.pop()
    st.session_state.board = undo_word(prev_board)
    st.session_state.moves = []  # Clear previous moves when undoing
    st.rerun()

# Rack Input and Move Suggestion
rack_input = st.text_input("Enter your rack letters (e.g. AETRSUN)", "").upper()

if st.button("Suggest Moves") and rack_input and rack_input.isalpha():
    st.session_state.moves = generate_moves(st.session_state.board, rack_input)
    st.rerun()

# Display Suggested Moves
if st.session_state.moves:
    st.subheader("Top Suggested Moves")
    for i, ((word, r, c, d), score) in enumerate(st.session_state.moves, 1):
        st.write(f"{i}. {word} at ({r},{c}) {d} → {score} pts")
elif rack_input and not rack_input.isalpha():
    st.warning("Please enter only letters A-Z")