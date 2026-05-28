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
    due_at: Optional[datetime] = None          # NEW: deadline
    recurrence: str = "none"                   # NEW: none|daily|weekly|monthly
    recurrence_end: Optional[datetime] = None  # NEW: stop repeating after


@dataclass
class MoneyEntry:
    id: int
    entry_type: str
    amount: float
    date: datetime
    note: str = ""
    person: str = ""
    category: str = "Uncategorised"  # NEW: spending category


@dataclass
class BudgetGoal:
    """Monthly spending cap per category."""
    id: int
    category: str
    monthly_limit: float
    year: int
    month: int


@dataclass
class SpendingSummary:
    """Category-level report for a given month."""
    category: str
    total_spent: float
    monthly_limit: Optional[float] = None

    @property
    def over_budget(self) -> bool:
        return self.monthly_limit is not None and self.total_spent > self.monthly_limit

    @property
    def remaining(self) -> Optional[float]:
        if self.monthly_limit is None:
            return None
        return max(0.0, self.monthly_limit - self.total_spent)
