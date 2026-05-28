from math import isfinite
from typing import Optional
from .errors import ValidationError

TASK_PRIORITIES = ("Low", "Medium", "High")
MONEY_ENTRY_TYPES = ("Income", "Expense", "EMI", "Credit", "Given", "Taken")
RECURRENCE_OPTIONS = ("none", "daily", "weekly", "monthly")

SPENDING_CATEGORIES = (
    "Uncategorised",
    "Food & Dining",
    "Transport",
    "Housing",
    "Utilities",
    "Health",
    "Entertainment",
    "Shopping",
    "Education",
    "EMI & Loans",
    "Savings",
    "Other",
)


def normalize_task_input(
    title: str,
    description: str = "",
    priority: str = "Medium",
    recurrence: str = "none",
) -> tuple:
    normalized_title = " ".join((title or "").split())
    normalized_description = (description or "").strip()
    if not normalized_title:
        raise ValidationError("Task title cannot be empty.")
    if priority not in TASK_PRIORITIES:
        raise ValidationError("Task priority must be Low, Medium, or High.")
    if recurrence not in RECURRENCE_OPTIONS:
        raise ValidationError("Recurrence must be none, daily, weekly, or monthly.")
    return normalized_title, normalized_description, priority, recurrence


def normalize_money_entry_input(
    entry_type: str,
    amount: float,
    note: str = "",
    person: str = "",
    category: str = "Uncategorised",
) -> tuple:
    normalized_note = (note or "").strip()
    normalized_person = (person or "").strip()
    normalized_category = (category or "Uncategorised").strip()
    if entry_type not in MONEY_ENTRY_TYPES:
        raise ValidationError("Money entry type is invalid.")
    if normalized_category not in SPENDING_CATEGORIES:
        normalized_category = "Uncategorised"
    try:
        normalized_amount = float(amount)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Amount must be a valid number.") from exc
    if not isfinite(normalized_amount) or normalized_amount <= 0:
        raise ValidationError("Amount must be greater than zero.")
    if entry_type in {"Given", "Taken"} and not normalized_person:
        raise ValidationError("Person is required for Given and Taken entries.")
    return entry_type, normalized_amount, normalized_note, normalized_person, normalized_category


def normalize_record_id(record_id: int, label: str) -> int:
    if not isinstance(record_id, int) or isinstance(record_id, bool) or record_id <= 0:
        raise ValidationError(f"{label} id must be a positive integer.")
    return record_id


def normalize_period(
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> tuple:
    if year is None and month is None:
        return None, None
    if year is None or month is None:
        raise ValidationError("Year and month must be provided together.")
    if not isinstance(year, int) or isinstance(year, bool) or year <= 0:
        raise ValidationError("Year must be a positive integer.")
    if not isinstance(month, int) or isinstance(month, bool) or month < 1 or month > 12:
        raise ValidationError("Month must be between 1 and 12.")
    return year, month


def normalize_budget_input(category: str, monthly_limit: float) -> tuple:
    if category not in SPENDING_CATEGORIES:
        raise ValidationError(f"Category must be one of: {', '.join(SPENDING_CATEGORIES)}")
    try:
        limit = float(monthly_limit)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Budget limit must be a valid number.") from exc
    if not isfinite(limit) or limit <= 0:
        raise ValidationError("Budget limit must be greater than zero.")
    return category, limit
