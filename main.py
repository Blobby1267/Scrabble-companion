import streamlit as st

# Constants
BOARD_SIZE = 15
LETTER_SCORES = {
    'a': 1, 'b': 3, 'c': 3, 'd': 2, 'e': 1, 'f': 4, 'g': 2, 'h': 4,
    'i': 1, 'j': 8, 'k': 5, 'l': 1, 'm': 3, 'n': 1, 'o': 1, 'p': 3,
    'q': 10, 'r': 1, 's': 1, 't': 1, 'u': 1, 'v': 4, 'w': 4, 'x': 8,
    'y': 4, 'z': 10
}

# Bonus squares definition (Scrabble layout simplified)
BONUS_TILES = {
    # Triple Word
    (0,0): "TW", (0,7): "TW", (0,14): "TW",
    (7,0): "TW", (7,14): "TW",
    (14,0): "TW", (14,7): "TW", (14,14): "TW",

    # Double Word
    (1,1): "DW", (2,2): "DW", (3,3): "DW", (4,4): "DW",
    (7,7): "*",  # center
    (10,10): "DW", (11,11): "DW", (12,12): "DW", (13,13): "DW",
    (1,13): "DW", (2,12): "DW", (3,11): "DW", (4,10): "DW",
    (10,4): "DW", (11,3): "DW", (12,2): "DW", (13,1): "DW",

    # Triple Letter
    (1,5): "TL", (1,9): "TL", (5,1): "TL", (5,5): "TL",
    (5,9): "TL", (5,13): "TL", (9,1): "TL", (9,5): "TL",
    (9,9): "TL", (9,13): "TL", (13,5): "TL", (13,9): "TL",

    # Double Letter
    (0,3): "DL", (0,11): "DL", (2,6): "DL", (2,8): "DL",
    (3,0): "DL", (3,7): "DL", (3,14): "DL", (6,2): "DL",
    (6,6): "DL", (6,8): "DL", (6,12): "DL", (7,3): "DL",
    (7,11): "DL", (8,2): "DL", (8,6): "DL", (8,8): "DL",
    (8,12): "DL", (11,0): "DL", (11,7): "DL", (11,14): "DL",
    (12,6): "DL", (12,8): "DL", (14,3): "DL", (14,11): "DL",
}

# Initialize session state
def init_session():
    if 'board' not in st.session_state:
        st.session_state.board = [
            [BONUS_TILES.get((r,c), '.') for c in range(BOARD_SIZE)]
            for r in range(BOARD_SIZE)
        ]
    if 'rack' not in st.session_state:
        st.session_state.rack = ""
    if 'moves' not in st.session_state:
        st.session_state.moves = []
    if 'history' not in st.session_state:
        st.session_state.history = []

# Word dictionary
def load_words():
    try:
        with open("Oxford5000.txt", "r") as f:
            return set(word.strip().lower() for word in f if word.strip())
    except:
        return {"hello", "world", "scrabble", "python", "game", "play", "word", "test", "serial", "aerial"}

WORDS = load_words()

# Place a word on the board
def place_word(board, word, row, col, direction):
    new_board = [r.copy() for r in board]
    word = word.upper()
    for i, letter in enumerate(word):
        r = row + (i if direction == "V" else 0)
        c = col + (i if direction == "H" else 0)
        if new_board[r][c] in ('.', 'TW', 'DW', 'TL', 'DL', '*'):
            new_board[r][c] = letter
    return new_board

# Score calculation with bonuses
def calculate_score(board, word, row, col, direction):
    word_multiplier = 1
    total = 0
    word = word.upper()
    for i, letter in enumerate(word):
        r = row + (i if direction == "V" else 0)
        c = col + (i if direction == "H" else 0)
        letter_score = LETTER_SCORES.get(letter.lower(), 0)

        if (r,c) in BONUS_TILES and board[r][c] in ('.','TW','DW','TL','DL','*'):
            bonus = BONUS_TILES[(r,c)]
            if bonus == "DL":
                letter_score *= 2
            elif bonus == "TL":
                letter_score *= 3
            elif bonus == "DW" or bonus == "*":
                word_multiplier *= 2
            elif bonus == "TW":
                word_multiplier *= 3

        total += letter_score

    return total * word_multiplier

# Simple move finder (bonus-aware scoring)
def find_moves(board, rack_letters):
    rack = rack_letters.upper()
    moves = []

    existing_letters = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c].isalpha():
                existing_letters.append((r, c, board[r][c]))

    center = BOARD_SIZE // 2

    if not existing_letters:
        for word in WORDS:
            word = word.upper()
            if len(word) > len(rack):
                continue
            temp_rack = list(rack)
            valid = True
            for letter in word:
                if letter in temp_rack:
                    temp_rack.remove(letter)
                else:
                    valid = False
                    break
            if valid:
                for direction in ["H", "V"]:
                    if direction == "H":
                        start_col = center - len(word) // 2
                        start_row = center
                        if start_col < 0 or start_col + len(word) > BOARD_SIZE:
                            continue
                    else:
                        start_row = center - len(word) // 2
                        start_col = center
                        if start_row < 0 or start_row + len(word) > BOARD_SIZE:
                            continue

                    score = calculate_score(board, word, start_row, start_col, direction)
                    moves.append((word, start_row, start_col, direction, score))
        return sorted(moves, key=lambda x: -x[4])[:10]

    for word in WORDS:
        word = word.upper()
        if len(word) > len(rack):
            continue
        temp_rack = list(rack)
        valid = True
        for letter in word:
            if letter in temp_rack:
                temp_rack.remove(letter)
            else:
                valid = False
                break
        if valid:
            for r, c, existing_letter in existing_letters:
                if existing_letter in word:
                    letter_index = word.index(existing_letter)
                    # Horizontal
                    start_col = c - letter_index
                    start_row = r
                    if start_col >= 0 and start_col + len(word) <= BOARD_SIZE:
                        valid_placement = True
                        for i, letter in enumerate(word):
                            pos_col = start_col + i
                            if board[start_row][pos_col].isalpha() and board[start_row][pos_col] != letter:
                                valid_placement = False
                                break
                        if valid_placement:
                            score = calculate_score(board, word, start_row, start_col, "H")
                            moves.append((word, start_row, start_col, "H", score))
                    # Vertical
                    start_row = r - letter_index
                    start_col = c
                    if start_row >= 0 and start_row + len(word) <= BOARD_SIZE:
                        valid_placement = True
                        for i, letter in enumerate(word):
                            pos_row = start_row + i
                            if board[pos_row][start_col].isalpha() and board[pos_row][start_col] != letter:
                                valid_placement = False
                                break
                        if valid_placement:
                            score = calculate_score(board, word, start_row, start_col, "V")
                            moves.append((word, start_row, start_col, "V", score))

    unique_moves = []
    seen = set()
    for move in sorted(moves, key=lambda x: -x[4]):
        key = (move[0], move[1], move[2], move[3])
        if key not in seen:
            seen.add(key)
            unique_moves.append(move)

    return unique_moves[:10]

# Streamlit UI
def main():
    st.title("Scrabble Companion")
    init_session()

    st.subheader("Game Board")
    st.table(st.session_state.board)

    with st.form("place_form"):
        word = st.text_input("Word to place", "").upper()
        row = int(st.number_input("Row", 0, BOARD_SIZE-1, 7, step=1, format="%d"))
        col = int(st.number_input("Column", 0, BOARD_SIZE-1, 7, step=1, format="%d"))
        direction = st.radio("Direction", ["H", "V"])
        submitted = st.form_submit_button("Place Word")
        if submitted and word:
            new_board = place_word(st.session_state.board, word, row, col, direction)
            st.session_state.history.append(st.session_state.board)
            st.session_state.board = new_board
            st.session_state.moves = []

    if st.button("Undo") and st.session_state.history:
        st.session_state.board = st.session_state.history.pop()
        st.session_state.moves = []

    st.subheader("Your Rack")
    rack_input = st.text_input("Enter your letters (e.g. AERIALS)", st.session_state.rack).upper()
    st.session_state.rack = rack_input

    if st.button("Suggest Moves"):
        if st.session_state.rack and st.session_state.rack.isalpha():
            st.session_state.moves = find_moves(st.session_state.board, st.session_state.rack)
        else:
            st.warning("Please enter valid letters (A-Z)")

    if st.session_state.moves:
        st.subheader("Suggested Moves")
        for i, (word, row, col, direction, score) in enumerate(st.session_state.moves, 1):
            st.write(f"{i}. {word} at ({row},{col}) {direction} → {score} pts")
    elif st.session_state.rack and not st.session_state.rack.isalpha():
        st.warning("Please enter only letters A-Z")

if __name__ == "__main__":
    main()
