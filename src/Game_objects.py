import random
from collections import deque

# ----- CONFIG -----
GRID_SIZE    = 10
BOMBS_COUNT  = 15
MIMIC_COUNT  = 6            # non-bomb tiles that distort nearby-bomb numbers on reveal

ICON_HIDDEN  = "░"          # unrevealed
ICON_PLAYER  = "P"          # cursor
ICON_FLAG    = "F"          # flag on hidden cell
ICON_EMPTY   = "."          # revealed 0
ICON_BOMB    = "*"          # bomb
ICON_WRONG   = "x"          # wrong flag shown at game-over
ICON_MIMIC   = "M"          # revealed mimic tile

# ----- STATE -----
board = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]   # -1 = bomb, else 0..8
revealed = [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
flagged  = [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
mimic    = [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

# display-only offsets (mimic effect)
offset   = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

player_pos = [0, 0]
bombs_placed = False   # delay until first reveal so first click is safe
bomb_positions = set()
game_over = False
won = False
triggered_bomb = None  # (r, c) that the player exploded

# ----- HELPERS -----
def neighbors(r, c):
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr, cc = r + dr, c + dc
            if 0 <= rr < GRID_SIZE and 0 <= cc < GRID_SIZE:
                yield rr, cc

def place_bombs_and_mimics(safe_r, safe_c):
    """Place bombs excluding the initial safe tile; compute counts; place mimics on safe tiles."""
    global bombs_placed, bomb_positions
    spots = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)
             if not (r == safe_r and c == safe_c)]
    bomb_positions = set(random.sample(spots, BOMBS_COUNT))
    for r, c in bomb_positions:
        board[r][c] = -1
    # compute neighbor counts
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] == -1:
                continue
            board[r][c] = sum(1 for rr, cc in neighbors(r, c) if board[rr][cc] == -1)
    # place mimics (on non-bomb, not the first-click cell)
    safe_spots = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)
                  if board[r][c] != -1 and not (r == safe_r and c == safe_c)]
    for r, c in random.sample(safe_spots, min(MIMIC_COUNT, len(safe_spots))):
        mimic[r][c] = True
    bombs_placed = True

def reset():
    """Reset entire game state."""
    global board, revealed, flagged, mimic, offset
    global player_pos, bombs_placed, bomb_positions, game_over, won, triggered_bomb
    board = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    revealed = [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    flagged  = [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    mimic    = [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    offset   = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    player_pos = [0, 0]
    bombs_placed = False
    bomb_positions = set()
    game_over = False
    won = False
    triggered_bomb = None

def placed_flags_count():
    return sum(1 for r in range(GRID_SIZE) for c in range(GRID_SIZE) if flagged[r][c])

def bombs_remaining():
    return BOMBS_COUNT - placed_flags_count()

def header_bar():
    """Classic Minesweeper-style: bombs remaining = total - flags placed."""
    remain = bombs_remaining()
    # simple visual bar of 20 slots
    total_slots = 20
    filled = max(0, min(total_slots, total_slots * max(0, remain) // max(1, BOMBS_COUNT)))
    bar = "#" * filled + "-" * (total_slots - filled)
    print(f"Bombs remaining: [{bar}] {remain:+d}  (Total: {BOMBS_COUNT})")

def draw_cell_char(r, c, reveal_all=False):
    """Character to display for cell (r,c)."""
    if reveal_all:
        if (r, c) == triggered_bomb:
            return ICON_BOMB  # exploded one
        if board[r][c] == -1 and not flagged[r][c]:
            return ICON_BOMB
        if board[r][c] != -1 and flagged[r][c] and not revealed[r][c]:
            return ICON_WRONG  # wrong flag
    if revealed[r][c]:
        if board[r][c] == -1:
            return ICON_BOMB
        if mimic[r][c]:
            return ICON_MIMIC
        val = board[r][c] + offset[r][c]
        val = max(0, min(8, val))
        return ICON_EMPTY if val == 0 else str(val)
    else:
        return ICON_FLAG if flagged[r][c] else ICON_HIDDEN

def show_grid(reveal_all=False):
    header_bar()
    for r in range(GRID_SIZE):
        row = ""
        for c in range(GRID_SIZE):
            ch = draw_cell_char(r, c, reveal_all=reveal_all)
            row += (ICON_PLAYER if [r, c] == player_pos else ch) + " "
        print(row)
    print()

def move_player(cmd):
    r, c = player_pos
    if cmd == "w" and r > 0:             player_pos[0] -= 1
    elif cmd == "s" and r < GRID_SIZE-1: player_pos[0] += 1
    elif cmd == "a" and c > 0:           player_pos[1] -= 1
    elif cmd == "d" and c < GRID_SIZE-1: player_pos[1] += 1

def flood_reveal(sr, sc):
    """Reveal empty region (true board), and boundary numbers."""
    q = deque([(sr, sc)])
    while q:
        r, c = q.popleft()
        if revealed[r][c] or flagged[r][c]:
            continue
        revealed[r][c] = True
        if board[r][c] == 0 and not mimic[r][c]:
            for rr, cc in neighbors(r, c):
                if not revealed[rr][cc] and not flagged[rr][cc]:
                    q.append((rr, cc))

def check_win():
    """Win when all non-bomb cells are revealed."""
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] != -1 and not revealed[r][c]:
                return False
    return True

def apply_mimic_effect():
    """When a mimic is revealed, distort only numbers around ONE random bomb (±1 display-only)."""
    if not bomb_positions:
        return
    br, bc = random.choice(list(bomb_positions))
    for rr, cc in neighbors(br, bc):
        if board[rr][cc] == -1:
            continue
        offset[rr][cc] += random.choice([-1, 1])

def reveal_current():
    """Reveal current cell with full bomb logic."""
    global game_over, won, triggered_bomb
    r, c = player_pos
    if flagged[r][c] or revealed[r][c]:
        return
    if not bombs_placed:
        place_bombs_and_mimics(r, c)  # safe first click (no bomb under first reveal)
    if board[r][c] == -1:
        triggered_bomb = (r, c)
        game_over = True
        return
    if mimic[r][c]:
        revealed[r][c] = True
        apply_mimic_effect()
    else:
        if board[r][c] == 0:
            flood_reveal(r, c)
        else:
            revealed[r][c] = True
    if check_win():
        won = True
        game_over = True

def toggle_flag():
    """Place/unplace a flag on a hidden cell. Limit flags to total bombs."""
    r, c = player_pos
    if revealed[r][c]:
        return
    if flagged[r][c]:
        flagged[r][c] = False
    else:
        if placed_flags_count() < BOMBS_COUNT:
            flagged[r][c] = True
        # else: ignore if you've already placed as many flags as bombs

def end_screen():
    show_grid(reveal_all=True)
    if won:
        print("🎉 You cleared the board! (WIN)")
    else:
        print("💥 Boom! You hit a bomb. (GAME OVER)")
    print("Press R to restart or Q to quit.")

# ----- MAIN LOOP -----
def main():
    reset()
    print("Minesweeper 10x10 — bombs, flags, flood-reveal, and Mimics")
    print("Controls: W A S D move | E reveal | F flag | Q quit")
    print(f"Bombs: {BOMBS_COUNT} | Mimics: {MIMIC_COUNT}\n")
    show_grid()

    while True:
        cmd = input("> ").strip().lower()
        if not game_over:
            if cmd in ("w", "a", "s", "d"):
                move_player(cmd)
            elif cmd == "e":
                reveal_current()
            elif cmd == "f":
                toggle_flag()
            elif cmd == "q":
                print("Bye!")
                return
            else:
                print("Use W/A/S/D, E, F, Q.")
            show_grid()
            if game_over:
                end_screen()
        else:
            if cmd == "r":
                reset()
                print("\n--- Restarted ---\n")
                show_grid()
            elif cmd == "q":
                print("Bye!")
                return
            else:
                print("Press R to restart or Q to quit.")

if __name__ == "__main__":
    main()
``