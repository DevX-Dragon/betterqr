from abc import ABC, abstractmethod
from typing import List, Tuple

class BaseRenderer(ABC):
    """Abstract base class for all BetterQR rendering backends."""
    
    def __init__(self, matrix: List[List[bool]], box_size: int = 10, border: int = 4):
        self.matrix = matrix
        self.matrix_size = len(matrix)
        self.box_size = box_size
        self.border = border
        self.pixel_size = (self.matrix_size + (border * 2)) * box_size

    @abstractmethod
    def draw(self, fill_color: str, back_color: str, module_shape: str) -> bytes:
        """Draws the QR code and returns the raw bytes or file stream."""
        pass