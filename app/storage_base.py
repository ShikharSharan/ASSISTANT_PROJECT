from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from .models import Task, MoneyEntry, BudgetGoal, SpendingSummary


class StorageBase(ABC):
    # ── Tasks ─────────────────────────────────────────────────────────────
    @abstractmethod
    def insert_task(self, title: str, description: str, priority: str,
                    due_at: Optional[str] = None, recurrence: str = "none",
                    recurrence_end: Optional[str] = None) -> int: ...

    @abstractmethod
    def get_tasks(self, done: int) -> List[Task]: ...

    @abstractmethod
    def mark_task_done(self, task_id: int) -> None: ...

    # ── Money entries ──────────────────────────────────────────────────────
    @abstractmethod
    def insert_money_entry(self, entry_type: str, amount: float, note: str,
                           person: str, category: str = "Uncategorised") -> int: ...

    @abstractmethod
    def update_money_entry(self, entry_id: int, entry_type: str, amount: float,
                           note: str, person: str,
                           category: str = "Uncategorised") -> None: ...

    @abstractmethod
    def delete_money_entry(self, entry_id: int) -> None: ...

    @abstractmethod
    def get_money_entries(self, year: Optional[int] = None,
                          month: Optional[int] = None,
                          entry_type: Optional[str] = None) -> List[MoneyEntry]: ...

    @abstractmethod
    def get_money_summary(self, year: Optional[int] = None,
                          month: Optional[int] = None) -> Tuple[float, float, float, float, float]: ...

    # ── Budget goals (NEW) ─────────────────────────────────────────────────
    @abstractmethod
    def set_budget_goal(self, category: str, monthly_limit: float,
                        year: int, month: int) -> int: ...

    @abstractmethod
    def get_budget_goals(self, year: int, month: int) -> List[BudgetGoal]: ...

    @abstractmethod
    def delete_budget_goal(self, goal_id: int) -> None: ...

    @abstractmethod
    def get_spending_by_category(self, year: int, month: int) -> List[SpendingSummary]: ...
