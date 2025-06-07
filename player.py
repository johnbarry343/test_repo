class Player:
    """
    Manages player-specific information, including score and special abilities.

    Attributes:
        score (int): The player's current score.
        slow_fall_charges (int): Number of available charges for the Slow Fall ability.
        slow_fall_active (bool): True if Slow Fall is currently active, False otherwise.
        slow_fall_duration_total (float): Default duration of the Slow Fall ability in seconds.
        slow_fall_duration_remaining (float): Remaining time for active Slow Fall in seconds.
        slow_fall_recharge_threshold (int): Number of lines to clear to earn a new Slow Fall charge.
        slow_fall_recharge_progress (int): Current progress (lines cleared) towards the next charge.
        max_slow_fall_charges (int): Maximum number of Slow Fall charges a player can hold.
    """
    def __init__(self):
        """Initializes player attributes."""
        self.score: int = 0

        # Slow Fall ability attributes
        self.slow_fall_charges: int = 1
        self.slow_fall_active: bool = False
        self.slow_fall_duration_total: float = 5.0  # seconds
        self.slow_fall_duration_remaining: float = 0.0
        self.slow_fall_recharge_threshold: int = 10 # lines to clear for a new charge
        self.slow_fall_recharge_progress: int = 0
        self.max_slow_fall_charges: int = 3

    def increase_score(self, points: int) -> None:
        """
        Increases the player's score by the given number of points.

        Args:
            points (int): The number of points to add to the score.
        """
        if points < 0:
            # Consider if score can be reduced or if this should be an error/warning.
            # For typical Tetris, score only increases.
            print("Warning: Attempted to increase score by a negative number.")
            return
        self.score += points

    def _earn_slow_fall_charge(self) -> None:
        """
        Grants one Slow Fall charge, up to the maximum limit.
        Resets recharge progress. This is an internal helper.
        """
        if self.slow_fall_charges < self.max_slow_fall_charges:
            self.slow_fall_charges += 1
        # Always reset progress, even if charges were already maxed (e.g. if called directly by mistake)
        # or to signify that the "current" earning cycle is complete.
        self.slow_fall_recharge_progress = 0

    def recharge_slow_fall(self, lines_cleared_count: int) -> None:
        """
        Updates progress towards earning a new Slow Fall charge based on lines cleared.
        If the threshold is met or exceeded, grants charge(s).

        Args:
            lines_cleared_count (int): Number of lines cleared in the current turn.
        """
        if lines_cleared_count <= 0:
            return

        self.slow_fall_recharge_progress += lines_cleared_count

        # Loop to handle earning multiple charges if many lines are cleared at once
        while self.slow_fall_recharge_progress >= self.slow_fall_recharge_threshold:
            if self.slow_fall_charges < self.max_slow_fall_charges:
                self.slow_fall_recharge_progress -= self.slow_fall_recharge_threshold
                self._earn_slow_fall_charge() # Use the internal method
            else:
                # If charges are maxed out, progress should not exceed the threshold.
                # This indicates player is ready for next charge once one is used.
                self.slow_fall_recharge_progress = self.slow_fall_recharge_threshold
                break # No more charges can be earned right now

    def activate_slow_fall(self) -> bool:
        """
        Activates the Slow Fall ability if charges are available and it's not already active.

        Returns:
            bool: True if Slow Fall was successfully activated, False otherwise.
        """
        if self.slow_fall_charges > 0 and not self.slow_fall_active:
            self.slow_fall_active = True
            self.slow_fall_duration_remaining = self.slow_fall_duration_total
            self.slow_fall_charges -= 1
            return True
        return False

    def update_slow_fall(self, delta_time: float) -> None:
        """
        Updates the duration of an active Slow Fall. Deactivates it if time runs out.

        Args:
            delta_time (float): The time elapsed (in seconds) since the last update.
                                Should typically be positive.
        """
        if delta_time < 0:
            # print("Warning: delta_time for update_slow_fall was negative.") # Or raise error
            delta_time = 0 # Prevent negative time from increasing duration

        if self.slow_fall_active:
            self.slow_fall_duration_remaining -= delta_time
            if self.slow_fall_duration_remaining <= 0:
                self.slow_fall_active = False
                self.slow_fall_duration_remaining = 0

    def get_slow_fall_status_dict(self) -> dict:
        """
        Returns a dictionary containing the current status of the Slow Fall ability.
        Useful for passing status to UI rendering functions.

        Returns:
            dict: A dictionary with keys 'charges', 'active', 'remaining',
                  'progress', 'threshold'.
        """
        return {
            'charges': self.slow_fall_charges,
            'active': self.slow_fall_active,
            'remaining': self.slow_fall_duration_remaining,
            'progress': self.slow_fall_recharge_progress,
            'threshold': self.slow_fall_recharge_threshold
        }
