import copy

class Block:
    """
    Represents a Tetris block (tetromino).

    Attributes:
        shape_name (str): The name of the shape (e.g., "L", "I"). Used for cloning.
        shape (list[list[int]]): A 2D list representing the block's current matrix form.
        color (str): The color of the block (currently a string, e.g., "blue").
        x (int): The x-coordinate of the block's top-left corner on the game board.
        y (int): The y-coordinate of the block's top-left corner on the game board.
    """
    SHAPES = {
        "I": [[1, 1, 1, 1]],
        "L": [[1, 0, 0], [1, 1, 1]],
        "J": [[0, 0, 1], [1, 1, 1]],
        "T": [[0, 1, 0], [1, 1, 1]],
        "O": [[1, 1], [1, 1]],
        "S": [[0, 1, 1], [1, 1, 0]],
        "Z": [[1, 1, 0], [0, 1, 1]],
    }
    COLORS = { # Basic colors, could be expanded to more specific color codes or objects
        "I": "cyan",
        "L": "orange",
        "J": "blue",
        "T": "purple",
        "O": "yellow",
        "S": "green",
        "Z": "red",
    }

    def __init__(self, shape_name: str, x: int = 0, y: int = 0):
        """
        Initializes a Block.

        Args:
            shape_name (str): The key for the desired shape in SHAPES and COLORS.
            x (int): Initial x-coordinate on the board.
            y (int): Initial y-coordinate on the board.
        """
        if shape_name not in self.SHAPES:
            raise ValueError(f"Unknown shape_name: {shape_name}")

        self.shape_name = shape_name
        self.shape = copy.deepcopy(self.SHAPES[shape_name]) # Ensure original SHAPES are not modified
        self.color = self.COLORS[shape_name]
        self.x = x
        self.y = y

    def rotate(self) -> None:
        """
        Rotates the block's shape matrix 90 degrees clockwise.
        The rotation is performed by transposing the matrix and then reversing each row.
        """
        # Transpose the matrix (rows become columns, columns become rows)
        # Example: [[1,2,3],[4,5,6]] -> [[1,4],[2,5],[3,6]]
        transposed_shape = [list(row) for row in zip(*self.shape)]

        # Reverse each row to achieve clockwise rotation
        # Example: [[1,4],[2,5],[3,6]] -> [[4,1],[5,2],[6,3]] (if original was landscape)
        self.shape = [row[::-1] for row in transposed_shape]

    def move(self, dx: int, dy: int) -> None:
        """
        Updates the block's x and y position by dx and dy respectively.

        Args:
            dx (int): Change in x-coordinate.
            dy (int): Change in y-coordinate.
        """
        self.x += dx
        self.y += dy

    def clone(self) -> 'Block':
        """
        Creates and returns a deep copy of this block instance.
        This is useful for testing potential moves or rotations without
        modifying the original block.

        Returns:
            Block: A new Block instance with the same properties as the original.
        """
        # Create a new instance using the stored shape_name, which sets initial shape and color
        new_block = Block(self.shape_name, x=self.x, y=self.y)

        # Crucially, override the shape with a deep copy of the current block's shape,
        # as it might have been rotated from its original state.
        new_block.shape = copy.deepcopy(self.shape)
        # Color is already set by the constructor based on shape_name, so no need to set it again.
        return new_block

    def get_shape_matrix(self) -> list[list[int]]:
        """
        Returns the block's current shape matrix.

        Returns:
            list[list[int]]: The 2D list representing the block's structure.
        """
        return self.shape
