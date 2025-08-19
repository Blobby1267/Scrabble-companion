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
        with open("Oxford5000.txt", "r") as f:
            return set(word.strip().lower() for word in f if word.strip())
    except:
        return {"hello", "world", "scrabble", "python", "game", "play", "word", "test", "serial", "aerial", "cat", "at", "act", "car", "art", "rat", "tar", "error", "terror"}

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

# Find cross words for a given position
def find_cross_words(board, word, row, col, direction):
    cross_words = []
    word = word.upper()
    
    for i, letter in enumerate(word):
        r = row + (i if direction == "V" else 0)
        c = col + (i if direction == "H" else 0)
        
        # Skip if this position already has a letter
        if board[r][c] != '.':
            continue
            
        # Check for cross words in perpendicular direction
        cross_direction = "V" if direction == "H" else "H"
        
        # Find the start of the cross word
        start_r, start_c = r, c
        if cross_direction == "H":
            while start_c > 0 and board[start_r][start_c-1] != '.':
                start_c -= 1
        else:
            while start_r > 0 and board[start_r-1][start_c] != '.':
                start_r -= 1
        
        # Build the cross word
        cross_word = ""
        cross_r, cross_c = start_r, start_c
        while (cross_r < BOARD_SIZE and cross_c < BOARD_SIZE and 
               (board[cross_r][cross_c] != '.' or (cross_r == r and cross_c == c))):
            if cross_r == r and cross_c == c:
                cross_word += letter
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

# Calculate score for a word placement including cross words
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
    
    total_score *= word_multiplier
    
    # Calculate score for cross words
    cross_words = find_cross_words(board, word, row, col, direction)
    for cross_word, cross_r, cross_c, cross_d in cross_words:
        cross_score = 0
        cross_word_multiplier = 1
        
        for i, cross_letter in enumerate(cross_word):
            r = cross_r + (i if cross_d == "V" else 0)
            c = cross_c + (i if cross_d == "H" else 0)
            
            # Get base letter score
            cross_letter_score = LETTER_SCORES.get(cross_letter.lower(), 0)
            
            # Check if this position has a bonus tile
            cross_bonus = BONUS_TILES.get((r, c), None)
            
            # Apply bonus if the tile was just placed
            if board[r][c] == '.' and cross_bonus:
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

# Check if a word can be placed at a given position
def can_place_word(board, word, row, col, direction, rack):
    word = word.upper()
    temp_rack = list(rack.upper())
    
    # Check if word fits on board
    if direction == "H" and col + len(word) > BOARD_SIZE:
        return False
    if direction == "V" and row + len(word) > BOARD_SIZE:
        return False
    
    # Check if word uses at least one existing letter or connects to existing words
    uses_existing = False
    connects_to_existing = False
    
    for i, letter in enumerate(word):
        r = row + (i if direction == "V" else 0)
        c = col + (i if direction == "H" else 0)
        
        # Check bounds
        if r < 0 or r >= BOARD_SIZE or c < 0 or c >= BOARD_SIZE:
            return False
        
        # Check if position is already occupied with a different letter
        if board[r][c] != '.':
            if board[r][c] != letter:
                return False
            uses_existing = True
        else:
            # Check if we have this letter in rack
            if letter in temp_rack:
                temp_rack.remove(letter)
            else:
                return False
        
        # Check if this placement connects to existing words
        if not connects_to_existing:
            # Check adjacent positions for existing letters
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    if board[nr][nc] != '.' and (nr != row or nc != col):
                        connects_to_existing = True
                        break
    
    # For first move, must use the center tile
    is_first_move = not any(any(cell != '.' for cell in row) for row in board)
    if is_first_move:
        center = BOARD_SIZE // 2
        for i in range(len(word)):
            r = row + (i if direction == "V" else 0)
            c = col + (i if direction == "H" else 0)
            if r == center and c == center:
                return True
        return False
    
    # For subsequent moves, must connect to existing words
    return uses_existing or connects_to_existing

# Validate all cross words are valid
def validate_cross_words(board, word, row, col, direction):
    cross_words = find_cross_words(board, word, row, col, direction)
    
    for cross_word, _, _, _ in cross_words:
        if cross_word.lower() not in WORDS:
            return False
    
    return True

# Find all valid moves
def find_moves(board, rack_letters):
    rack = rack_letters.upper()
    moves = []
    
    # If board is empty, only allow placements through center
    is_empty = not any(any(cell != '.' for cell in row) for row in board)
    if is_empty:
        center = BOARD_SIZE // 2
        for word in WORDS:
            word = word.upper()
            if len(word) > len(rack):
                continue
                
            # Check if we can make this word with our rack
            temp_rack = list(rack)
            valid = True
            for letter in word:
                if letter in temp_rack:
                    temp_rack.remove(letter)
                else:
                    valid = False
                    break
            
            if valid:
                # Try placing through center
                for direction in ["H", "V"]:
                    if direction == "H":
                        start_col = center - len(word) // 2
                        start_row = center
                        if start_col < 0:
                            continue
                    else:
                        start_row = center - len(word) // 2
                        start_col = center
                        if start_row < 0:
                            continue
                    
                    if (direction == "H" and start_col + len(word) > BOARD_SIZE) or \
                       (direction == "V" and start_row + len(word) > BOARD_SIZE):
                        continue
                        
                    score = calculate_score(board, word, start_row, start_col, direction)
                    moves.append((word, start_row, start_col, direction, score))
        return moves[:10]
    
    # Find all existing letters on board
    existing_letters = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != '.':
                existing_letters.append((r, c, board[r][c]))
    
    # Generate possible moves that connect with existing letters
    for word in WORDS:
        word = word.upper()
        if len(word) > len(rack) + 7:  # Allow for using up to 7 existing letters
            continue
            
        # Check if we can make this word with our rack
        temp_rack = list(rack)
        valid = True
        for letter in word:
            if letter in temp_rack:
                temp_rack.remove(letter)
            else:
                valid = False
                break
        
        if not valid:
            continue
            
        # Try placing the word by connecting to existing letters
        for r, c, existing_letter in existing_letters:
            if existing_letter in word:
                # Find all positions where this letter appears in the word
                for pos in range(len(word)):
                    if word[pos] == existing_letter:
                        # Try horizontal placement
                        start_col = c - pos
                        start_row = r
                        if start_col >= 0 and start_col + len(word) <= BOARD_SIZE:
                            # Check if we can place the word here
                            if can_place_word(board, word, start_row, start_col, "H", rack):
                                # Validate all cross words are valid
                                if validate_cross_words(board, word, start_row, start_col, "H"):
                                    score = calculate_score(board, word, start_row, start_col, "H")
                                    moves.append((word, start_row, start_col, "H", score))
                        
                        # Try vertical placement
                        start_row = r - pos
                        start_col = c
                        if start_row >= 0 and start_row + len(word) <= BOARD_SIZE:
                            # Check if we can place the word here
                            if can_place_word(board, word, start_row, start_col, "V", rack):
                                # Validate all cross words are valid
                                if validate_cross_words(board, word, start_row, start_col, "V"):
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