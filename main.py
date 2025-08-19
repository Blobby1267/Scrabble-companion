import streamlit as st

# Constants
BOARD_SIZE = 15
LETTER_SCORES = {
    'a': 1, 'b': 3, 'c': 3, 'd': 2, 'e': 1, 'f': 4, 'g': 2, 'h': 4,
    'i': 1, 'j': 8, 'k': 5, 'l': 1, 'm': 3, 'n': 1, 'o': 1, 'p': 3,
    'q': 10, 'r': 1, 's': 1, 't': 1, 'u': 1, 'v': 4, 'w': 4, 'x': 8,
    'y': 4, 'z': 10
}

# Bonus squares definition
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
        st.session_state.board = [['.' for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    if 'rack' not in st.session_state:
        st.session_state.rack = ""
    if 'moves' not in st.session_state:
        st.session_state.moves = []
    if 'history' not in st.session_state:
        st.session_state.history = []

# Word dictionary
def load_words():
    try:
        with open("all_words.txt", "r") as f:
            return set(word.strip().lower() for word in f if word.strip())
    except:
        return {"hello", "world", "scrabble"}

WORDS = load_words()

# Create display board with bonus tiles and placed words
def get_display_board(board):
    display_board = [['.' for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    
    # Add bonus tiles
    for (r, c), bonus in BONUS_TILES.items():
        display_board[r][c] = bonus
    
    # Add placed words
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != '.':
                display_board[r][c] = board[r][c]
    
    return display_board

# Place a word on the board
def place_word(board, word, row, col, direction):
    new_board = [row.copy() for row in board]
    word = word.upper()
    for i, letter in enumerate(word):
        r = row + (i if direction == "V" else 0)
        c = col + (i if direction == "H" else 0)
        new_board[r][c] = letter
    return new_board

# Calculate score for a word placement
def calculate_score(board, word, row, col, direction):
    total_score = 0
    word_multiplier = 1
    word = word.upper()
    
    for i, letter in enumerate(word):
        r = row + (i if direction == "V" else 0)
        c = col + (i if direction == "H" else 0)
        
        # Get base letter score
        letter_score = LETTER_SCORES.get(letter.lower(), 0)
        
        # Check if this position has a bonus tile
        bonus = BONUS_TILES.get((r, c), None)
        
        # Apply bonus if the tile was just placed (not already on board)
        if board[r][c] == '.' and bonus:
            if bonus == "DL":
                letter_score *= 2
            elif bonus == "TL":
                letter_score *= 3
            elif bonus == "DW":
                word_multiplier *= 2
            elif bonus == "TW":
                word_multiplier *= 3
        
        total_score += letter_score
    
    return total_score * word_multiplier

# Find all valid moves
def find_moves(board, rack_letters):
    rack = rack_letters.upper()
    moves = []
    
    # Find all existing letters on the board
    existing_letters = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != '.':
                existing_letters.append((r, c, board[r][c]))
    
    # Generate possible moves that connect with existing letters
    for r, c, existing_letter in existing_letters:
        for word in WORDS:
            word = word.upper()

            # Skip words that don't contain the existing letter
            if existing_letter not in word:
                continue

            # Check if we can make this word with the rack and the existing letter
            temp_rack = list(rack)
            letter_counts = {letter: temp_rack.count(letter) for letter in set(temp_rack)}
            valid = True
            for i, letter in enumerate(word):
                if i == pos:  # <-- only skip the board-covered position
                    continue
                if letter_counts.get(letter, 0) > 0:
                    letter_counts[letter] -= 1
                else:
                    valid = False
                    break
            
            if not valid:
                continue

            # Find all positions where the existing letter appears in the word
            for pos in range(len(word)):
                if word[pos] == existing_letter:
                    # Try horizontal placement
                    start_col = c - pos
                    start_row = r
                    if start_col >= 0 and start_col + len(word) <= BOARD_SIZE:
                        valid_placement = True
                        for i, letter in enumerate(word):
                            pos_col = start_col + i
                            if board[start_row][pos_col] != '.':
                                if board[start_row][pos_col] != letter:
                                    valid_placement = False
                                    break
                        
                        if valid_placement:
                            score = calculate_score(board, word, start_row, start_col, "H")
                            moves.append((word, start_row, start_col, "H", score))
                    
                    # Try vertical placement
                    start_row = r - pos
                    start_col = c
                    if start_row >= 0 and start_row + len(word) <= BOARD_SIZE:
                        valid_placement = True
                        for i, letter in enumerate(word):
                            pos_row = start_row + i
                            if board[pos_row][start_col] != '.':
                                if board[pos_row][start_col] != letter:
                                    valid_placement = False
                                    break
                        
                        if valid_placement:
                            score = calculate_score(board, word, start_row, start_col, "V")
                            moves.append((word, start_row, start_col, "V", score))
    
    # Remove duplicates and sort by score
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
    
    # Display board with bonus tiles and placed words
    st.subheader("Game Board")
    display_board = get_display_board(st.session_state.board)
    st.table(display_board)
    
    # Word placement form
    with st.form("place_form"):
        word = st.text_input("Word to place", "").upper()
        row = st.number_input("Row", 0, BOARD_SIZE-1, 7)
        col = st.number_input("Column", 0, BOARD_SIZE-1, 7)
        direction = st.radio("Direction", ["H", "V"])
        submitted = st.form_submit_button("Place Word")
        
        if submitted and word:
            new_board = place_word(st.session_state.board, word, row, col, direction)
            st.session_state.history.append(st.session_state.board)
            st.session_state.board = new_board
            st.session_state.moves = []
    
    # Undo button
    if st.button("Undo") and st.session_state.history:
        st.session_state.board = st.session_state.history.pop()
        st.session_state.moves = []
    
    # Rack input
    st.subheader("Your Rack")
    rack_input = st.text_input("Enter your letters (e.g. AERIALS)", st.session_state.rack).upper()
    st.session_state.rack = rack_input
    
    # Suggest moves button
    if st.button("Suggest Moves"):
        if st.session_state.rack and st.session_state.rack.isalpha():
            st.session_state.moves = find_moves(st.session_state.board, st.session_state.rack)
        else:
            st.warning("Please enter valid letters (A-Z)")
    
    # Display suggested moves
    if st.session_state.moves:
        st.subheader("Suggested Moves")
        for i, (word, row, col, direction, score) in enumerate(st.session_state.moves, 1):
            st.write(f"{i}. {word} at ({row},{col}) {direction} → {score} pts")
    elif st.session_state.rack and not st.session_state.moves:
        st.warning("No valid moves found with these letters")

if __name__ == "__main__":
    main()