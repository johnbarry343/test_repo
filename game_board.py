from typing import List, Optional # Add Block if type hint for 'Block' is needed and not just forward ref.
# from block import Block # Assuming Block is available in the context where GameBoard is used.

BOARD_WIDTH = 10
BOARD_HEIGHT = 20

class GameBoard:
    """
    Manages the game board, including block placement, collision detection, and line clearing.

    Attributes:
        width (int): The width of the game board in cells.
        height (int): The height of the game board in cells.
        grid (List[List[int]]): A 2D list representing the board.
                                 0 for empty, 1 for landed block,
                                 2 for the currently falling block (used in display logic).
    """
    def __init__(self, width: int = BOARD_WIDTH, height: int = BOARD_HEIGHT):
        """
        Initializes the GameBoard.

        Args:
            width (int): Width of the board. Defaults to BOARD_WIDTH.
            height (int): Height of the board. Defaults to BOARD_HEIGHT.
        """
        self.width = width
        self.height = height
        # Grid: 0 = empty, 1 = landed block cell
        self.grid: List[List[int]] = [[0 for _ in range(self.width)] for _ in range(self.height)]

    def add_block_to_grid(self, block: 'Block') -> None:
        """
        Adds a block's cells permanently to the grid when it lands.

        Args:
            block (Block): The block (e.g., an instance of the Block class) to add.
        """
        for r_idx, row in enumerate(block.shape):
            for c_idx, cell in enumerate(row):
                if cell != 0: # If it's part of the block's shape
                    board_x = block.x + c_idx
                    board_y = block.y + r_idx
                    if 0 <= board_y < self.height and 0 <= board_x < self.width:
                        self.grid[board_y][board_x] = 1 # Mark cell as a landed block part
                    # else:
                        # This case should ideally be prevented by prior collision checks.
                        # Consider logging a warning if this occurs.
                        # print(f"Warning: Attempted to add block part out of bounds at ({board_x},{board_y})")

    def is_collision(self, block: 'Block', x: int, y: int) -> bool:
        """
        Checks if placing a block at the given (x, y) coordinates would cause a collision
        with board boundaries or other landed blocks.

        Args:
            block (Block): The block to check.
            x (int): The potential x-coordinate of the block's top-left on the board.
            y (int): The potential y-coordinate of the block's top-left on the board.

        Returns:
            bool: True if a collision is detected, False otherwise.
        """
        for r_idx, row in enumerate(block.shape):
            for c_idx, cell in enumerate(row):
                if cell != 0:
                    board_x = x + c_idx
                    board_y = y + r_idx

                    # Check collision with left or right walls
                    if not (0 <= board_x < self.width):
                        return True
                    # Check collision with bottom wall
                    # (Blocks spawn from top, so top wall collision isn't checked for initial fall)
                    if board_y >= self.height:
                        return True

                    # Check collision with other landed blocks on the grid
                    # Only if the block part is within the board's vertical bounds (board_y >= 0)
                    if board_y >= 0 and self.grid[board_y][board_x] != 0:
                        return True
        return False # No collision detected

    def clear_lines(self) -> int:
        """
        Checks for and removes any completed lines from the board.
        Shifts down the lines above any cleared lines.

        Returns:
            int: The number of lines cleared.
        """
        lines_cleared = 0
        # Create a new grid, initially empty. Store non-cleared lines here.
        new_grid: List[List[int]] = []

        # Iterate from the bottom of the board upwards
        for r_idx in range(self.height - 1, -1, -1):
            is_line_full = True
            for c_idx in range(self.width):
                if self.grid[r_idx][c_idx] == 0: # If any cell in the row is empty
                    is_line_full = False
                    break

            if is_line_full:
                lines_cleared += 1
                # Don't add this full line to new_grid, effectively removing it.
            else:
                # If the line is not full, add it to the *top* of our new_grid list.
                # This preserves its content and relative order of non-full lines.
                new_grid.insert(0, list(self.grid[r_idx])) # Use list() for a copy.

        # If lines were cleared, the new_grid will be shorter than the board height.
        # Add new empty lines at the top to fill the space.
        if lines_cleared > 0:
            for _ in range(lines_cleared):
                new_grid.insert(0, [0 for _ in range(self.width)])
            self.grid = new_grid # Update the board's grid
        # If no lines were cleared, new_grid should be identical to the original grid,
        # so no update to self.grid is strictly necessary unless new_grid was built differently.
        # The current logic correctly rebuilds new_grid even if no lines are cleared.

        return lines_cleared

    def get_display_output_string(self, current_block: Optional['Block'],
                                  next_block_shape: List[List[int]],
                                  score: int, lines_cleared: int,
                                  speed_delay: float, slow_fall_status: dict) -> str:
        """
        Constructs a multi-line string representation of the entire game UI,
        including the game board, current falling block, next block preview, and game stats.

        Args:
            current_block (Optional[Block]): The currently falling block, or None.
            next_block_shape (List[List[int]]): The shape matrix of the next block.
            score (int): Current player score.
            lines_cleared (int): Total lines cleared by the player.
            speed_delay (float): Current fall delay (game speed).
            slow_fall_status (dict): Dictionary with keys 'charges', 'active', 'remaining',
                                     'progress', 'threshold' for the slow fall power-up.

        Returns:
            str: A multi-line string suitable for printing to the console.
        """
        # Character choices for display
        EMPTY_CELL = ' . '
        LANDED_BLOCK_CELL = '[▣]'
        FALLING_BLOCK_CELL = '[■]'
        NEXT_BLOCK_CELL = '▣' # Simpler char for next block, will be padded by spaces

        # Create a temporary display grid by copying the current board state
        # Grid cell values for display: 0=empty, 1=landed, 2=falling
        display_grid: List[List[int]] = [row[:] for row in self.grid]

        # Overlay the currently falling block onto this temporary display_grid
        if current_block:
            for r_idx, row in enumerate(current_block.shape):
                for c_idx, cell in enumerate(row):
                    if cell != 0:
                        board_x = current_block.x + c_idx
                        board_y = current_block.y + r_idx
                        if 0 <= board_y < self.height and 0 <= board_x < self.width:
                            display_grid[board_y][board_x] = 2 # Mark as falling block cell

        output_lines: List[str] = []
        board_render_width = self.width * len(EMPTY_CELL)

        # Prepare Next Block panel
        next_block_title = "Next Block"
        preview_cells_width = 4  # Max width for preview (e.g., I-shape)
        preview_cells_height = 4 # Max height for preview
        # Content width of preview in characters (each cell is 3 chars wide like EMPTY_CELL)
        preview_content_width_chars = preview_cells_width * len(EMPTY_CELL.strip()) # Use stripped width for content part

        # Centering the title text over the preview content area
        title_width_chars = len(next_block_title)
        title_padding_total = preview_content_width_chars - title_width_chars
        title_padding_left = title_padding_total // 2
        title_padding_right = title_padding_total - title_padding_left

        # Header line with board title (implicit) and Next Block panel title
        header = (f"╔{'═' * board_render_width}╗"
                  f" {'╔'}{'═' * title_padding_left}{next_block_title}{'═' * title_padding_right}{'╗'}")
        output_lines.append(header)

        # Board rows and Next Block preview area
        for r in range(self.height):
            # Start building the line for the current board row
            line_str = "║"
            for cell_val in display_grid[r]:
                if cell_val == 0: line_str += EMPTY_CELL
                elif cell_val == 2: line_str += FALLING_BLOCK_CELL
                else: line_str += LANDED_BLOCK_CELL
            line_str += "║"

            # Append Next Block Display Area alongside board rows
            if r == 0: # Top border of the content area for next block
                line_str += f" {'║'}{' ' * preview_content_width_chars}{'║'}"
            elif 1 <= r <= preview_cells_height: # Rows for the block shape itself
                shape_row_idx = r - 1
                preview_row_str = ""
                if next_block_shape and shape_row_idx < len(next_block_shape):
                    current_shape_row_data = next_block_shape[shape_row_idx]
                    for cell_idx in range(preview_cells_width):
                        if cell_idx < len(current_shape_row_data) and current_shape_row_data[cell_idx]:
                            preview_row_str += f" {NEXT_BLOCK_CELL} " # Pad char for consistency
                        else:
                            preview_row_str += EMPTY_CELL # Use EMPTY_CELL for spacing
                else: # If shape is shorter or no shape, print empty rows within preview box
                    preview_row_str = EMPTY_CELL * preview_cells_width
                line_str += f" {'║'}{preview_row_str}{'║'}"
            elif r == preview_cells_height + 1: # Bottom border of the content area
                line_str += f" {'╚'}{'═' * preview_content_width_chars}{'╝'}"
            else: # For other board rows where preview box is not drawn, add spacing
                # Calculate width of the next block panel including its borders
                next_block_panel_total_width = preview_content_width_chars + 4 # +2 for content borders, +2 for outer space and borders
                line_str += ' ' * next_block_panel_total_width
            output_lines.append(line_str)

        board_footer = f"╚{'═' * board_render_width}╝"
        next_block_panel_total_width = preview_content_width_chars + 4
        output_lines.append(board_footer + ' ' * next_block_panel_total_width) # Align footer with board

        # Info Panel - Spanning total width
        total_ui_width = board_render_width + 2 + 1 + next_block_panel_total_width # board_borders + space + panel_total_width
        info_separator = "═" * total_ui_width

        output_lines.append(info_separator)
        score_line = f"Score: {score:<10} Lines: {lines_cleared:<5} Speed: {speed_delay:.3f}s"
        output_lines.append(f"║ {score_line:<{total_ui_width-4}} ║")

        sf = slow_fall_status
        sf_line = (f"Slow Fall: Charges: {sf['charges']}, Active: {'Yes' if sf['active'] else 'No'} "
                   f"({sf['remaining']:.1f}s), Recharge: {sf['progress']}/{sf['threshold']}")
        output_lines.append(f"║ {sf_line:<{total_ui_width-4}} ║")
        output_lines.append(info_separator)

        return "\n".join(output_lines)

    def display(self, current_block=None):
        """(Deprecated) Simple console print of the grid, primarily for debugging.
        In a Pyodide environment, direct print() might go to browser console if not redirected.
        For web UI, get_display_output_string() should be used.
        """
        # Content removed as it's not used for web UI and print() is discouraged in Pyodide modules
        # If debugging is needed, one could use js.console.log here after importing js.
        pass
