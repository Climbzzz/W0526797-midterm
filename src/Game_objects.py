# super basic prototype of the diagram logic

# ---- Data ----
grid = [
    ["cell", "flag", "cell"],
    ["cell", "mimic", "cell"],
    ["cell", "cell", "cell"]
]

player_pos = [0, 0]
inventory = []   # can only hold 2 numbers
revealed_numbers = {
    "cell": 3,
    "flag": 7,
    "mimic": 0
}

# ---- Helpers ----
def show_grid():
    for r in range(3):
        row = ""
        for c in range(3):
            if [r, c] == player_pos:
                row += "[P] "
            else:
                row += "[ ] "
        print(row)
    print()

def move(direction):
    r, c = player_pos
    if direction == "w" and r > 0: player_pos[0] -= 1
    elif direction == "s" and r < 2: player_pos[0] += 1
    elif direction == "a" and c > 0: player_pos[1] -= 1
    elif direction == "d" and c < 2: player_pos[1] += 1

def get_tile():
    r, c = player_pos
    return grid[r][c]

# ---- Game Loop ----
print("Simple Grid Demo (WASD to move, q to quit)")
show_grid()

while True:
    cmd = input("Move (w/a/s/d): ").lower()
    if cmd == "q":
        break

    move(cmd)
    tile = get_tile()

    print(f"You stepped on a {tile}!")

    # Step on flag → add to inventory (max 2)
    if tile == "flag":
        if len(inventory) < 2:
            inventory.append(revealed_numbers["flag"])
            print("Picked up a number! Inventory:", inventory)
        else:
            print("Inventory full (max 2).")

    # Step on mimic → change a number (only if you already revealed something)
    if tile == "mimic" and inventory:
        print("Mimic! You can change one number in your inventory.")
        print("Current inventory:", inventory)
        idx = int(input("Choose index to change (0 or 1): "))
        new_val = int(input("Enter new number: "))
        inventory[idx] = new_val
        print("Inventory updated:", inventory)

    # Look at number (cell or flag reveal)
    print("This tile's number is:", revealed_numbers[tile])
    show_grid()

print("Game ended.")