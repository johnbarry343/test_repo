import time
import random
import os
import sys

# --- Game Constants ---
INITIAL_FALL_DELAY: float = 0.7
MIN_FALL_DELAY: float = 0.1
SPEED_INCREASE_INTERVAL_LINES: int = 5
FALL_DELAY_DECREMENT: float = 0.05
ENABLE_SOUND_PLACEHOLDERS: bool = True


# --- Non-blocking Input Setup ---
_get_keypress_func = None
_orig_termios_settings = None # For select_keypress on Linux/macOS

# Try msvcrt for Windows non-blocking input
try:
    import msvcrt
    def _msvcrt_keypress():
        if msvcrt.kbhit():
            return msvcrt.getch().decode(errors='ignore').lower()
        return None
    _get_keypress_func = _msvcrt_keypress
except ImportError:
    # Try select for Linux/macOS non-blocking input
    try:
        import select
        import tty
        import termios

        def _set_raw_terminal():
            global _orig_termios_settings
            if sys.stdin.isatty(): # Only if input is a terminal
                _orig_termios_settings = termios.tcgetattr(sys.stdin)
                tty.setraw(sys.stdin.fileno())

        def _restore_terminal_settings():
            global _orig_termios_settings
            if _orig_termios_settings: # Only restore if settings were saved
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, _orig_termios_settings)
                _orig_termios_settings = None # Clear after restoring

        def _select_keypress():
            if sys.stdin.isatty() and sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1)
                if key:
                    return key.lower()
            return None
        _get_keypress_func = _select_keypress
    except ImportError:
        # Fallback message will be printed in main() if _get_keypress_func is still None
        pass

# --- Game Imports ---
from game_board import GameBoard, BOARD_WIDTH, BOARD_HEIGHT
from player import Player
from block import Block # Assuming Block class has SHAPES attribute
from typing import Dict, Any, Tuple, List, Optional


def initialize_game_state() -> Dict[str, Any]:
    """
    Creates and returns a dictionary containing the initial state for a new game.
    This ensures a fresh start for each game session.

    Returns:
        Dict[str, Any]: A dictionary holding all essential game state variables.
    """
    game_board = GameBoard()
    player = Player()

    all_shape_names: List[str] = list(Block.SHAPES.keys())
    current_bag: List[str] = all_shape_names[:] # Initial fill of the Tetris bag
    random.shuffle(current_bag)

    return {
        "game_board": game_board,
        "player": player,
        "current_block": None, # Will be set by the first call to _spawn_new_block_internal
        "next_block": None,    # Will be set by the first call to _spawn_new_block_internal
        "current_bag": current_bag,
        "all_shape_names": all_shape_names,
        "total_lines_cleared": 0,
        "current_fall_delay": INITIAL_FALL_DELAY,
        "last_speed_increase_at_line": -1, # Ensures speed increase can happen at line 0 if interval is met
        "last_fall_time": time.time(),     # Timestamp of the last automatic block fall
        "game_over": False,
        # "command_buffer": None # Not currently used, but could be for more complex input sequences
    }

def _spawn_new_block_internal(game_board: GameBoard,
                             current_block_old: Optional[Block],
                             next_block_old: Optional[Block],
                             current_bag: List[str],
                             all_shape_names_list: List[str]) -> Tuple[Optional[Block], Optional[Block], bool]:
    """
    Manages the spawning of new blocks, including using the Tetris bag system.
    It updates the current and next blocks and checks for game over conditions on spawn.

    Args:
        game_board (GameBoard): The current game board instance.
        current_block_old (Optional[Block]): The block that was previously falling (can be None).
        next_block_old (Optional[Block]): The block that was previously in the "next" preview.
        current_bag (List[str]): The list of shape names for the current Tetris bag (mutated by this function).
        all_shape_names_list (List[str]): A list of all possible shape names (used to refill the bag).

    Returns:
        Tuple[Optional[Block], Optional[Block], bool]:
            - The new current_block (or None if game over).
            - The new next_block.
            - A boolean flag indicating if the game is over due to spawn collision.
    """

    def get_block_from_bag(bag: List[str], all_shapes: List[str]) -> Block:
        """Nested helper to get one block from the bag, refilling if necessary."""
        if not bag: # If the bag is empty
            bag.extend(all_shapes[:]) # Refill with all shapes
            random.shuffle(bag)       # Shuffle for randomness

        shape_name = bag.pop() # Get the next shape from the bag

        # Determine starting position to center the block
        block_matrix = Block.SHAPES[shape_name]
        block_width = len(block_matrix[0]) if block_matrix else 0 # Width of the first row
        start_x = BOARD_WIDTH // 2 - block_width // 2
        start_y = 0 # Blocks spawn at the top
        return Block(shape_name=shape_name, x=start_x, y=start_y)

    current_block_new: Optional[Block]
    next_block_new: Optional[Block]
    game_over_flag: bool = False

    if next_block_old is None: # This is the very first block of the game
        current_block_new = get_block_from_bag(current_bag, all_shape_names_list)
        next_block_new = get_block_from_bag(current_bag, all_shape_names_list)
    else: # Promote the previous next_block to current_block
        current_block_new = next_block_old
        next_block_new = get_block_from_bag(current_bag, all_shape_names_list)

    # Reset the new current_block's position to its spawn point at the top-center
    # This is important because current_block_new might be the `next_block_old` which doesn't have x,y set for board.
    if current_block_new: # Ensure current_block_new is not None before accessing attributes
        block_matrix = current_block_new.get_shape_matrix()
        block_width = len(block_matrix[0]) if block_matrix else 0
        current_block_new.x = BOARD_WIDTH // 2 - block_width // 2
        current_block_new.y = 0

        # Check for immediate collision upon spawning (game over condition)
        if game_board.is_collision(current_block_new, current_block_new.x, current_block_new.y):
            game_over_flag = True
            current_block_new = None # Block cannot be placed, so it shouldn't be drawn
            if ENABLE_SOUND_PLACEHOLDERS: print("SFX: Game Over (Spawn Collision)")


    # Optional: Sound for new block spawn (can be noisy if printed every time)
    # if ENABLE_SOUND_PLACEHOLDERS and not game_over_flag and current_block_new:
    #     print("SFX: New Block Spawned")

    return current_block_new, next_block_new, game_over_flag


def run_game() -> int:
    """
    Runs a single session of the Tetris game, from start until game over.

    Returns:
        int: The player's final score for the session.
    """
    gs: Dict[str, Any] = initialize_game_state()

    # Unpack frequently used mutable objects from game state for easier access
    game_board: GameBoard = gs["game_board"]
    player: Player = gs["player"]
    current_bag: List[str] = gs["current_bag"] # Mutated by _spawn_new_block_internal
    all_shape_names: List[str] = gs["all_shape_names"]


    # Initial block spawn for the game session
    gs["current_block"], gs["next_block"], gs["game_over"] = _spawn_new_block_internal(
        game_board,
        gs["current_block"], # Initially None
        gs["next_block"],    # Initially None
        current_bag,         # Pass the list reference
        all_shape_names
    )
    gs["last_fall_time"] = time.time() # Reset fall timer after first spawn

    global _get_keypress_func # Use the globally determined input function
    is_select_input_active = hasattr(_select_keypress, '__call__') and _get_keypress_func == _select_keypress

    if is_select_input_active:
        _set_raw_terminal() # Set terminal to raw mode for select-based input

    try:
        while not gs["game_over"]:
            command = _get_keypress_func()

            # --- Main Game Loop ---
            command = _get_keypress_func()

            if command == 'q': # Player quits
                gs["game_over"] = True
                if ENABLE_SOUND_PLACEHOLDERS: print("SFX: Quit Game")
                # Loop will terminate after this iteration based on gs["game_over"]

            # Process player input if a block exists
            if gs["current_block"]:
                if command == 'p': # Activate Slow Fall
                    if player.activate_slow_fall():
                        if ENABLE_SOUND_PLACEHOLDERS: print("SFX: Slow Fall Activated!")
                elif command == 'a': # Move Left
                    if not game_board.is_collision(gs["current_block"], gs["current_block"].x - 1, gs["current_block"].y):
                        gs["current_block"].move(-1, 0)
                elif command == 'd': # Move Right
                    if not game_board.is_collision(gs["current_block"], gs["current_block"].x + 1, gs["current_block"].y):
                        gs["current_block"].move(1, 0)
                elif command == 'w': # Rotate
                    rotated_block = gs["current_block"].clone()
                    rotated_block.rotate()
                    if not game_board.is_collision(rotated_block, rotated_block.x, rotated_block.y):
                        gs["current_block"].shape = rotated_block.shape
                        if ENABLE_SOUND_PLACEHOLDERS: print("SFX: Rotate")
                elif command == 's': # Soft Drop
                    if not game_board.is_collision(gs["current_block"], gs["current_block"].x, gs["current_block"].y + 1):
                        gs["current_block"].move(0, 1)
                        gs["last_fall_time"] = time.time() # Reset fall timer to make drop feel immediate
                    else: # Landed due to soft drop attempt
                        game_board.add_block_to_grid(gs["current_block"])
                        if ENABLE_SOUND_PLACEHOLDERS: print("SFX: Block Land (Soft Drop)")

                        lines_cleared_this_turn = game_board.clear_lines()
                        if lines_cleared_this_turn > 0:
                            if ENABLE_SOUND_PLACEHOLDERS: print(f"SFX: Line Cleared ({lines_cleared_this_turn} lines!)")
                            player.increase_score(lines_cleared_this_turn * 100) # Example scoring
                            gs["total_lines_cleared"] += lines_cleared_this_turn
                            player.recharge_slow_fall(lines_cleared_this_turn)

                        # Spawn next block
                        gs["current_block"], gs["next_block"], gs["game_over"] = _spawn_new_block_internal(
                            game_board, gs["current_block"], gs["next_block"], current_bag, all_shape_names
                        )
                        if gs["game_over"]: command = 'q' # Ensure loop terminates if spawn fails

            # --- Automatic Downward Movement (Time-based) ---
            # Determine the effective fall delay for this tick (considering Slow Fall)
            current_effective_fall_delay = gs["current_fall_delay"]
            if player.slow_fall_active:
                current_effective_fall_delay = 0.8 # Fixed slower speed for Slow Fall

            if gs["current_block"] and (time.time() - gs["last_fall_time"] > current_effective_fall_delay):
                if not game_board.is_collision(gs["current_block"], gs["current_block"].x, gs["current_block"].y + 1):
                    gs["current_block"].move(0, 1) # Move block down
                else: # Block has landed (collision detected one step below)
                    game_board.add_block_to_grid(gs["current_block"])
                    if ENABLE_SOUND_PLACEHOLDERS: print("SFX: Block Land (Normal Fall)")

                    lines_cleared_this_turn = game_board.clear_lines()
                    if lines_cleared_this_turn > 0:
                        if ENABLE_SOUND_PLACEHOLDERS: print(f"SFX: Line Cleared ({lines_cleared_this_turn} lines!)")
                        player.increase_score(lines_cleared_this_turn * 100)
                        gs["total_lines_cleared"] += lines_cleared_this_turn
                        player.recharge_slow_fall(lines_cleared_this_turn)

                    # Spawn next block
                    gs["current_block"], gs["next_block"], gs["game_over"] = _spawn_new_block_internal(
                        game_board, gs["current_block"], gs["next_block"], current_bag, all_shape_names
                    )
                    if gs["game_over"]: command = 'q' # Ensure loop terminates if spawn fails
                gs["last_fall_time"] = time.time() # Reset fall timer

            # --- Difficulty Progression ---
            # Check if speed should be increased based on total lines cleared
            if gs["total_lines_cleared"] // SPEED_INCREASE_INTERVAL_LINES > \
               gs["last_speed_increase_at_line"] // SPEED_INCREASE_INTERVAL_LINES:
                if gs["current_fall_delay"] > MIN_FALL_DELAY:
                    gs["current_fall_delay"] = max(MIN_FALL_DELAY, gs["current_fall_delay"] - FALL_DELAY_DECREMENT)
                gs["last_speed_increase_at_line"] = gs["total_lines_cleared"]

            # --- Update Power-ups ---
            player.update_slow_fall(0.016) # Approximate time for one game tick / frame

            # --- Rendering ---
            os.system('cls' if os.name == 'nt' else 'clear') # Clear console

            slow_fall_status: Dict[str, Any] = {
                'charges': player.slow_fall_charges, # From player object
                'active': player.slow_fall_active,
                'remaining': player.slow_fall_duration_remaining,
                'progress': player.slow_fall_recharge_progress,
                'threshold': player.slow_fall_recharge_threshold
            }

            # Get shape for the next block preview, handling if next_block is None (should not happen if game not over)
            next_block_shape_matrix = gs["next_block"].get_shape_matrix() if gs["next_block"] else []

            # Generate the complete UI string
            display_string: str = game_board.get_display_output_string(
                gs["current_block"],    # Current falling block
                next_block_shape_matrix, # Shape of the next block
                player.score,           # Player's score
                gs["total_lines_cleared"], # Total lines cleared
                gs["current_fall_delay"], # Current game speed (fall delay)
                slow_fall_status        # Dictionary of slow fall power-up status
            )
            print(display_string)

            # Sound effect placeholders are printed as events occur, so they will appear
            # interspersed with the game states. This is acceptable for text-based SFX.

            # If game over was triggered in this loop iteration (e.g., by 'q' or spawn failure)
            if gs["game_over"]:
                # No special action here, loop condition will handle termination.
                # Game over message is printed after the loop.
                pass

            # --- Loop Timing ---
            # Control game loop speed, aiming for ~60 FPS for updates if non-blocking input is active.
            # If using blocking input, this sleep is less critical for responsiveness but helps control fall speed.
            loop_sleep_time = 0.016 # Target for ~60 FPS
            if _get_keypress_func is None or \
               (hasattr(_get_keypress_func, '__name__') and _get_keypress_func.__name__ == '_blocking_input_keypress'):
                # If using the blocking input fallback, or if stdin is not a TTY (where select might behave differently)
                # A slightly longer sleep might be acceptable as input() itself pauses.
                # However, the primary fall speed is time-based now. This sleep is more for general CPU usage.
                loop_sleep_time = 0.05
            time.sleep(loop_sleep_time)
        # --- End of Main Game Loop ---

        # --- Game Over Sequence ---
        if ENABLE_SOUND_PLACEHOLDERS: print("SFX: Game Over (Final)")

        # Clear screen one last time for the game over message
        os.system('cls' if os.name == 'nt' else 'clear')

        game_over_message = [
            "╔" + "═" * 30 + "╗",
            "║" + " " * 10 + "GAME OVER" + " " * 11 + "║",
            "╠" + "═" * 30 + "╣",
            f"║ Final Score: {player.score:<15} ║",
            f"║ Lines Cleared: {gs['total_lines_cleared']:<13} ║",
            "╚" + "═" * 30 + "╝",
            "\n"
        ]
        print("\n".join(game_over_message))

        return player.score # Return final score for the session

    finally:
        # Ensure terminal settings are restored if select-based input was used
        if is_select_input_active:
            _restore_terminal_settings()


# --- Main Application Execution ---
if __name__ == "__main__":
    # Setup fallback input method if no non-blocking method was initialized
    if _get_keypress_func is None:
        print("Non-blocking input not available. Using standard input() (game will pause for commands).")
        def _blocking_input_keypress(): # Renamed to avoid conflict if it was somehow defined globally
            try:
                # Prompt clearly indicates it's waiting for action
                action = input("Action (a:left, d:right, w:rotate, s:drop, p:slow-fall, q:quit): ").lower()
                if action: return action[0] # Return the first character of input
            except EOFError: # Handle unexpected end of input (e.g., in CI environments)
                return 'q' # Default to quit to prevent hanging
            return None # No input or empty input
        _get_keypress_func = _blocking_input_keypress

    # --- Outer Game Loop (allows playing multiple sessions) ---
    while True:
        final_score_this_game = run_game()
        # Optional: print(f"Game session ended with score: {final_score_this_game}")

        # Prompt to play again
        while True:
            try:
                play_again_choice = input("Play again? (y/n): ").lower()
                if play_again_choice in ['y', 'n']:
                    break
                print("Invalid input. Please enter 'y' or 'n'.")
            except EOFError:
                play_again_choice = 'n' # Default to not playing again if input stream ends
                break

        if play_again_choice != 'y':
            print("Thanks for playing Tetris!")
            break

    # Final cleanup of terminal settings (safeguard, should be handled by run_game's finally)
    if hasattr(_select_keypress, '__call__') and _get_keypress_func == _select_keypress:
        _restore_terminal_settings()
