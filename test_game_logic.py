import unittest
import copy # For deepcopy in tests if needed

# Assuming the game files are in the same directory or accessible via PYTHONPATH
from block import Block
from game_board import GameBoard, BOARD_WIDTH, BOARD_HEIGHT
from player import Player

class TestBlock(unittest.TestCase):
    def test_rotation_L_shape(self):
        """Test clockwise rotation of an L-shape block."""
        # Initial L-shape: [[1, 0, 0], [1, 1, 1]]
        l_block = Block("L")
        original_shape = copy.deepcopy(l_block.shape)

        # 1st rotation: [[1, 1], [1, 0], [1, 0]]
        l_block.rotate()
        expected_shape_1 = [[1, 1], [1, 0], [1, 0]]
        self.assertEqual(l_block.shape, expected_shape_1, "Rotation 1 failed")

        # 2nd rotation: [[1, 1, 1], [0, 0, 1]]
        l_block.rotate()
        expected_shape_2 = [[1, 1, 1], [0, 0, 1]]
        self.assertEqual(l_block.shape, expected_shape_2, "Rotation 2 failed")

        # 3rd rotation: [[0, 1], [0, 1], [1, 1]]
        l_block.rotate()
        expected_shape_3 = [[0, 1], [0, 1], [1, 1]]
        self.assertEqual(l_block.shape, expected_shape_3, "Rotation 3 failed")

        # 4th rotation: should be back to original
        l_block.rotate()
        self.assertEqual(l_block.shape, original_shape, "Rotation 4 (back to original) failed")

    def test_rotation_I_shape_vertical(self):
        """Test rotation of an I-shape (initially horizontal)."""
        # Block.SHAPES["I"] is [[1, 1, 1, 1]]
        # To test vertical to horizontal, we need a shape that starts vertical,
        # or rotate the horizontal one first.
        # Let's assume Block("I") gives the standard horizontal one.
        i_block = Block("I")
        i_block.shape = [[1], [1], [1], [1]] # Manually set to vertical I
        original_vertical = copy.deepcopy(i_block.shape)

        # 1st rotation (to horizontal): [[1, 1, 1, 1]]
        i_block.rotate()
        expected_horizontal = [[1, 1, 1, 1]]
        self.assertEqual(i_block.shape, expected_horizontal, "I-shape vertical to horizontal failed")

        # 2nd rotation (back to vertical): [[1], [1], [1], [1]]
        i_block.rotate()
        self.assertEqual(i_block.shape, original_vertical, "I-shape horizontal to vertical failed")


    def test_clone(self):
        """Test that clone() creates a true deep copy of the block."""
        block = Block("T", x=5, y=10)
        block.rotate() # Change shape from original

        cloned_block = block.clone()

        # Check for deep copy (different objects)
        self.assertIsNot(block, cloned_block, "Clone is not a new object.")
        self.assertIsNot(block.shape, cloned_block.shape, "Shape attribute is not a deep copy.")

        # Check for value equality
        self.assertEqual(block.shape, cloned_block.shape, "Cloned shape matrix is not equal.")
        self.assertEqual(block.color, cloned_block.color, "Cloned color is not equal.")
        self.assertEqual(block.x, cloned_block.x, "Cloned x position is not equal.")
        self.assertEqual(block.y, cloned_block.y, "Cloned y position is not equal.")
        self.assertEqual(block.shape_name, cloned_block.shape_name, "Cloned shape_name is not equal.")

        # Modify original, ensure clone is unaffected
        block.move(1, 1)
        block.rotate()
        original_shape_after_modification = copy.deepcopy(block.shape)

        self.assertNotEqual(block.x, cloned_block.x, "Modifying original's x affected clone's x.")
        self.assertNotEqual(block.y, cloned_block.y, "Modifying original's y affected clone's y.")
        # This will fail if rotate() was not applied to original, or if shapes were identical before
        # Ensure the shapes were different after the original block.rotate()
        self.assertNotEqual(original_shape_after_modification, cloned_block.shape,
                            "Modifying original's shape affected clone's shape.")


class TestGameBoard(unittest.TestCase):
    def setUp(self):
        """Set up a new GameBoard for each test."""
        self.board = GameBoard() # Uses BOARD_WIDTH, BOARD_HEIGHT from game_board.py

    def test_initial_empty_grid(self):
        """Test if the grid is initialized as empty (all zeros)."""
        for r in range(self.board.height):
            for c in range(self.board.width):
                self.assertEqual(self.board.grid[r][c], 0, f"Cell ({r},{c}) is not empty.")

    def test_collision_boundary_left_right(self):
        """Test collision with left and right boundaries."""
        block = Block("I") # Horizontal I: [[1,1,1,1]]
        # Test left boundary
        self.assertTrue(self.board.is_collision(block, x=-1, y=0), "Collision not detected at left boundary.")
        # Test right boundary (I shape width is 4)
        self.assertTrue(self.board.is_collision(block, x=BOARD_WIDTH - 3, y=0), "Collision not detected at right boundary for I-block (width 4).")
        self.assertFalse(self.board.is_collision(block, x=BOARD_WIDTH - 4, y=0), "False collision at right boundary edge for I-block.")


    def test_collision_boundary_bottom(self):
        """Test collision with the bottom boundary."""
        block = Block("T") # T shape height is 2
        # Position block so its bottom edge is at BOARD_HEIGHT
        self.assertTrue(self.board.is_collision(block, x=0, y=BOARD_HEIGHT - 1), "Collision not detected at bottom boundary.")
        self.assertFalse(self.board.is_collision(block, x=0, y=BOARD_HEIGHT - 2), "False collision at bottom boundary edge.")


    def test_add_block_to_grid(self):
        """Test adding a block to the grid updates cells correctly."""
        block = Block("O") # O-shape: [[1,1],[1,1]]
        block.x = 3
        block.y = 5
        self.board.add_block_to_grid(block)

        # Check cells where the O-block should be
        self.assertEqual(self.board.grid[5][3], 1, "Cell (5,3) not updated for O-block.")
        self.assertEqual(self.board.grid[5][4], 1, "Cell (5,4) not updated for O-block.")
        self.assertEqual(self.board.grid[6][3], 1, "Cell (6,3) not updated for O-block.")
        self.assertEqual(self.board.grid[6][4], 1, "Cell (6,4) not updated for O-block.")
        # Check a cell that should remain empty
        self.assertEqual(self.board.grid[0][0], 0, "Cell (0,0) should be empty.")

    def test_collision_with_other_blocks(self):
        """Test collision when moving a block into another landed block."""
        block1 = Block("O") # [[1,1],[1,1]]
        block1.x = 4
        block1.y = BOARD_HEIGHT - 2 # Land it at the bottom
        self.board.add_block_to_grid(block1)

        block2 = Block("I") # [[1,1,1,1]] horizontal
        # Try to move block2 into block1's space from above
        self.assertTrue(self.board.is_collision(block2, x=3, y=BOARD_HEIGHT - 2),
                        "Collision not detected when block2 overlaps block1.")
        # Try to move block2 next to block1 (should not collide)
        self.assertFalse(self.board.is_collision(block2, x=0, y=BOARD_HEIGHT - 1),
                         "False collision when block2 is next to block1.")


    def test_no_collision_valid_move(self):
        """Test that valid moves do not report collision."""
        block = Block("L")
        self.assertFalse(self.board.is_collision(block, x=0, y=0), "Collision reported for valid placement at (0,0).")
        self.assertFalse(self.board.is_collision(block, x=BOARD_WIDTH // 2, y=BOARD_HEIGHT // 2),
                         "Collision reported for valid placement in middle of board.")

    def test_clear_lines_single(self):
        """Test clearing a single complete line."""
        # Fill the bottom line completely
        for c in range(self.board.width):
            self.board.grid[BOARD_HEIGHT - 1][c] = 1
        # Add some blocks on the line above, but not a full line
        self.board.grid[BOARD_HEIGHT - 2][0] = 1
        self.board.grid[BOARD_HEIGHT - 2][self.board.width -1] = 1

        lines_cleared = self.board.clear_lines()
        self.assertEqual(lines_cleared, 1, "Should have cleared 1 line.")
        # Check that the previously second to bottom line is now the bottom and empty cells above it
        self.assertEqual(self.board.grid[BOARD_HEIGHT - 1][0], 1, "Block did not shift down correctly.")
        self.assertEqual(self.board.grid[BOARD_HEIGHT - 1][self.board.width -1], 1, "Block did not shift down correctly.")
        self.assertTrue(all(c == 0 for c in self.board.grid[0]), "Top line should be empty after clear.")

    def test_clear_lines_multiple(self):
        """Test clearing multiple complete lines."""
        # Fill bottom two lines
        for r in range(BOARD_HEIGHT - 2, BOARD_HEIGHT):
            for c in range(self.board.width):
                self.board.grid[r][c] = 1
        # Add a block on the third line from bottom
        self.board.grid[BOARD_HEIGHT - 3][0] = 1

        lines_cleared = self.board.clear_lines()
        self.assertEqual(lines_cleared, 2, "Should have cleared 2 lines.")
        self.assertEqual(self.board.grid[BOARD_HEIGHT - 1][0], 1, "Block from 3rd line did not shift down to bottom.")
        self.assertTrue(all(c == 0 for c in self.board.grid[0]), "Top line should be empty.")
        self.assertTrue(all(c == 0 for c in self.board.grid[1]), "Second line should be empty.")

    def test_clear_lines_no_lines(self):
        """Test clear_lines on a board with no full lines."""
        self.board.grid[BOARD_HEIGHT - 1][0] = 1
        self.board.grid[BOARD_HEIGHT - 1][BOARD_WIDTH - 1] = 1
        original_grid_state = copy.deepcopy(self.board.grid)

        lines_cleared = self.board.clear_lines()
        self.assertEqual(lines_cleared, 0, "Should have cleared 0 lines.")
        self.assertEqual(self.board.grid, original_grid_state, "Grid should not change if no lines are cleared.")

    def test_clear_lines_empty_board(self):
        """Test clear_lines on a completely empty board."""
        original_grid_state = copy.deepcopy(self.board.grid)
        lines_cleared = self.board.clear_lines()
        self.assertEqual(lines_cleared, 0, "Should have cleared 0 lines on empty board.")
        self.assertEqual(self.board.grid, original_grid_state, "Empty grid should not change.")


class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.player = Player()

    def test_initial_state(self):
        """Test initial state of player attributes, especially for Slow Fall."""
        self.assertEqual(self.player.score, 0)
        self.assertEqual(self.player.slow_fall_charges, 1, "Initial slow fall charges incorrect.")
        self.assertFalse(self.player.slow_fall_active, "Slow fall should be inactive initially.")
        self.assertEqual(self.player.slow_fall_duration_remaining, 0.0)
        self.assertEqual(self.player.slow_fall_recharge_progress, 0)
        self.assertEqual(self.player.slow_fall_recharge_threshold, 10) # Default or as set
        self.assertEqual(self.player.max_slow_fall_charges, 3) # Default or as set

    def test_increase_score(self):
        self.player.increase_score(100)
        self.assertEqual(self.player.score, 100)
        self.player.increase_score(50)
        self.assertEqual(self.player.score, 150)

    def test_slow_fall_activation_success(self):
        """Test successful activation of Slow Fall."""
        activated = self.player.activate_slow_fall()
        self.assertTrue(activated, "Slow fall failed to activate with charges available.")
        self.assertEqual(self.player.slow_fall_charges, 0, "Charges did not decrement.")
        self.assertTrue(self.player.slow_fall_active, "Slow fall not set to active.")
        self.assertEqual(self.player.slow_fall_duration_remaining, self.player.slow_fall_duration_total)

    def test_slow_fall_activation_no_charges(self):
        """Test activating Slow Fall with no charges."""
        self.player.slow_fall_charges = 0
        activated = self.player.activate_slow_fall()
        self.assertFalse(activated, "Slow fall activated with no charges.")
        self.assertFalse(self.player.slow_fall_active)

    def test_slow_fall_activation_already_active(self):
        """Test activating Slow Fall when it's already active."""
        self.player.activate_slow_fall() # First activation
        self.player.slow_fall_charges = 1 # Give another charge for testing

        original_duration = self.player.slow_fall_duration_remaining
        activated_again = self.player.activate_slow_fall()

        self.assertFalse(activated_again, "Slow fall should not reactivate if already active.")
        self.assertEqual(self.player.slow_fall_charges, 1, "Charges should not decrement if not reactivated.")
        self.assertEqual(self.player.slow_fall_duration_remaining, original_duration, "Duration should not reset.")


    def test_slow_fall_update_and_deactivation(self):
        """Test duration update and deactivation of Slow Fall."""
        self.player.activate_slow_fall()
        self.assertTrue(self.player.slow_fall_active)

        # Simulate time passing, but not enough to deactivate
        self.player.update_slow_fall(self.player.slow_fall_duration_total / 2)
        self.assertTrue(self.player.slow_fall_active)
        self.assertAlmostEqual(self.player.slow_fall_duration_remaining, self.player.slow_fall_duration_total / 2)

        # Simulate enough time to deactivate
        self.player.update_slow_fall(self.player.slow_fall_duration_total / 2 + 0.1) # Add a bit more
        self.assertFalse(self.player.slow_fall_active, "Slow fall did not deactivate after duration.")
        self.assertEqual(self.player.slow_fall_duration_remaining, 0)

    def test_slow_fall_recharge_progress(self):
        """Test progress towards earning a new Slow Fall charge."""
        self.player.slow_fall_charges = 0 # Start with 0 charges to test earning one
        self.player.recharge_slow_fall(5)
        self.assertEqual(self.player.slow_fall_recharge_progress, 5)
        self.assertEqual(self.player.slow_fall_charges, 0) # Not enough to earn a charge

    def test_slow_fall_recharge_earn_charge(self):
        """Test earning a Slow Fall charge by meeting the threshold."""
        self.player.slow_fall_charges = 0
        self.player.recharge_slow_fall(self.player.slow_fall_recharge_threshold) # Exact threshold
        self.assertEqual(self.player.slow_fall_charges, 1, "Did not earn a charge after meeting threshold.")
        self.assertEqual(self.player.slow_fall_recharge_progress, 0, "Recharge progress did not reset.")

    def test_slow_fall_recharge_earn_multiple_charges_if_possible(self):
        """Test earning multiple charges if lines cleared are high enough (player.py handles this in a loop)."""
        self.player.slow_fall_charges = 0
        lines_for_two_charges = self.player.slow_fall_recharge_threshold * 2 + 5 # 2 charges + 5 progress
        self.player.recharge_slow_fall(lines_for_two_charges)
        self.assertEqual(self.player.slow_fall_charges, 2, "Did not earn two charges.")
        self.assertEqual(self.player.slow_fall_recharge_progress, 5, "Incorrect remaining progress.")


    def test_slow_fall_max_charges(self):
        """Test that Slow Fall charges do not exceed the maximum."""
        self.player.slow_fall_charges = self.player.max_slow_fall_charges -1
        # Earn one charge
        self.player.recharge_slow_fall(self.player.slow_fall_recharge_threshold)
        self.assertEqual(self.player.slow_fall_charges, self.player.max_slow_fall_charges)

        # Try to earn another charge
        self.player.recharge_slow_fall(self.player.slow_fall_recharge_threshold)
        self.assertEqual(self.player.slow_fall_charges, self.player.max_slow_fall_charges, "Charges exceeded maximum.")
        # Progress should be capped at threshold if charges are full
        self.assertEqual(self.player.slow_fall_recharge_progress, self.player.slow_fall_recharge_threshold,
                         "Progress should be capped at threshold when charges are maxed.")

    def test_slow_fall_recharge_progress_when_maxed(self):
        self.player.slow_fall_charges = self.player.max_slow_fall_charges
        self.player.slow_fall_recharge_progress = 0 # Start progress at 0
        self.player.recharge_slow_fall(5)
        # Even if max charges, progress should still track towards the next potential earn
        # IF Player.recharge_slow_fall allows progress accumulation when maxed.
        # Based on current Player.recharge_slow_fall, it caps progress at threshold if maxed.
        self.assertEqual(self.player.slow_fall_recharge_progress, 5)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
