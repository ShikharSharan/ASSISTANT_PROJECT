import logging
from datetime import datetime
from typing import List
from .models import Task, MoneyEntry
from .storage_base import StorageBase
from .sqlite_storage import SQLiteStorage

logger = logging.getLogger(__name__)

# In future, you can switch this to CloudStorage(...) without touching other code
storage: StorageBase = SQLiteStorage()

class TaskManager:
    def list_pending_tasks(self) -> List[Task]:
        return storage.get_tasks(done=0)

    def list_completed_tasks(self) -> List[Task]:
        return storage.get_tasks(done=1)

    def add_task(self, title: str, description: str = "", priority: str = "Medium") -> Task:
        task_id = storage.insert_task(title, description, priority)
        logger.info("Added task with id %s", task_id)
        return Task(
            id=task_id,
            title=title,
            description=description,
            date=datetime.now(),
            priority=priority,
            done=False,
        )

    def mark_done(self, task_id: int) -> None:
        storage.mark_task_done(task_id)
        logger.info("Marked task %s as done", task_id)

class MoneyManager:
    def add_entry(self, entry_type: str, amount: float, note: str = "", person: str = "") -> MoneyEntry:
        entry_id = storage.insert_money_entry(entry_type, amount, note, person)
        logger.info("Added money entry %s", entry_id)
        return MoneyEntry(
            id=entry_id,
            entry_type=entry_type,
            amount=amount,
            date=datetime.now(),
            note=note,
            person=person,
        )

    def list_entries(self) -> List[MoneyEntry]:
        return storage.get_money_entries()

    def compute_summary(self):
        salary, expenses, emi, credit, owes_you = storage.get_money_summary()
        return {
            "salary": salary,
            "expenses": expenses,
            "emi": emi,
            "credit": credit,
            "owes_you": owes_you,
        }