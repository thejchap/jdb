from typing import Tuple, TypeVar, Callable, Any, Dict, Optional

ID = int
Key = bytes
Value = bytes
Offset = int
Timestamp = int
IndexEntry = Tuple[Key, Offset]
T = TypeVar("T")
Comparator = Callable[[Any, T, T], int]
Returning = Dict[Key, Optional[Value]]
