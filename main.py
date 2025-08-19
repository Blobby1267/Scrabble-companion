import streamlit as st
from collections import defaultdict

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
        return {"hello", "world", "scrabble", "python", "game", "play", "word", "test", "serial", "aerial", "cat", "at", "act", "car", "art", "rat", "tar"}

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

# Find all valid anchor points (positions adjacent to existing tiles)
def find_anchor_points(board):
    anchors = set()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c].isalpha():
                for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and 
                        not board[nr][nc].isalpha()):
                        anchors.add((nr, nc))
    return anchors

# Find all possible cross words for a given position
def find_cross_words(board, row, col, direction):
    cross_words = []
    cross_direction = "V" if direction == "H" else "H"
    
    # Find the start of the cross word
    start_r, start_c = row, col
    if cross_direction == "H":
        while start_c > 0 and (board[start_r][start_c-1].isalpha() or (start_r == row and start_c-1 == col)):
            start_c -= 1
    else:
        while start_r > 0 and (board[start_r-1][start_c].isalpha() or (start_r-1 == row and start_c == col)):
            start_r -= 1
    
    # Build the cross word
    cross_word = ""
    cross_r, cross_c = start_r, start_c
    while (cross_r < BOARD_SIZE and cross_c < BOARD_SIZE and 
           (board[cross_r][cross_c].isalpha() or (cross_r == row and cross_c == col))):
        if cross_r == row and cross_c == col:
            cross_word += "?"  # Placeholder for the new letter
        else:
            cross_word += board[cross_r][cross_c]
        
        if cross_direction == "H":
            cross_c += 1
        else:
            cross_r += 1
    
    # Only add if it's a valid word (more than one letter)
    if len(cross_word) > 1:
        cross_words.append((cross_word, start_r, start_c, cross_direction))
    
    return cross_words

# Calculate score for a word placement
def calculate_score(board, word, row, col, direction):
    total_score = 0
    word_multiplier = 1
    word = word.upper()
    
    # Calculate score for the main word
    for i, letter in enumerate(word):
        r = row + (i if direction == "V" else 0)
        c = col + (i if direction == "H" else 0)
        
        # Get base letter score
        letter_score = LETTER_SCORES.get(letter.lower(), 0)
        
        # Check if this position has a bonus tile
        bonus = BONUS_TILES.get((r, c), None)
        
        # Apply bonus if the tile was just placed (not already on board)
        if not board[r][c].isalpha() and bonus:
            if bonus == "DL":
                letter_score *= 2
            elif bonus == "TL":
                letter_score *= 3
            elif bonus == "DW":
                word_multiplier *= 2
            elif bonus == "TW":
                word_multiplier *= 3
        
        total_score += letter_score
    
    total_score *= word_multiplier
    
    # Calculate score for cross words
    for i, letter in enumerate(word):
        r = row + (i if direction == "V" else 0)
        c = col + (i if direction == "H" else 0)
        
        # Skip if this position already had a letter
        if board[r][c].isalpha():
            continue
        
        # Find cross words
        cross_words = find_cross_words(board, r, c, direction)
        for cross_word, cross_r, cross_c, cross_d in cross_words:
            # Replace placeholder with actual letter
            cross_word = cross_word.replace("?", letter)
            
            # Calculate score for cross word
            cross_score = 0
            cross_word_multiplier = 1
            
            for j, cross_letter in enumerate(cross_word):
                cr = cross_r + (j if cross_d == "V" else 0)
                cc = cross_c + (j if cross_d == "H" else 0)
                
                # Get base letter score
                cross_letter_score = LETTER_SCORES.get(cross_letter.lower(), 0)
                
                # Check if this position has a bonus tile
                cross_bonus = BONUS_TILES.get((cr, cc), None)
                
                # Apply bonus if the tile was just placed
                if not board[cr][cc].isalpha() and cross_bonus:
                    if cross_bonus == "DL":
                        cross_letter_score *= 2
                    elif cross_bonus == "TL":
                        cross_letter_score *= 3
                    elif cross_bonus == "DW":
                        cross_word_multiplier *= 2
                    elif cross_bonus == "TW":
                        cross_word_multiplier *= 3
                
                cross_score += cross_letter_score
            
            cross_score *= cross_word_multiplier
            total_score += cross_score
    
    return total_score

# Find all valid moves
def find_moves(board, rack_letters):
    rack = rack_letters.upper()
    moves = []
    
    # If board is empty, only allow placements through center
    is_empty = not any(any(cell.isalpha() for cell in row) for row in board)
    if is_empty:
        center = BOARD_SIZE // 2
        for word in WORDS:
            if len(word) > len(rack):
                continue
                
            # Check if we can form this word with our rack
            temp_rack = list(rack)
            needed_letters = []
            
            for letter in word.upper():
                if letter in temp_rack:
                    temp_rack.remove(letter)
                else:
                    needed_letters.append(letter)
            
            if len(needed_letters) > 0:
                continue
                
            # Try both directions through center
            for direction in ["H", "V"]:
                if direction == "H":
                    for offset in range(len(word)):
                        row = center
                        col = center - offset
                        if col >= 0 and col + len(word) <= BOARD_SIZE:
                            score = calculate_score(board, word, row, col, direction)
                            moves.append((word, row, col, direction, score))
                else:
                    for offset in range(len(word)):
                        row = center - offset
                        col = center
                        if row >= 0 and row + len(word) <= BOARD_SIZE:
                            score = calculate_score(board, word, row, col, direction)
                            moves.append((word, row, col, direction, score))
    else:
        # Find all anchor points (positions adjacent to existing tiles)
        anchors = find_anchor_points(board)
        
        # Try all words that can be formed with the rack
        for word in WORDS:
            if len(word) > len(rack) + 7:  # Allow for using up to 7 existing letters
                continue
                
            # Check if we can form this word with our rack
            temp_rack = list(rack)
            needed_letters = []
            
            for letter in word.upper():
                if letter in temp_rack:
                    temp_rack.remove(letter)
                else:
                    needed_letters.append(letter)
            
            if len(needed_letters) > 0:
                continue
                
            # Try all anchor points and directions
            for (row, col) in anchors:
                for direction in ["H", "V"]:
                    # Check if the word fits on the board
                    if direction == "H" and col + len(word) > BOARD_SIZE:
                        continue
                    if direction == "V" and row + len(word) > BOARD_SIZE:
                        continue
                    
                    # Check if the word can be placed here
                    valid = True
                    uses_existing = False
                    
                    for i, letter in enumerate(word.upper()):
                        r = row + (i if direction == "V" else 0)
                        c = col + (i if direction == "H" else 0)
                        
                        # Check bounds
                        if r < 0 or r >= BOARD_SIZE or c < 0 or c >= BOARD_SIZE:
                            valid = False
                            break
                        
                        # Check if position is already occupied with a different letter
                        if board[r][c].isalpha():
                            if board[r][c] != letter:
                                valid = False
                                break
                            uses_existing = True
                    
                    # Word must use at least one existing tile
                    if not uses_existing:
                        valid = False
                    
                    if valid:
                        score = calculate_score(board, word, row, col, direction)
                        moves.append((word, row, col, direction, score))
    
    # Deduplicate and sort by score
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
        row = int(st.number_input("Row", 0, BOARD_SIZE-1, 7))
        col = int(st.number_input("Column", 0, BOARD_SIZE-1, 7))
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
    elif st.session_state.rack and not st.session_state.moves:
        st.warning("No valid moves found with these letters")

if __name__ == "__main__":
    main()