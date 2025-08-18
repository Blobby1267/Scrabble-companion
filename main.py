from english_words import get_english_words_set
import streamlit as st


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

def create_board():
    return [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

def print_board(board):
    # Column headers
    header = "   " + " ".join(f"{i:2}" for i in range(BOARD_SIZE))
    print(header)
    for i, row in enumerate(board):
        row_str = " ".join(f"{ch:2}" for ch in row)
        print(f"{i:2} {row_str}")

def place_word(board, word, row, col, direction):
    word = word.upper()
    for i, ch in enumerate(word):
        r = row + i if direction.upper() == "V" else row
        c = col + i if direction.upper() == "H" else col
        board[r][c] = ch
    print(f"Placed {word} at ({row},{col}) {direction.upper()}")
    print_board(board)

def undo_word(board, word, row, col, direction, previous_board):
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            board[r][c] = previous_board[r][c]

def find_anchor_squares(board):
    anchors = set()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != ".":
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    rr, cc = r+dr, c+dc
                    if 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE and board[rr][cc] == ".":
                        anchors.add((rr,cc))
    if not anchors:
        anchors.add((BOARD_SIZE//2, BOARD_SIZE//2))
    return anchors

def possible_words(rack, must_include=None):
    rack = rack.upper()
    results = []
    english_words_set = get_english_words_set(['web2'], lower=True)
    for word in english_words_set:
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

def fits_on_board(word, row, col, direction):
    if direction.upper() == "H":
        return col + len(word) <= BOARD_SIZE
    else:
        return row + len(word) <= BOARD_SIZE

def can_place(board, word, row, col, direction):
    board_size = len(board)
    word_len = len(word)
    
    for i, ch in enumerate(word):
        r = row + i if direction.upper() == "V" else row
        c = col + i if direction.upper() == "H" else col
        
        # Check if the cell conflicts with existing letters
        if board[r][c] != "." and board[r][c] != ch:
            return False
    
    # Check the cell before the word
    before_r = row - 1 if direction.upper() == "V" else row
    before_c = col - 1 if direction.upper() == "H" else col
    if 0 <= before_r < board_size and 0 <= before_c < board_size:
        if board[before_r][before_c] != ".":
            return False
    
    # Check the cell after the word
    after_r = row + word_len if direction.upper() == "V" else row
    after_c = col + word_len if direction.upper() == "H" else col
    if 0 <= after_r < board_size and 0 <= after_c < board_size:
        if board[after_r][after_c] != ".":
            return False
    
    return True


def word_score(word):
    word = word.lower()
    return sum(LETTER_SCORES.get(ch, 0) for ch in word)

def generate_moves(board, rack):
    results = []
    seen = set()
    anchors = find_anchor_squares(board)
    for r, c in anchors:
        anchor_letter = board[r][c] if board[r][c] != "." else None
        for word, _ in possible_words(rack, must_include=anchor_letter):
            for direction in ("H", "V"):
                for i, ch in enumerate(word):
                    row = r - i if direction == "V" else r
                    col = c - i if direction == "H" else c
                    if row < 0 or col < 0:
                        continue
                    if not fits_on_board(word, row, col, direction):
                        continue
                    if not can_place(board, word, row, col, direction):
                        continue
                    overlaps_anchor = False
                    for j, wch in enumerate(word):
                        rr = row + j if direction == "V" else row
                        cc = col + j if direction == "H" else col
                        if board[rr][cc] != ".":
                            overlaps_anchor = True
                    if overlaps_anchor or all(board[r][c] == "." for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)):
                        move_key = (word, row, col, direction)
                        if move_key not in seen:
                            score = word_score(word)
                            results.append((move_key, score))
                            seen.add(move_key)
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:10]

# --- Streamlit UI ---
st.title("Scrabble Helper")

if "board" not in st.session_state:
    st.session_state.board = create_board()
    st.session_state.move_history = []

# Display board
st.subheader("Current Board")
st.table(st.session_state.board)

# --- Input for placing words ---
with st.form("place_word_form"):
    word = st.text_input("Word to place (e.g. HELLO)")
    row = st.number_input("Row", min_value=0, max_value=BOARD_SIZE-1, value=7)
    col = st.number_input("Column", min_value=0, max_value=BOARD_SIZE-1, value=7)
    direction = st.radio("Direction", ["H", "V"])
    submitted = st.form_submit_button("Place Word")
    if submitted and word:
        prev_board = [r.copy() for r in st.session_state.board]
        st.session_state.board = place_word(st.session_state.board, word, row, col, direction)
        st.session_state.move_history.append((word.upper(), row, col, direction.upper(), prev_board))

# Undo move
if st.button("Undo Last Move"):
    if st.session_state.move_history:
        last_move = st.session_state.move_history.pop()
        _, _, _, _, prev_board = last_move
        st.session_state.board = undo_word(st.session_state.board, prev_board)

# Generate suggestions
st.subheader("Find Best Moves")
rack = st.text_input("Enter your rack letters (e.g. AETRSUN)")
if st.button("Suggest Moves") and rack:
    moves = generate_moves(st.session_state.board, rack)
    if moves:
        for (word, r, c, d), score in moves:
            st.write(f"{word} at ({r},{c}) {d} → {score} pts")
    else:
        st.write("No valid moves found.")