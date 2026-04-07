from .backend import TaskManager

def get_daily_suggestion(task_manager: TaskManager) -> str:
    pending = task_manager.list_pending_tasks()
    if not pending:
        return "You have no pending tasks. This is a good day to rest or plan ahead."
    count = len(pending)
    high_count = sum(1 for t in pending if t.priority == "High")
    return (
        f"You have {count} pending tasks today, {high_count} marked High priority. "
        "Start with your highest priority tasks, and move any low-priority tasks that "
        "don’t fit into your free time to tomorrow."
    )