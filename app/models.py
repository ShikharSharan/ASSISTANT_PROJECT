from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Task:
    id: int
    title: str
    description: str = ""
    date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    time: Optional[datetime] = None
    priority: str = "Medium"
    done: bool = False

@dataclass
class MoneyEntry:
    id: int
    entry_type: str
    amount: float
    date: datetime
    note: str = ""
    person: str = ""
