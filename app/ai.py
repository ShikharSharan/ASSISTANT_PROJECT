from datetime import datetime

from .backend import MoneyManager, TaskManager
from .models import Task


def _priority_rank(priority: str) -> int:
    return {
        "High": 0,
        "Medium": 1,
        "Low": 2,
    }.get(priority, 3)


def _pick_focus_task(tasks: list[Task]) -> Task | None:
    if not tasks:
        return None
    return min(
        tasks,
        key=lambda task: (
            _priority_rank(task.priority),
            task.date or datetime.max,
            task.id,
        ),
    )


def _format_currency(value: float) -> str:
    return f"Rs {int(round(value)):,}"


def _format_signed_currency(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}Rs {abs(int(round(value))):,}"


def _format_month_label(moment: datetime) -> str:
    return moment.strftime("%B %Y")


def _summarize_remaining_tasks(tasks: list[Task], excluded_task_id: int | None = None) -> str:
    remaining = [
        task.title
        for task in sorted(
            tasks,
            key=lambda task: (
                _priority_rank(task.priority),
                task.date or datetime.max,
                task.id,
            ),
        )
        if task.id != excluded_task_id
    ]
    if not remaining:
        return ""
    if len(remaining) == 1:
        return remaining[0]
    if len(remaining) == 2:
        return f"{remaining[0]} and {remaining[1]}"
    return f"{remaining[0]}, {remaining[1]}, and {remaining[2]}"


def get_daily_suggestion(task_manager: TaskManager) -> str:
    pending = task_manager.list_pending_tasks()
    if not pending:
        return "You have no pending tasks. This is a good day to rest or plan ahead."

    count = len(pending)
    high_count = sum(1 for task in pending if task.priority == "High")
    focus_task = _pick_focus_task(pending)
    focus_sentence = f"Start with '{focus_task.title}' first. " if focus_task is not None else ""
    return (
        f"You have {count} pending tasks today, {high_count} marked High priority. "
        f"{focus_sentence}"
        "Move any low-priority tasks that do not fit into your free time to tomorrow."
    )


def _task_response(pending_tasks: list[Task], reference_date: datetime) -> str:
    if not pending_tasks:
        return (
            "Your task list is clear right now. Use this window to capture one meaningful next step, "
            f"review your money entries for {_format_month_label(reference_date)}, and set a light plan "
            "for tomorrow."
        )

    focus_task = _pick_focus_task(pending_tasks)
    high_priority_count = sum(1 for task in pending_tasks if task.priority == "High")
    remaining_titles = _summarize_remaining_tasks(pending_tasks, focus_task.id if focus_task else None)
    follow_up_sentence = (
        f"After that, batch {remaining_titles} into one shorter admin block."
        if remaining_titles
        else "After that, do a quick review so tomorrow starts clean."
    )
    return (
        f"Start with '{focus_task.title}' first. You have {len(pending_tasks)} pending tasks and "
        f"{high_priority_count} marked High priority. Give it one protected 45-minute focus block, "
        f"then take a short reset. {follow_up_sentence}"
    )


def _money_response(summary: dict[str, float], reference_date: datetime) -> str:
    month_label = _format_month_label(reference_date)
    if not any(summary.values()):
        return (
            f"There are no money entries saved for {month_label} yet. Add income, expenses, EMI, or "
            "credit items first, then I can help you spot patterns and next steps."
        )

    net_balance = summary["net_balance"]
    net_text = _format_signed_currency(net_balance) if net_balance < 0 else _format_currency(net_balance)
    base_response = (
        f"For {month_label}, your income is {_format_currency(summary['salary'])} and your tracked "
        f"outflow is {_format_currency(summary['expenses'])}, so your current net balance is {net_text}. "
        f"That includes {_format_currency(summary['emi'])} in EMI and "
        f"{_format_currency(summary['credit'])} in credit payments."
    )

    follow_up_parts = []
    if summary["owes_you"] > 0:
        follow_up_parts.append(
            f"People owe you {_format_currency(summary['owes_you'])}, so a gentle follow-up could improve your buffer."
        )
    if net_balance < 0:
        follow_up_parts.append(
            "Pause non-essential spending for now and review the biggest recent expense entries first."
        )
    else:
        follow_up_parts.append(
            "Keep logging spending as it happens so this month stays accurate and easier to manage."
        )
    return f"{base_response} {' '.join(follow_up_parts)}"


def _routine_response(pending_tasks: list[Task], summary: dict[str, float], reference_date: datetime) -> str:
    if pending_tasks:
        focus_task = _pick_focus_task(pending_tasks)
        return (
            f"Use a simple rhythm today: start with '{focus_task.title}' in one focused block, move to a "
            "short admin block for small tasks, then do a 10-minute reset. End the day by reviewing your "
            f"{_format_month_label(reference_date)} money entries and choosing tomorrow's first task."
        )

    if any(summary.values()):
        return (
            "Keep today light but structured: do a short planning session, one personal errand, and a quick "
            "money review so the rest of the week stays calm."
        )

    return (
        "A productive day does not need to feel crowded. Try one planning block, one personal reset, and a "
        "short shutdown note so tomorrow begins with clarity."
    )


def _combined_response(
    pending_tasks: list[Task],
    summary: dict[str, float],
    reference_date: datetime,
) -> str:
    if pending_tasks:
        focus_task = _pick_focus_task(pending_tasks)
        task_sentence = (
            f"You have {len(pending_tasks)} pending tasks, so anchor the day around '{focus_task.title}' first."
        )
    else:
        task_sentence = "Your task list is clear right now, so keep the day light and intentional."

    if any(summary.values()):
        month_label = _format_month_label(reference_date)
        net_balance = summary["net_balance"]
        net_text = _format_signed_currency(net_balance) if net_balance < 0 else _format_currency(net_balance)
        money_sentence = (
            f"For {month_label}, your current net balance is {net_text}. "
            "Finish one real task before opening distractions, then log any missing money entries so both boards stay honest."
        )
    else:
        money_sentence = (
            "You have not logged money entries for this month yet, so add the basics after your main task to keep the picture complete."
        )
    return f"{task_sentence} {money_sentence}"


def _capability_response(
    pending_tasks: list[Task],
    summary: dict[str, float],
    reference_date: datetime,
) -> str:
    net_balance = summary["net_balance"]
    net_text = _format_signed_currency(net_balance) if net_balance < 0 else _format_currency(net_balance)
    return (
        "I can help you prioritize tasks, plan a productive day, review your money patterns, and suggest "
        f"simple daily routines. Right now you have {len(pending_tasks)} pending tasks and a net balance of "
        f"{net_text} for {_format_month_label(reference_date)}. Try asking what to focus on, how your money "
        "looks, or how to plan your evening."
    )


def get_chat_response(
    message: str,
    task_manager: TaskManager,
    money_manager: MoneyManager,
    reference_date: datetime | None = None,
) -> str:
    prompt = " ".join(message.strip().split())
    current_date = reference_date or datetime.now()
    pending_tasks = task_manager.list_pending_tasks()
    summary = money_manager.compute_summary(year=current_date.year, month=current_date.month)
    lowered_prompt = prompt.lower()

    if not prompt:
        return _capability_response(pending_tasks, summary, current_date)

    help_keywords = ("help", "what can you do", "how can you help", "hello", "hi")
    task_keywords = (
        "task",
        "focus",
        "priority",
        "priorit",
        "plan",
        "work",
        "productive",
        "todo",
        "to do",
    )
    money_keywords = (
        "money",
        "budget",
        "expense",
        "spend",
        "salary",
        "income",
        "emi",
        "credit",
        "cash",
        "balance",
        "loan",
    )
    routine_keywords = (
        "routine",
        "daily life",
        "habit",
        "morning",
        "evening",
        "day",
        "rest",
        "break",
    )

    wants_help = any(keyword in lowered_prompt for keyword in help_keywords)
    wants_tasks = any(keyword in lowered_prompt for keyword in task_keywords)
    wants_money = any(keyword in lowered_prompt for keyword in money_keywords)
    wants_routine = any(keyword in lowered_prompt for keyword in routine_keywords)

    if wants_help and not (wants_tasks or wants_money or wants_routine):
        return _capability_response(pending_tasks, summary, current_date)
    if wants_tasks and wants_money:
        return _combined_response(pending_tasks, summary, current_date)
    if wants_money:
        return _money_response(summary, current_date)
    if wants_tasks:
        return _task_response(pending_tasks, current_date)
    if wants_routine:
        return _routine_response(pending_tasks, summary, current_date)
    return _combined_response(pending_tasks, summary, current_date)
