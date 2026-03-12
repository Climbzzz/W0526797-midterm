import random

# ---- CONFIG ----
GRID_SIZE = 10

ICON_HIDDEN = "░"      # unrevealed
ICON_PLAYER = "P"
ICON_CELL = "."        # revealed normal cell
ICON_FLAG = "F"        # revealed flag
ICON_MIMIC = "M"       # revealed mimic (player doesn't know until revealed)

# ---- GRID GENERATION ----
def random_tile():
    chance = random.random()
    if chance < 0.1:
        return "flag"
    elif chance < 0.15:
        return "mimic"
    else:
        return "cell"

grid = [[random_tile() for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
revealed = [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

numbers = {}  # gives each tile a number when revealed

player_pos = [0, 0]
inventory = []

# ---- FUNCTIONS ----

def generate_number(tile_type):
    """Assign numbers based on tile type."""
    if tile_type == "cell":
        return random.randint(1, 9)
    if tile_type == "flag":
        return random.randint(5, 15)
    if tile_type == "mimic":
        return random.randint(0, 9)

def show_grid():
    for r in range(GRID_SIZE):
        row = ""
        for c in range(GRID_SIZE):
            if [r, c] == player_pos:
                row += ICON_PLAYER + " "
            else:
                if not revealed[r][c]:
                    row += ICON_HIDDEN + " "
                else:
                    t = grid[r][c]
                    if t == "cell": row += ICON_CELL + " "
                    if t == "flag": row += ICON_FLAG + " "
                    if t == "mimic": row += ICON_MIMIC + " "
        print(row)
    print()

def move(dir):
    r, c = player_pos
    if dir == "w" and r > 0: player_pos[0] -= 1
    if dir == "s" and r < GRID_SIZE - 1: player_pos[0] += 1
    if dir == "a" and c > 0: player_pos[1] -= 1
    if dir == "d" and c < GRID_SIZE - 1: player_pos[1] += 1

def reveal_tile():
    r, c = player_pos
    t = grid[r][c]

    if not revealed[r][c]:
        revealed[r][c] = True
        numbers[(r, c)] = generate_number(t)

    # flag pickup
    if t == "flag" and numbers[(r, c)] not in inventory:
        if len(inventory) < 2:
            inventory.append(numbers[(r, c)])
            print("Picked up flag number:", numbers[(r, c)])
        else:
            print("Inventory full.")

    # mimic behavior (NO announcement)
    if t == "mimic" and inventory:
        print("You feel a strange effect nearby...")
        idx = int(input("Choose inventory slot to change (0 or 1): "))
        new_num = int(input("Enter new number: "))
        inventory[idx] = new_num
        print("Inventory updated:", inventory)

    print("Tile number:", numbers[(r, c)])

# ---- GAME LOOP ----

print("Controls: w/a/s/d to move, e to reveal, q to quit\n")

show_grid()

while True:
    cmd = input("> ")

    if cmd == "q":
        break
    elif cmd in ("w", "a", "s", "d"):
        move(cmd)
    elif cmd == "e":
        reveal_tile()

    show_grid()
    print("Inventory:", inventory)

print("Game Over.")