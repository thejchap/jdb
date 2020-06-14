from typing import Tuple, Dict, Optional

ID = int
Key = bytes
Value = bytes
Offset = int
Timestamp = int
IndexEntry = Tuple[Key, Offset]
Returning = Dict[Key, Optional[Value]]
