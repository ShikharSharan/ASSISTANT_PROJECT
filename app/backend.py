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
storage = None


class TaskManager:
    def __init__(self, storage: StorageBase | None = None, db_key: str = "") -> None:
        self.storage: StorageBase = storage if storage is not None else SQLiteStorage(db_key=db_key)

    def list_pending_tasks(self) -> List[Task]:
        return self.storage.get_tasks(done=0)

    def list_completed_tasks(self) -> List[Task]:
        return self.storage.get_tasks(done=1)

    def add_task(
        self,
        title: str,
        description: str = "",
        priority: str = "Medium",
        due_at: "datetime | None" = None,
        recurrence: str = "none",
        recurrence_end: "datetime | None" = None,
    ) -> Task:
        normalized_title, normalized_description, normalized_priority, normalized_recurrence = normalize_task_input(
            title, description, priority, recurrence
        )
        for existing_task in self.list_pending_tasks():
            if (
                existing_task.title == normalized_title
                and existing_task.description == normalized_description
                and existing_task.priority == normalized_priority
            ):
                raise ValidationError("This task is already in your pending list.")
        due_str = due_at.strftime("%Y-%m-%dT%H:%M:%S") if due_at else None
        end_str = recurrence_end.strftime("%Y-%m-%dT%H:%M:%S") if recurrence_end else None
        task_id = self.storage.insert_task(
            normalized_title, normalized_description, normalized_priority,
            due_at=due_str, recurrence=normalized_recurrence, recurrence_end=end_str,
        )
        logger.info("Added task with id %s", task_id)
        return Task(
            id=task_id,
            title=normalized_title,
            description=normalized_description,
            date=datetime.now(),
            completed_at=None,
            priority=normalized_priority,
            done=False,
            due_at=due_at,
            recurrence=normalized_recurrence,
            recurrence_end=recurrence_end,
        )

    def mark_done(self, task_id: int) -> None:
        normalized_task_id = normalize_record_id(task_id, "Task")
        self.storage.mark_task_done(normalized_task_id)
        logger.info("Marked task %s as done", task_id)


class MoneyManager:
    def __init__(self, storage: StorageBase | None = None, db_key: str = "") -> None:
        self.storage: StorageBase = storage if storage is not None else SQLiteStorage(db_key=db_key)

    def add_entry(self, entry_type: str, amount: float, note: str = "", person: str = "", category: str = "Uncategorised") -> MoneyEntry:
        normalized_type, normalized_amount, normalized_note, normalized_person, normalized_category = normalize_money_entry_input(
            entry_type, amount, note, person, category
        )
        entry_id = self.storage.insert_money_entry(
            normalized_type, normalized_amount, normalized_note, normalized_person, normalized_category
        )
        logger.info("Added money entry %s", entry_id)
        return MoneyEntry(
            id=entry_id,
            entry_type=normalized_type,
            amount=normalized_amount,
            date=datetime.now(),
            note=normalized_note,
            person=normalized_person,
            category=normalized_category,
        )

    def update_entry(self, entry_id: int, entry_type: str, amount: float, note: str = "", person: str = "") -> None:
        normalized_entry_id = normalize_record_id(entry_id, "Money entry")
        normalized_type, normalized_amount, normalized_note, normalized_person, _normalized_category = normalize_money_entry_input(
            entry_type,
            amount,
            note,
            person,
        )
        self.storage.update_money_entry(
            normalized_entry_id,
            normalized_type,
            normalized_amount,
            normalized_note,
            normalized_person,
        )
        logger.info("Updated money entry %s", normalized_entry_id)

    def delete_entry(self, entry_id: int) -> None:
        normalized_entry_id = normalize_record_id(entry_id, "Money entry")
        self.storage.delete_money_entry(normalized_entry_id)
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
        return self.storage.get_money_entries(
            year=normalized_year,
            month=normalized_month,
            entry_type=entry_type,
        )

    def compute_summary(self, year: int | None = None, month: int | None = None):
        normalized_year, normalized_month = normalize_period(year=year, month=month)
        salary, expenses, emi, credit, owes_you = self.storage.get_money_summary(
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


class BudgetManager:
    """Manage monthly budget goals and spending summaries."""

    def __init__(self, storage=None) -> None:
        self.storage = storage if storage is not None else globals()["storage"] or SQLiteStorage()

    def set_goal(self, category: str, monthly_limit: float, year: int, month: int):
        from .validation import normalize_budget_input
        category, monthly_limit = normalize_budget_input(category, monthly_limit)
        return self.storage.set_budget_goal(category, monthly_limit, year, month)

    def list_goals(self, year: int, month: int):
        return self.storage.get_budget_goals(year, month)

    def delete_goal(self, goal_id: int) -> None:
        from .validation import normalize_record_id
        self.storage.delete_budget_goal(normalize_record_id(goal_id, "Budget goal"))

    def spending_report(self, year: int, month: int):
        """Return per-category spending, enriched with budget caps."""
        return self.storage.get_spending_by_category(year, month)

    def over_budget_categories(self, year: int, month: int):
        return [s for s in self.spending_report(year, month) if s.over_budget]
