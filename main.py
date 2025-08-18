import streamlit as st
import os

# Constants
BOARD_SIZE = 15
LETTER_SCORES = {
    'a': 1, 'b': 3, 'c': 3, 'd': 2, 'e': 1, 'f': 4, 'g': 2, 'h': 4,
    'i': 1, 'j': 8, 'k': 5, 'l': 1, 'm': 3, 'n': 1, 'o': 1, 'p': 3,
    'q': 10, 'r': 1, 's': 1, 't': 1, 'u': 1, 'v': 4, 'w': 4, 'x': 8,
    'y': 4, 'z': 10
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

# Word validation
def load_words():
    try:
        with open("Oxford5000.txt", "r") as f:
            return set(word.strip().lower() for word in f if word.strip())
    except:
        return {"hello", "world", "scrabble", "python", "game", "play"}

WORDS = load_words()

# Game functions
def place_word(board, word, row, col, direction):
    new_board = [row.copy() for row in board]
    word = word.upper()
    for i, letter in enumerate(word):
        r = row + (i if direction == "V" else 0)
        c = col + (i if direction == "H" else 0)
        new_board[r][c] = letter
    return new_board

def calculate_score(word):
    return sum(LETTER_SCORES.get(letter.lower(), 0) for letter in word)

def find_moves(board, rack_letters):
    rack = rack_letters.upper()
    moves = []
    
    # Find all empty spots adjacent to existing letters
    anchors = set()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != '.':
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == '.':
                        anchors.add((nr, nc))
    
    if not anchors:
        anchors.add((BOARD_SIZE//2, BOARD_SIZE//2))
    
    # Generate possible moves
    for r, c in anchors:
        for direction in ["H", "V"]:
            for word in WORDS:
                word = word.upper()
                if len(word) > 7:  # Skip very long words for performance
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
                    # Try placing at different positions
                    for offset in range(len(word)):
                        if direction == "H":
                            start_col = c - offset
                            start_row = r
                        else:
                            start_row = r - offset
                            start_col = c
                        
                        if start_row < 0 or start_col < 0:
                            continue
                            
                        if direction == "H" and start_col + len(word) > BOARD_SIZE:
                            continue
                        if direction == "V" and start_row + len(word) > BOARD_SIZE:
                            continue
                            
                        # Check if placement is valid
                        valid_placement = True
                        for i, letter in enumerate(word):
                            pos_r = start_row + (i if direction == "V" else 0)
                            pos_c = start_col + (i if direction == "H" else 0)
                            
                            if board[pos_r][pos_c] != '.' and board[pos_r][pos_c] != letter:
                                valid_placement = False
                                break
                                
                        if valid_placement:
                            score = calculate_score(word)
                            moves.append((word, start_row, start_col, direction, score))
    
    # Remove duplicates and sort by score
    unique_moves = []
    seen = set()
    for move in sorted(moves, key=lambda x: -x[4]):
        key = (move[0], move[1], move[2], move[3])
        if key not in seen:
            seen.add(key)
            unique_moves.append(move)
    
    return unique_moves[:10]  # Return top 10 moves

# Streamlit UI
def main():
    st.title("Scrabble Helper")
    init_session()
    
    # Display board
    st.subheader("Game Board")
    st.table(st.session_state.board)
    
    # Word placement
    with st.form("place_form"):
        word = st.text_input("Word to place", "").upper()
        row = st.number_input("Row", 0, BOARD_SIZE-1, 7)
        col = st.number_input("Column", 0, BOARD_SIZE-1, 7)
        direction = st.radio("Direction", ["H", "V"])
        if st.form_submit_button("Place Word") and word:
            new_board = place_word(st.session_state.board, word, row, col, direction)
            st.session_state.history.append(st.session_state.board)
            st.session_state.board = new_board
            st.session_state.moves = []  # Clear previous moves
            st.rerun()
    
    # Undo button
    if st.button("Undo") and st.session_state.history:
        st.session_state.board = st.session_state.history.pop()
        st.session_state.moves = []  # Clear moves after undo
        st.rerun()
    
    # Rack input and move suggestion
    st.subheader("Your Rack")
    rack_input = st.text_input("Enter your letters (e.g. AETRSUN)", st.session_state.rack).upper()
    st.session_state.rack = rack_input
    
    if st.button("Suggest Moves"):
        if st.session_state.rack and st.session_state.rack.isalpha():
            st.session_state.moves = find_moves(st.session_state.board, st.session_state.rack)
            st.rerun()
        else:
            st.warning("Please enter valid letters (A-Z)")
    
    # Display suggested moves
    if st.session_state.moves:
        st.subheader("Suggested Moves")
        for i, (word, row, col, direction, score) in enumerate(st.session_state.moves, 1):
            st.write(f"{i}. {word} at ({row},{col}) {direction} → {score} pts")

if __name__ == "__main__":
    main()