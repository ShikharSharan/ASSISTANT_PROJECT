import logging
from datetime import datetime
from typing import List
from .errors import ValidationError
from .models import Task, MoneyEntry
from .storage_base import StorageBase
from .sqlite_storage import SQLiteStorage
from .validation import (
    MONEY_ENTRY_TYPES,
    normalize_money_entry_input,
    normalize_period,
    normalize_record_id,
    normalize_task_input,
)

logger = logging.getLogger(__name__)

# In future, you can switch this to CloudStorage(...) without touching other code
storage: StorageBase = SQLiteStorage()

class TaskManager:
    def list_pending_tasks(self) -> List[Task]:
        return storage.get_tasks(done=0)

    def list_completed_tasks(self) -> List[Task]:
        return storage.get_tasks(done=1)

    def add_task(self, title: str, description: str = "", priority: str = "Medium") -> Task:
        normalized_title, normalized_description, normalized_priority = normalize_task_input(
            title,
            description,
            priority,
        )
        task_id = storage.insert_task(normalized_title, normalized_description, normalized_priority)
        logger.info("Added task with id %s", task_id)
        return Task(
            id=task_id,
            title=normalized_title,
            description=normalized_description,
            date=datetime.now(),
            completed_at=None,
            priority=normalized_priority,
            done=False,
        )

    def mark_done(self, task_id: int) -> None:
        normalized_task_id = normalize_record_id(task_id, "Task")
        storage.mark_task_done(normalized_task_id)
        logger.info("Marked task %s as done", task_id)

class MoneyManager:
    def add_entry(self, entry_type: str, amount: float, note: str = "", person: str = "") -> MoneyEntry:
        normalized_type, normalized_amount, normalized_note, normalized_person = normalize_money_entry_input(
            entry_type,
            amount,
            note,
            person,
        )
        entry_id = storage.insert_money_entry(
            normalized_type,
            normalized_amount,
            normalized_note,
            normalized_person,
        )
        logger.info("Added money entry %s", entry_id)
        return MoneyEntry(
            id=entry_id,
            entry_type=normalized_type,
            amount=normalized_amount,
            date=datetime.now(),
            note=normalized_note,
            person=normalized_person,
        )

    def update_entry(self, entry_id: int, entry_type: str, amount: float, note: str = "", person: str = "") -> None:
        normalized_entry_id = normalize_record_id(entry_id, "Money entry")
        normalized_type, normalized_amount, normalized_note, normalized_person = normalize_money_entry_input(
            entry_type,
            amount,
            note,
            person,
        )
        storage.update_money_entry(
            normalized_entry_id,
            normalized_type,
            normalized_amount,
            normalized_note,
            normalized_person,
        )
        logger.info("Updated money entry %s", normalized_entry_id)

    def delete_entry(self, entry_id: int) -> None:
        normalized_entry_id = normalize_record_id(entry_id, "Money entry")
        storage.delete_money_entry(normalized_entry_id)
        logger.info("Deleted money entry %s", normalized_entry_id)

    def list_entries(
        self,
        year: int | None = None,
        month: int | None = None,
        entry_type: str | None = None,
    ) -> List[MoneyEntry]:
        normalized_year, normalized_month = normalize_period(year=year, month=month)
        if entry_type is not None and entry_type not in MONEY_ENTRY_TYPES:
            raise ValidationError("Money entry type is invalid.")
        return storage.get_money_entries(
            year=normalized_year,
            month=normalized_month,
            entry_type=entry_type,
        )

    def compute_summary(self, year: int | None = None, month: int | None = None):
        normalized_year, normalized_month = normalize_period(year=year, month=month)
        salary, expenses, emi, credit, owes_you = storage.get_money_summary(
            year=normalized_year,
            month=normalized_month,
        )
        return {
            "salary": salary,
            "expenses": expenses,
            "emi": emi,
            "credit": credit,
            "owes_you": owes_you,
            "net_balance": salary - expenses,
        }
