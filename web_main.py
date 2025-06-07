import time
import random

from pyodide.ffi import create_proxy, to_js
import js

from block import Block
from game_board import GameBoard, BOARD_WIDTH, BOARD_HEIGHT
from player import Player

# --- Game Constants (Web Canvas Version) ---
CELL_SIZE: int = 20  # pixels per cell
GAME_AREA_TEXT_COLOR: str = "#FFFFFF" # White for score, lines, etc.
PREVIEW_AREA_X_OFFSET: int = (BOARD_WIDTH * CELL_SIZE) + 30 # Where score/next block info starts
INFO_TEXT_Y_START: int = 30
INFO_TEXT_LINE_HEIGHT: int = 20

BLOCK_COLORS: Dict[str, str] = {
    'T': '#AA00AA', # Purple
    'L': '#FFA500', # Orange
    'J': '#0000FF', # Blue
    'S': '#00FF00', # Green
    'Z': '#FF0000', # Red
    'I': '#00FFFF', # Cyan
    'O': '#FFFF00', # Yellow
    'DEFAULT': '#777777' # Default color for blocks if not found
}
EMPTY_CELL_COLOR: str = "#1A1A1A" # Very dark grey, almost black for board background
BOARD_GRID_LINE_COLOR: str = "#333333" # Dark grey for grid lines if drawn
LANDED_BLOCK_OUTLINE_COLOR: str = "#444444" # Slightly lighter outline for landed blocks

# --- Global Game State Variables ---
game_board_instance: Optional[GameBoard] = None
player_instance: Optional[Player] = None
current_block: Optional[Block] = None
next_block: Optional[Block] = None
current_bag: List[str] = []
all_shape_names: List[str] = []

score: int = 0
total_lines_cleared: int = 0
current_fall_delay: float = 0.7 # Default, will be set by initialize
last_speed_increase_at_line: int = -1

last_fall_time: float = 0.0
game_over: bool = True
game_paused: bool = False
input_key_buffer: Optional[str] = None

DOM_STATUS_ID: str = "status" # Default, can be overridden by JS

# --- DOM Interaction Helper (for status messages) ---
def update_dom_element(element_id: str, content: str) -> None:
    try:
        element = js.document.getElementById(element_id)
        if element:
            element.innerText = content
        else:
            js.console.error(f"Element with ID '{element_id}' not found in the DOM.")
    except Exception as e:
        js.console.error(f"Error updating DOM element '{element_id}': {str(e)}")

# --- Game Initialization ---
def initialize_game_for_web() -> None:
    global game_board_instance, player_instance, current_block, next_block, current_bag, all_shape_names
    global score, total_lines_cleared, current_fall_delay, last_speed_increase_at_line, last_fall_time
    global game_over, game_paused, input_key_buffer, DOM_STATUS_ID
    # Game speed constants from web_main.py, not console version
    global WEB_INITIAL_FALL_DELAY, WEB_MIN_FALL_DELAY, WEB_SPEED_INCREASE_INTERVAL_LINES, WEB_FALL_DELAY_DECREMENT


    js.console.log("Python: initialize_game_for_web() called for canvas rendering.")

    if js.pyodide.globals.has('status_element_id'): # Fetch if JS set it
        DOM_STATUS_ID = str(js.pyodide.globals.get('status_element_id'))

    game_board_instance = GameBoard(width=BOARD_WIDTH, height=BOARD_HEIGHT)
    player_instance = Player()

    if not all_shape_names:
        all_shape_names = list(Block.SHAPES.keys())

    current_bag = all_shape_names[:]
    random.shuffle(current_bag)

    score = 0
    total_lines_cleared = 0
    current_fall_delay = WEB_INITIAL_FALL_DELAY # Use web specific constant
    last_speed_increase_at_line = -1

    # Initial block spawning
    # Need to assign to global current_block and next_block from the tuple returned
    current_block, next_block, game_over_on_spawn = _spawn_block_web()
    if game_over_on_spawn:
        game_over = True
    else:
        game_over = False

    game_paused = False
    input_key_buffer = None
    last_fall_time = time.time()

    # Setup canvas dimensions
    canvas_width = (BOARD_WIDTH * CELL_SIZE) + 200  # Extra 200px for info panel
    canvas_height = BOARD_HEIGHT * CELL_SIZE
    try:
        js_set_dim_func = js.globals.get('js_set_canvas_dimensions')
        if js_set_dim_func:
            js_set_dim_func(canvas_width, canvas_height)
        else:
            js.console.error("JS function 'js_set_canvas_dimensions' not found.")
    except Exception as e:
        js.console.error(f"Python error setting canvas dimensions: {e}")

    _render_game_state()
    update_dom_element(DOM_STATUS_ID, "Game Ready. Use keyboard to play.")
    js.console.log("Python: Game initialized for canvas and initial state rendered.")


def _spawn_block_web() -> Tuple[Optional[Block], Optional[Block], bool]:
    global current_bag, all_shape_names, next_block

    def get_from_bag(bag: List[str], all_shapes: List[str]) -> Block:
        if not bag:
            bag.extend(all_shapes[:])
            random.shuffle(bag)
        shape_name = bag.pop()
        start_x = BOARD_WIDTH // 2 - len(Block.SHAPES[shape_name][0]) // 2
        return Block(shape_name=shape_name, x=start_x, y=0)

    new_current_block: Optional[Block]
    is_game_over_on_spawn = False

    if next_block is None:
        new_current_block = get_from_bag(current_bag, all_shape_names)
        next_block = get_from_bag(current_bag, all_shape_names)
    else:
        new_current_block = next_block
        next_block = get_from_bag(current_bag, all_shape_names)

    if new_current_block:
        new_current_block.x = BOARD_WIDTH // 2 - len(new_current_block.shape[0]) // 2
        new_current_block.y = 0
        if game_board_instance and game_board_instance.is_collision(new_current_block, new_current_block.x, new_current_block.y):
            is_game_over_on_spawn = True
            new_current_block = None

    return new_current_block, next_block, is_game_over_on_spawn


def handle_input_from_js(key_pressed: str) -> None:
    global input_key_buffer, game_paused, game_over
    js.console.log(f"Python received key: {key_pressed}")

    if game_over:
        if key_pressed.lower() == 'q':
            js.console.log("Python: Restarting game from 'q' press.")
            initialize_game_for_web()
        return

    if not game_paused:
        key_map = {
            "arrowleft": "a", "arrowright": "d", "arrowup": "w", "arrowdown": "s", " ": " "
        }
        normalized_key = key_pressed.lower()
        input_key_buffer = key_map.get(normalized_key, normalized_key)


def python_game_tick() -> None:
    global last_fall_time, current_block, next_block, game_over, game_paused, input_key_buffer
    global score, total_lines_cleared, current_fall_delay, last_speed_increase_at_line
    # Game speed constants for difficulty progression
    global WEB_INITIAL_FALL_DELAY, WEB_MIN_FALL_DELAY, WEB_SPEED_INCREASE_INTERVAL_LINES, WEB_FALL_DELAY_DECREMENT


    if game_over or game_paused:
        if game_over:
             _render_game_state()
        return

    if not game_board_instance or not player_instance:
        js.console.error("Python Error: Game components not initialized in tick.")
        return

    # --- 1. Process Input ---
    if input_key_buffer and current_block:
        key_to_process = input_key_buffer
        input_key_buffer = None

        if key_to_process == 'a':
            if not game_board_instance.is_collision(current_block, current_block.x - 1, current_block.y):
                current_block.move(-1, 0)
        elif key_to_process == 'd':
            if not game_board_instance.is_collision(current_block, current_block.x + 1, current_block.y):
                current_block.move(1, 0)
        elif key_to_process == 'w':
            rotated_block = current_block.clone()
            rotated_block.rotate()
            if not game_board_instance.is_collision(rotated_block, rotated_block.x, rotated_block.y):
                current_block.shape = rotated_block.shape
        elif key_to_process == 's':
            if not game_board_instance.is_collision(current_block, current_block.x, current_block.y + 1):
                current_block.move(0, 1)
                last_fall_time = time.time()
            else:
                _handle_block_landing()
        elif key_to_process == 'p':
            if player_instance.activate_slow_fall():
                js.console.log("Python: Slow Fall activated.")
        elif key_to_process == 'q':
            game_over = True
            js.console.log("Python: Game quit by 'q' press.")

    # --- 2. Game Logic: Automatic Downward Movement ---
    effective_delay = current_fall_delay
    if player_instance.slow_fall_active:
        effective_delay = WEB_INITIAL_FALL_DELAY + 0.3 # Use WEB_INITIAL for consistency

    if current_block and (time.time() - last_fall_time > effective_delay):
        if not game_board_instance.is_collision(current_block, current_block.x, current_block.y + 1):
            current_block.move(0, 1)
        else:
            _handle_block_landing()
        last_fall_time = time.time()

    # --- 3. Update Difficulty / Game Speed ---
    if total_lines_cleared // WEB_SPEED_INCREASE_INTERVAL_LINES > \
       last_speed_increase_at_line // WEB_SPEED_INCREASE_INTERVAL_LINES:
        if current_fall_delay > WEB_MIN_FALL_DELAY:
            current_fall_delay = max(WEB_MIN_FALL_DELAY, current_fall_delay - WEB_FALL_DELAY_DECREMENT)
            js.console.log(f"Python: Speed increased. New delay: {current_fall_delay:.3f}s")
        last_speed_increase_at_line = total_lines_cleared

    if player_instance:
        player_instance.update_slow_fall(0.016)

    _render_game_state()

    if game_over:
         js.console.log("Python: Game over detected in tick, status will be updated by render.")


def _handle_block_landing() -> None:
    global current_block, next_block, game_over, score, total_lines_cleared

    if not current_block or not game_board_instance or not player_instance:
        js.console.error("Python Error: _handle_block_landing called with uninitialized components.")
        return

    game_board_instance.add_block_to_grid(current_block)

    lines_cleared_this_turn = game_board_instance.clear_lines()
    if lines_cleared_this_turn > 0:
        js.console.log(f"Python: Lines cleared: {lines_cleared_this_turn}")
        player_instance.increase_score(lines_cleared_this_turn * 100 * lines_cleared_this_turn)
        total_lines_cleared += lines_cleared_this_turn
        player_instance.recharge_slow_fall(lines_cleared_this_turn)

    score = player_instance.score

    new_current, _, game_over_on_spawn = _spawn_block_web()
    current_block = new_current
    if game_over_on_spawn:
        game_over = True
        js.console.log("Python: Game over due to spawn collision after landing.")


def _render_game_state() -> None:
    global DOM_STATUS_ID

    if not game_board_instance or not player_instance:
        js.console.error("Python Error: _render_game_state - game components not initialized.")
        return

    try:
        js_clear = js.globals.get('js_clear_canvas')
        js_draw_r = js.globals.get('js_draw_rect')
        js_draw_t = js.globals.get('js_draw_text')

        if not all([js_clear, js_draw_r, js_draw_t]):
            js.console.error("Python Error: JS drawing functions not found.")
            return

        js_clear()

        # Draw Board Outline / Background
        # Outer border
        # js_draw_r(0, 0, BOARD_WIDTH * CELL_SIZE, BOARD_HEIGHT * CELL_SIZE, BOARD_GRID_LINE_COLOR)
        # Inner background
        # js_draw_r(1, 1, BOARD_WIDTH * CELL_SIZE - 2, BOARD_HEIGHT * CELL_SIZE - 2, EMPTY_CELL_COLOR)


        # Draw Landed Blocks & Grid background cells
        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH):
                px, py = c * CELL_SIZE, r * CELL_SIZE
                cell_value = game_board_instance.grid[r][c]
                if cell_value != 0: # Landed block
                    # For now, use a generic color for all landed blocks.
                    # To use original block colors, grid would need to store more info (e.g., shape_name or color_id)
                    color = BLOCK_COLORS['DEFAULT']
                    js_draw_r(px, py, CELL_SIZE -1 , CELL_SIZE - 1, color)
                    # Optional: draw outline for landed blocks
                    # js_draw_r(px, py, CELL_SIZE, CELL_SIZE, LANDED_BLOCK_OUTLINE_COLOR) # Draw outline first
                    # js_draw_r(px + 1, py + 1, CELL_SIZE - 2, CELL_SIZE - 2, color)      # Then fill
                else: # Empty cell
                    js_draw_r(px, py, CELL_SIZE -1, CELL_SIZE -1, EMPTY_CELL_COLOR)


        # Draw Falling Block (current_block)
        if current_block:
            color = BLOCK_COLORS.get(current_block.shape_name, BLOCK_COLORS['DEFAULT'])
            for r_idx, row in enumerate(current_block.shape):
                for c_idx, cell in enumerate(row):
                    if cell != 0:
                        board_r, board_c = current_block.y + r_idx, current_block.x + c_idx
                        if 0 <= board_r < BOARD_HEIGHT: # Only draw if within vertical board bounds (partially visible at top)
                            px, py = board_c * CELL_SIZE, board_r * CELL_SIZE
                            js_draw_r(px, py, CELL_SIZE - 1, CELL_SIZE - 1, color)

        # --- Draw Info Panel (Score, Next Block, etc.) ---
        current_y = INFO_TEXT_Y_START

        js_draw_t("Next:", PREVIEW_AREA_X_OFFSET, current_y, color=GAME_AREA_TEXT_COLOR, font="bold 18px Courier New")
        current_y += INFO_TEXT_LINE_HEIGHT

        if next_block:
            color = BLOCK_COLORS.get(next_block.shape_name, BLOCK_COLORS['DEFAULT'])
            shape_matrix = next_block.get_shape_matrix()
            # Find offset to center the preview block (assuming max 4x4 preview)
            preview_block_offset_x = 0
            if len(shape_matrix[0]) < 4 :
                 preview_block_offset_x = ((4 - len(shape_matrix[0])) * CELL_SIZE) // 2


            for r_idx, row in enumerate(shape_matrix):
                for c_idx, cell in enumerate(row):
                    if cell != 0:
                        px = PREVIEW_AREA_X_OFFSET + preview_block_offset_x + (c_idx * CELL_SIZE)
                        py = current_y + (r_idx * CELL_SIZE)
                        js_draw_r(px, py, CELL_SIZE - 1, CELL_SIZE - 1, color)
            current_y += (len(shape_matrix) * CELL_SIZE) + INFO_TEXT_LINE_HEIGHT # Space after block

        js_draw_t(f"Score: {score}", PREVIEW_AREA_X_OFFSET, current_y, color=GAME_AREA_TEXT_COLOR, font="18px Courier New")
        current_y += INFO_TEXT_LINE_HEIGHT
        js_draw_t(f"Lines: {total_lines_cleared}", PREVIEW_AREA_X_OFFSET, current_y, color=GAME_AREA_TEXT_COLOR, font="18px Courier New")
        current_y += INFO_TEXT_LINE_HEIGHT
        js_draw_t(f"Speed: {current_fall_delay:.2f}s", PREVIEW_AREA_X_OFFSET, current_y, color=GAME_AREA_TEXT_COLOR, font="18px Courier New")
        current_y += INFO_TEXT_LINE_HEIGHT

        if player_instance:
            sf_status = player_instance.get_slow_fall_status_dict()
            sf_active_str = "Yes" if sf_status['active'] else "No"
            js_draw_t(f"SlowFall: {sf_status['charges']} ({sf_active_str})", PREVIEW_AREA_X_OFFSET, current_y, color=GAME_AREA_TEXT_COLOR, font="16px Courier New")
            current_y += INFO_TEXT_LINE_HEIGHT
            js_draw_t(f"SF Recharge: {sf_status['progress']}/{sf_status['threshold']}", PREVIEW_AREA_X_OFFSET, current_y, color=GAME_AREA_TEXT_COLOR, font="14px Courier New")
            current_y += INFO_TEXT_LINE_HEIGHT


        # Update Status DOM Element (for text messages like Game Over)
        if game_over:
            status_msg = f"Game Over! Score: {score}. 'Q' to Restart."
            # Optionally draw GAME OVER text on canvas too
            game_over_text_x = (BOARD_WIDTH * CELL_SIZE) / 2
            game_over_text_y = (BOARD_HEIGHT * CELL_SIZE) / 2
            js_draw_t("GAME OVER", game_over_text_x, game_over_text_y - 20, font="bold 40px Courier New", color="red", textAlign="center")
            js_draw_t("Press 'Q' to Restart", game_over_text_x, game_over_text_y + 20, font="20px Courier New", color="white", textAlign="center")

        else:
            status_msg = f"Score: {score} | Lines: {total_lines_cleared}"
        update_dom_element(DOM_STATUS_ID, status_msg)

    except Exception as e:
        js.console.error(f"Python error during _render_game_state: {e}")
        # Attempt to update status with error if possible
        try:
            update_dom_element(DOM_STATUS_ID, f"Render Error: {e}")
        except:
            pass


try:
    js.globals['initialize_game_for_web'] = initialize_game_for_web
    js.globals['python_game_tick'] = python_game_tick
    js.globals['handle_input_from_js'] = handle_input_from_js

    _python_is_ready_for_game = False
    def is_game_ready_for_js():
        global _python_is_ready_for_game
        _python_is_ready_for_game = game_board_instance is not None and player_instance is not None
        return _python_is_ready_for_game
    js.globals['is_game_ready_for_js'] = is_game_ready_for_js

    js.console.log("Python: web_main.py executed, functions exposed.")
except Exception as e:
    js.console.error(f"Python error during exposing functions to JS: {e}")
