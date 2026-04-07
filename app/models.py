from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Task:
    id: int
    title: str
    description: str = ""
    date: Optional[datetime] = None
    time: Optional[datetime] = None  # we can refine later
    priority: str = "Medium"
    done: bool = False

@dataclass
class MoneyEntry:
    id: int
    entry_type: str      # "Income", "Expense", "EMI", "Credit", "Given", "Taken"
    amount: float
    date: datetime
    note: str = ""
    person: str = ""