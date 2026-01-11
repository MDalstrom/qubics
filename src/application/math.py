import math
from dataclasses import dataclass
from typing import Union, overload


@dataclass
class Vector:
    x: float
    y: float

    def __add__(self, other: 'Vector') -> 'Vector':
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Vector') -> 'Vector':
        return Vector(self.x - other.x, self.y - other.y)

    @overload
    def __mul__(self, other: Union[float, int]) -> 'Vector': ...

    @overload
    def __mul__(self, other: 'Vector') -> float: ...

    def __mul__(self, other: Union[float, int, 'Vector']) -> Union['Vector', float]:
        if isinstance(other, (float, int)):
            return Vector(self.x * other, self.y * other)
        elif isinstance(other, Vector):
            return self.x * other.x + self.y * other.y
        return NotImplemented

    def __rmul__(self, other: Union[float, int]) -> 'Vector':
        if isinstance(other, (float, int)):
            return Vector(self.x * other, self.y * other)
        return NotImplemented

    def __truediv__(self, scalar: Union[float, int]) -> 'Vector':
        return Vector(self.x / scalar, self.y / scalar)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __neg__(self) -> 'Vector':
        return Vector(-self.x, -self.y)

    def dot(self, other: 'Vector') -> float:
        return self.x * other.x + self.y * other.y

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)

    def length_squared(self) -> float:
        return self.x * self.x + self.y * self.y

    def normalized(self) -> 'Vector':
        length = self.length()
        if length == 0:
            return Vector(0, 0)
        return Vector(self.x / length, self.y / length)

    def scale(self, scalar: float) -> 'Vector':
        return Vector(self.x * scalar, self.y * scalar)

    def add(self, other: 'Vector') -> 'Vector':
        return Vector(self.x + other.x, self.y + other.y)

    def subtract(self, other: 'Vector') -> 'Vector':
        return Vector(self.x - other.x, self.y - other.y)

    def round(self) -> tuple[int, int]:
        return int(self.x), int(self.y)


class Matrix:
    def __init__(self, data: list[list[float]]):
        self.data = [row[:] for row in data]
        self.rows = len(data)
        self.cols = len(data[0]) if data else 0

    @staticmethod
    def identity(size: int = 3) -> 'Matrix':
        data = [[1.0 if i == j else 0.0 for j in range(size)] for i in range(size)]
        return Matrix(data)

    @staticmethod
    def translation(x: float, y: float) -> 'Matrix':
        return Matrix([[1.0, 0.0, x], [0.0, 1.0, y], [0.0, 0.0, 1.0]])

    @staticmethod
    def rotation(angle: float) -> 'Matrix':
        c = math.cos(angle)
        s = math.sin(angle)
        return Matrix([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])

    @staticmethod
    def transform(x: float, y: float, angle: float) -> 'Matrix':
        c = math.cos(angle)
        s = math.sin(angle)
        return Matrix([[c, -s, x], [s, c, y], [0.0, 0.0, 1.0]])

    def __getitem__(self, key: tuple[int, int]) -> float:
        row, col = key
        return self.data[row][col]

    def __setitem__(self, key: tuple[int, int], value: float) -> None:
        row, col = key
        self.data[row][col] = value

    @overload
    def __matmul__(self, other: 'Matrix') -> 'Matrix': ...

    @overload
    def __matmul__(self, other: Vector) -> Vector: ...

    def __matmul__(self, other: Union['Matrix', Vector]) -> Union['Matrix', Vector]:
        if isinstance(other, Vector):
            if self.cols != 3:
                raise ValueError("Matrix must have 3 columns for Vector transformation")
            x = self.data[0][0] * other.x + self.data[0][1] * other.y + self.data[0][2]
            y = self.data[1][0] * other.x + self.data[1][1] * other.y + self.data[1][2]
            return Vector(x, y)
        elif isinstance(other, Matrix):
            if self.cols != other.rows:
                raise ValueError("Matrix dimensions incompatible for multiplication")
            result = [[0.0 for _ in range(other.cols)] for _ in range(self.rows)]
            for i in range(self.rows):
                for j in range(other.cols):
                    for k in range(self.cols):
                        result[i][j] += self.data[i][k] * other.data[k][j]
            return Matrix(result)
        return NotImplemented

    def __mul__(self, scalar: Union[float, int]) -> 'Matrix':
        result = [[self.data[i][j] * scalar for j in range(self.cols)] for i in range(self.rows)]
        return Matrix(result)

    def __rmul__(self, scalar: Union[float, int]) -> 'Matrix':
        return self.__mul__(scalar)

    def __add__(self, other: 'Matrix') -> 'Matrix':
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError("Matrix dimensions must match for addition")
        result = [[self.data[i][j] + other.data[i][j] for j in range(self.cols)] for i in range(self.rows)]
        return Matrix(result)

    def copy(self) -> 'Matrix':
        return Matrix(self.data)

    def inverse(self) -> 'Matrix':
        if self.rows != 3 or self.cols != 3:
            raise ValueError("Only 3x3 matrices supported for inversion")
        
        a = self.data
        det = (a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1]) -
               a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0]) +
               a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0]))
        
        if abs(det) < 1e-10:
            raise ValueError("Matrix is singular and cannot be inverted")
        
        inv_det = 1.0 / det
        result = [
            [
                (a[1][1] * a[2][2] - a[1][2] * a[2][1]) * inv_det,
                (a[0][2] * a[2][1] - a[0][1] * a[2][2]) * inv_det,
                (a[0][1] * a[1][2] - a[0][2] * a[1][1]) * inv_det
            ],
            [
                (a[1][2] * a[2][0] - a[1][0] * a[2][2]) * inv_det,
                (a[0][0] * a[2][2] - a[0][2] * a[2][0]) * inv_det,
                (a[0][2] * a[1][0] - a[0][0] * a[1][2]) * inv_det
            ],
            [
                (a[1][0] * a[2][1] - a[1][1] * a[2][0]) * inv_det,
                (a[0][1] * a[2][0] - a[0][0] * a[2][1]) * inv_det,
                (a[0][0] * a[1][1] - a[0][1] * a[1][0]) * inv_det
            ]
        ]
        return Matrix(result)
