from abc import ABC, abstractmethod
from typing import List, Tuple
from datetime import datetime
from .models import Task, MoneyEntry

class StorageBase(ABC):
    @abstractmethod
    def insert_task(self, title: str, description: str, priority: str) -> int:
        ...

    @abstractmethod
    def get_tasks(self, done: int) -> List[Task]:
        ...

    @abstractmethod
    def mark_task_done(self, task_id: int) -> None:
        ...

    @abstractmethod
    def insert_money_entry(self, entry_type: str, amount: float, note: str, person: str) -> int:
        ...

    @abstractmethod
    def get_money_entries(self) -> List[MoneyEntry]:
        ...

    @abstractmethod
    def get_money_summary(self) -> Tuple[float, float, float, float, float]:
        ...