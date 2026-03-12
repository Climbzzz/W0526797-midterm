from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Tuple


class Direction(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


class MenuOption(Enum):
    RESTART = auto()
    QUIT = auto()


@dataclass
class Cell:
    """Represents a single tile on the grid.

    Mapped from diagrams:
      - Can hold a flag (flag_interaction.png)
      - Can be revealed during game over to show bombs (final_board_reveal.png)
      - Has a number that can be previewed without revealing (tile_number_reveal.png)
    """

    x: int
    y: int
    has_bomb: bool = False
    number: int = 0  # Adjacent bomb count
    has_flag: bool = False
    revealed: bool = False

    def place_flag(self) -> bool:
        """Attempt to place a flag on this cell.
        Returns True if placed, False if already flagged.
        """
        if self.has_flag:
            return False
        self.has_flag = True
        return True

    def remove_flag(self) -> bool:
        """Attempt to remove a flag from this cell.
        Returns True if removed, False if no flag to remove.
        """
        if not self.has_flag:
            return False
        self.has_flag = False
        return True

    def reveal(self) -> None:
        self.revealed = True

    def preview_number(self) -> int:
        """Return the number on this cell *without* revealing it.
        ("Look at number (no reveal)" in tile_number_reveal.png)
        """
        return self.number


class Inventory:
    """Holds the player's flags (capacity limited).

    From flag_interaction.png:
      - Capacity is 0..2
      - +1 flag when picking up from a cell
      - -1 flag when placing on a cell
    """

    MAX_FLAGS = 2

    def __init__(self, starting_flags: int = 0) -> None:
        self._flags = max(0, min(self.MAX_FLAGS, starting_flags))

    @property
    def flags(self) -> int:
        return self._flags

    def has_at_least(self, n: int) -> bool:
        return self._flags >= n

    def has_space(self) -> bool:
        return self._flags < self.MAX_FLAGS

    def add_flag(self) -> bool:
        if self._flags >= self.MAX_FLAGS:
            return False
        self._flags += 1
        return True

    def remove_flag(self) -> bool:
        if self._flags <= 0:
            return False
        self._flags -= 1
        return True


@dataclass
class Player:
    x: int
    y: int
    inventory: Inventory = field(default_factory=Inventory)

    def move(self, direction: Direction, grid_width: int, grid_height: int) -> Tuple[int, int]:
        """Move within bounds of the grid (WASD/Arrow equivalent)."""
        dx, dy = 0, 0
        if direction == Direction.UP:
            dy = -1
        elif direction == Direction.DOWN:
            dy = 1
        elif direction == Direction.LEFT:
            dx = -1
        elif direction == Direction.RIGHT:
            dx = 1

        new_x = max(0, min(grid_width - 1, self.x + dx))
        new_y = max(0, min(grid_height - 1, self.y + dy))
        self.x, self.y = new_x, new_y
        return self.x, self.y


class Grid:
    """The grid that holds all cells, bombs, and numbers."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells: List[List[Cell]] = [
            [Cell(x, y) for x in range(width)] for y in range(height)
        ]

    def get_cell(self, x: int, y: int) -> Cell:
        return self.cells[y][x]

    def get_tile_under_player(self, player: Player) -> Cell:
        return self.get_cell(player.x, player.y)

    def reveal_all_bombs(self) -> None:
        """Reveal all bombs on the grid (final_board_reveal.png)."""
        for row in self.cells:
            for c in row:
                if c.has_bomb:
                    c.reveal()

    def show_final_board_state(self) -> List[List[str]]:
        """Return a text visualization of the final board for UI to display."""
        board: List[List[str]] = []
        for row in self.cells:
            display_row: List[str] = []
            for c in row:
                if c.has_bomb and c.revealed:
                    display_row.append("*")
                elif c.has_flag:
                    display_row.append("F")
                elif c.revealed:
                    display_row.append(str(c.number))
                else:
                    display_row.append("·")
            board.append(display_row)
        return board

    def add_flag_to_inventory_if_present(self, player: Player) -> bool:
        """If the player steps on a flagged cell and has inventory space, pick it up.
        ("Walk over flag" -> "Add to inventory (max 2)" in tile_number_reveal.png)
        Returns True if a flag was collected.
        """
        cell = self.get_tile_under_player(player)
        if cell.has_flag and player.inventory.has_space():
            # Remove from cell, add to inventory
            cell.remove_flag()
            player.inventory.add_flag()
            return True
        return False

    def set_numbers_from_bombs(self) -> None:
        """Utility to compute numbers based on bombs (standard minesweeper rule)."""
        dirs = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
        for y in range(self.height):
            for x in range(self.width):
                c = self.get_cell(x, y)
                c.number = 0
                for dx, dy in dirs:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if self.get_cell(nx, ny).has_bomb:
                            c.number += 1


class Mimic:
    """A special rule element: can change one number only after reveals.

    Based on tile_number_reveal.png: "Change one number (only after reveals)".
    This class tracks whether the mimic power is unlocked and whether it has
    already been used.
    """

    def __init__(self) -> None:
        self.unlocked: bool = False
        self.used: bool = False

    def unlock(self) -> None:
        self.unlocked = True

    def change_one_number(self, grid: Grid, x: int, y: int, new_value: int) -> bool:
        """Attempt to change the number on a cell.
        Returns True if allowed and applied.
        Constraints:
          - Only after reveals (unlock must be True)
          - Only once overall (used must be False)
        """
        if not self.unlocked or self.used:
            return False
        if not (0 <= x < grid.width and 0 <= y < grid.height):
            return False
        cell = grid.get_cell(x, y)
        cell.number = max(0, new_value)
        self.used = True
        return True


class UI:
    """Very simple text-based UI placeholder.

    Real games should replace this with an actual UI system (e.g., pygame,
    Unity UI, Godot, etc.).
    """

    def show_final_board(self, grid: Grid) -> None:
        board = grid.show_final_board_state()
        print("\nFINAL BOARD:")
        for row in board:
            print(" ".join(row))

    def show_restart_quit(self) -> MenuOption:
        # Placeholder: always choose QUIT by default
        print("Options: [R]estart / [Q]uit")
        return MenuOption.QUIT

    def show_current_number(self, number: int) -> None:
        print(f"Current tile number (preview): {number}")


class GameManager:
    """Coordinates Player, Grid, UI, and special rules.

    This class wires together the behaviors shown in the four diagrams:
      - Movement + preview numbers + flag collection (tile_number_reveal.png)
      - Place/Pickup key logic with inventory constraints (flag_interaction.png)
      - Game over flow: reveal bombs -> show final board -> restart/quit (final_board_reveal.png)
    """

    def __init__(self, grid: Grid, player: Player, ui: Optional[UI] = None, mimic: Optional[Mimic] = None):
        self.grid = grid
        self.player = player
        self.ui = ui or UI()
        self.mimic = mimic or Mimic()
        self.game_over_state: bool = False

    # --- Movement & inspection (tile_number_reveal.png) ---
    def handle_move(self, direction: Direction) -> None:
        """Player movement + interactions triggered by stepping on a tile."""
        self.player.move(direction, self.grid.width, self.grid.height)

        # 1) Get tile under player
        current_cell = self.grid.get_tile_under_player(self.player)

        # 2) Walk over flag -> add to inventory (max 2)
        self.grid.add_flag_to_inventory_if_present(self.player)

        # 3) Look at number (no reveal) -> Show current number
        number = current_cell.preview_number()
        self.ui.show_current_number(number)

    # --- Place/Pickup key (flag_interaction.png) ---
    def handle_place_or_pickup_flag(self) -> None:
        cell = self.grid.get_tile_under_player(self.player)

        # alt 1: Cell has a flag -> Try pickup
        if cell.has_flag:
            if self.player.inventory.has_space():
                if cell.remove_flag():
                    self.player.inventory.add_flag()
                    # UI could indicate success here
                else:
                    # Cannot pick up (no flag ?) – safety
                    pass
            else:
                # Cannot pick up (inventory full)
                pass
            return

        # alt 2: Cell has no flag -> Try placing if player has at least one
        if not cell.has_flag:
            if self.player.inventory.has_at_least(1):
                if cell.place_flag():
                    self.player.inventory.remove_flag()
                else:
                    # Cannot place (already flagged) – safety
                    pass
            else:
                # Cannot place (no flags)
                pass

    # --- Game over sequence (final_board_reveal.png) ---
    def trigger_game_over(self) -> MenuOption:
        """Reveal bombs, show final board, then prompt for restart/quit."""
        self.game_over_state = True

        # Reveal all bombs
        self.grid.reveal_all_bombs()

        # Allow mimic power now ("only after reveals")
        self.mimic.unlock()

        # Show final board in the UI
        self.ui.show_final_board(self.grid)

        # Prompt for restart/quit
        choice = self.ui.show_restart_quit()
        return choice

    def apply_mimic_change(self, x: int, y: int, new_value: int) -> bool:
        """Convenience pass-through for the mimic rule."""
        return self.mimic.change_one_number(self.grid, x, y, new_value)


# --- Example usage (optional quick demo in console) ---
if __name__ == "__main__":
    # Small 5x3 board demo
    grid = Grid(5, 3)

    # Put a couple of bombs for demonstration and compute numbers
    grid.get_cell(1, 0).has_bomb = True
    grid.get_cell(3, 2).has_bomb = True
    grid.set_numbers_from_bombs()

    # Place a flag on (0,0)
    grid.get_cell(0, 0).place_flag()

    player = Player(0, 0, Inventory(starting_flags=0))
    gm = GameManager(grid, player)

    # Move right, preview number, pick up flag if any
    gm.handle_move(Direction.RIGHT)

    # Try to place/pickup on current tile
    gm.handle_place_or_pickup_flag()

    # Simulate game over
    choice = gm.trigger_game_over()
    print("Choice taken:", choice)

    # Try mimic change after reveals
    changed = gm.apply_mimic_change(2, 1, 5)
    print("Mimic change applied: ", changed)
