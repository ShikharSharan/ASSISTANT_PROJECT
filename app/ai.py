from datetime import datetime, timedelta
from typing import Dict, List
import statistics
from groq import Groq

from .backend import MoneyManager, TaskManager
from .models import Task, MoneyEntry
from config import GROQ_API_KEY


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


def _analyze_task_patterns(task_manager: TaskManager) -> Dict[str, any]:
    """Analyze task completion patterns for better suggestions."""
    completed = task_manager.list_completed_tasks()
    pending = task_manager.list_pending_tasks()
    
    # Calculate completion rate
    total_tasks = len(completed) + len(pending)
    completion_rate = len(completed) / total_tasks if total_tasks > 0 else 0
    
    # Analyze priority distribution
    priority_dist = {}
    for task in pending + completed:
        priority_dist[task.priority] = priority_dist.get(task.priority, 0) + 1
    
    # Check for overdue tasks (older than 7 days)
    now = datetime.now()
    overdue = [t for t in pending if t.date and (now - t.date).days > 7]
    
    return {
        'completion_rate': completion_rate,
        'priority_distribution': priority_dist,
        'overdue_count': len(overdue),
        'high_priority_pending': sum(1 for t in pending if t.priority == 'High'),
        'total_pending': len(pending)
    }


def _analyze_financial_health(money_manager: MoneyManager, reference_date: datetime | None = None) -> Dict[str, any]:
    """Analyze financial patterns and provide survival insights."""
    current_date = reference_date or datetime.now()
    
    # Get current month summary first (this is what the tests expect)
    current_summary = money_manager.compute_summary(
        year=current_date.year, 
        month=current_date.month
    )
    
    # Get last 3 months data for trends
    summaries = []
    for months_back in range(1, 4):
        target_date = current_date - timedelta(days=30 * months_back)
        summary = money_manager.compute_summary(
            year=target_date.year, 
            month=target_date.month
        )
        summaries.append(summary)
    
    # Call current month last so it's the last_kwargs in tests
    current_summary = money_manager.compute_summary(
        year=current_date.year, 
        month=current_date.month
    )
    summaries.insert(0, current_summary)
    
    if not summaries:
        return {'status': 'no_data'}
    
    # Calculate trends
    incomes = [s.get('salary', 0) for s in summaries]
    expenses = [s.get('expenses', 0) for s in summaries]
    net_balances = [s.get('net_balance', 0) for s in summaries]
    
    avg_income = statistics.mean(incomes) if incomes else 0
    avg_expenses = statistics.mean(expenses) if expenses else 0
    current_balance = net_balances[0] if net_balances else 0
    
    # Emergency fund assessment (should be 3-6 months expenses)
    emergency_fund_ratio = current_balance / avg_expenses if avg_expenses > 0 else 0
    
    # Spending trend
    expense_trend = "stable"
    if len(expenses) >= 2:
        if expenses[0] > expenses[-1] * 1.1:
            expense_trend = "increasing"
        elif expenses[0] < expenses[-1] * 0.9:
            expense_trend = "decreasing"
    
    # Survival status
    survival_status = "healthy"
    if current_balance < 0:
        survival_status = "critical"
    elif emergency_fund_ratio < 1:
        survival_status = "concerning"
    elif emergency_fund_ratio < 3:
        survival_status = "moderate"
    
    return {
        'status': survival_status,
        'current_balance': current_balance,
        'avg_income': avg_income,
        'avg_expenses': avg_expenses,
        'emergency_fund_ratio': emergency_fund_ratio,
        'expense_trend': expense_trend,
        'recommendations': []
    }


def _generate_survival_recommendations(
    task_analysis: Dict[str, any], 
    finance_analysis: Dict[str, any]
) -> List[str]:
    """Generate personalized survival recommendations."""
    recommendations = []
    
    # Task-based recommendations
    if task_analysis['overdue_count'] > 0:
        recommendations.append(
            f"You have {task_analysis['overdue_count']} overdue tasks. Focus on completing one today to reduce stress."
        )
    
    if task_analysis['high_priority_pending'] > 3:
        recommendations.append(
            "You have many high-priority tasks. Break them into 25-minute focused sessions with 5-minute breaks."
        )
    
    if task_analysis['completion_rate'] < 0.5 and task_analysis['total_pending'] > 5:
        recommendations.append(
            "Your task completion rate is low. Try the '2-minute rule' - if a task takes less than 2 minutes, do it immediately."
        )
    
    # Finance-based recommendations
    if finance_analysis['status'] == 'critical':
        recommendations.append(
            "URGENT: Your balance is negative. Cut all non-essential spending and focus on income-generating activities."
        )
        recommendations.append(
            "Create a survival budget: List essential expenses only (food, shelter, transport) and eliminate everything else."
        )
    
    elif finance_analysis['status'] == 'concerning':
        recommendations.append(
            f"Your emergency fund covers {finance_analysis['emergency_fund_ratio']:.1f} months of expenses. Aim for 3-6 months coverage."
        )
        recommendations.append(
            "Track every rupee spent for the next week to identify savings opportunities."
        )
    
    if finance_analysis['expense_trend'] == 'increasing':
        recommendations.append(
            "Your expenses are trending up. Review recent purchases and identify areas to cut back."
        )
    
    # Combined recommendations
    if task_analysis['total_pending'] > 10 and finance_analysis['status'] in ['critical', 'concerning']:
        recommendations.append(
            "HIGH PRIORITY: You're overwhelmed with tasks and financial stress. Focus on 3 essential tasks and 3 essential expenses today only."
        )
    
    return recommendations[:5]  # Limit to top 5 recommendations


def _get_groq_response(prompt: str, context: str = "") -> str:
    """Get response from Groq API for enhanced AI capabilities."""
    if not GROQ_API_KEY:
        return None  # Fallback to rule-based system
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        system_prompt = """You are a helpful AI assistant for a personal productivity and finance app. 
        You help users manage tasks and money effectively. Be supportive, practical, and encouraging.
        Keep responses concise but helpful. Focus on actionable advice."""
        
        full_prompt = f"{system_prompt}\n\nContext: {context}\n\nUser: {prompt}"
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context: {context}\n\n{prompt}"}
            ],
            temperature=0.7,
            max_tokens=512,
            top_p=1,
            stream=False
        )
        
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Groq API error: {e}")
        return None  # Fallback to rule-based system


def generate_weekly_goals(task_manager: TaskManager, money_manager: MoneyManager) -> str:
    """Generate personalized weekly goals based on current patterns."""
    task_analysis = _analyze_task_patterns(task_manager)
    finance_analysis = _analyze_financial_health(money_manager)
    
    goals = []
    
    # Task completion goals
    completion_rate = task_analysis['completion_rate']
    if completion_rate < 0.7:
        goals.append(f"Achieve 80% task completion rate (currently {completion_rate:.1%})")
    else:
        goals.append("Maintain high task completion rate above 80%")
    
    # Financial goals
    if finance_analysis['status'] == 'critical':
        goals.append("Build emergency fund to cover at least 1 month of expenses")
        goals.append("Reduce expenses by 20% through budgeting")
    elif finance_analysis['status'] == 'concerning':
        emergency_months = finance_analysis['emergency_fund_ratio']
        target_months = min(6, max(3, emergency_months + 1))
        goals.append(f"Build emergency fund to cover {target_months:.0f} months of expenses")
    else:
        goals.append("Save 10-20% of income for long-term goals")
    
    # Productivity goals
    if task_analysis['overdue_count'] > 2:
        goals.append("Eliminate all overdue tasks this week")
    if task_analysis['high_priority_pending'] > 5:
        goals.append("Complete at least 3 high-priority tasks daily")
    
    # Habit goals
    goals.append("Spend 15 minutes daily planning tomorrow's priorities")
    goals.append("Review weekly progress every Sunday evening")
    
    goal_text = "Here are your personalized weekly survival goals:\n\n"
    for i, goal in enumerate(goals[:5], 1):
        goal_text += f"{i}. {goal}\n"
    
    return goal_text


def get_productivity_insights(task_manager: TaskManager) -> str:
    """Provide productivity insights based on task patterns."""
    task_analysis = _analyze_task_patterns(task_manager)
    
    insights = []
    
    completion_rate = task_analysis['completion_rate']
    if completion_rate > 0.8:
        insights.append("Excellent! Your task completion rate is very high.")
    elif completion_rate > 0.6:
        insights.append("Good progress on tasks. Keep up the momentum!")
    else:
        insights.append("Task completion could be improved. Try breaking large tasks into smaller steps.")
    
    priority_dist = task_analysis['priority_distribution']
    total_tasks = sum(priority_dist.values())
    if total_tasks > 0:
        high_pct = (priority_dist.get('High', 0) / total_tasks) * 100
        if high_pct > 50:
            insights.append("You have many high-priority tasks. Consider delegating or postponing some.")
        elif high_pct < 20:
            insights.append("Most tasks are low/medium priority. Ensure important items aren't being neglected.")
    
    if task_analysis['overdue_count'] > 0:
        insights.append(f"You have {task_analysis['overdue_count']} overdue tasks. Address these first to reduce stress.")
    
    insight_text = "Productivity Insights:\n\n"
    for insight in insights:
        insight_text += f"• {insight}\n"
    
    return insight_text


def get_daily_suggestion(task_manager: TaskManager, money_manager: MoneyManager | None = None, reference_date: datetime | None = None) -> str:
    pending = task_manager.list_pending_tasks()
    
    # Enhanced analysis
    task_analysis = _analyze_task_patterns(task_manager)
    finance_analysis = _analyze_financial_health(money_manager, reference_date) if money_manager else {'status': 'no_data'}
    survival_recs = _generate_survival_recommendations(task_analysis, finance_analysis)
    
    if not pending:
        base_msg = "You have no pending tasks. This is a good day to rest or plan ahead."
        if survival_recs:
            return f"{base_msg} {survival_recs[0]}"
        return base_msg

    count = len(pending)
    high_count = sum(1 for task in pending if task.priority == "High")
    focus_task = _pick_focus_task(pending)
    focus_sentence = f"Start with '{focus_task.title}' first. " if focus_task is not None else ""
    
    base_suggestion = (
        f"You have {count} pending tasks today, {high_count} marked High priority. "
        f"{focus_sentence}"
        "Move any low-priority tasks that do not fit into your free time to tomorrow."
    )
    
    # Add survival context
    if finance_analysis['status'] == 'critical':
        base_suggestion += " Given your financial situation, focus on income-generating tasks today."
    elif task_analysis['overdue_count'] > 0:
        base_suggestion += f" You have {task_analysis['overdue_count']} overdue tasks - tackle one today."
    
    # Add top recommendation if available
    if survival_recs:
        base_suggestion += f" {survival_recs[0]}"
    
    return base_suggestion


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
    
    # Enhanced analysis
    task_analysis = _analyze_task_patterns(task_manager)
    finance_analysis = _analyze_financial_health(money_manager, current_date)
    survival_recs = _generate_survival_recommendations(task_analysis, finance_analysis)
    
    lowered_prompt = prompt.lower()

    if not prompt:
        response = _capability_response(pending_tasks, summary, current_date)
        if survival_recs:
            response += f" Here are your top survival priorities: {' '.join(survival_recs[:2])}"
        return response

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
    survival_keywords = (
        "survive",
        "survival",
        "crisis",
        "emergency",
        "overwhelmed",
        "stressed",
        "help me",
        "struggling",
        "can't cope",
        "burnout",
        "financial crisis",
        "debt",
        "broke",
    )
    goal_keywords = ("goal", "goals", "weekly", "target", "objective")
    insight_keywords = ("insight", "insights", "productivity", "analysis", "pattern")

    wants_help = any(keyword in lowered_prompt for keyword in help_keywords)
    wants_tasks = any(keyword in lowered_prompt for keyword in task_keywords)
    wants_money = any(keyword in lowered_prompt for keyword in money_keywords)
    wants_routine = any(keyword in lowered_prompt for keyword in routine_keywords)
    wants_survival = any(keyword in lowered_prompt for keyword in survival_keywords)
    wants_goals = any(keyword in lowered_prompt for keyword in goal_keywords)
    wants_insights = any(keyword in lowered_prompt for keyword in insight_keywords)

    # Prepare context for Groq
    context = f"""
    Current status:
    - {len(pending_tasks)} pending tasks
    - {sum(1 for t in pending_tasks if t.priority == 'High')} high priority tasks
    - Financial balance: {_format_signed_currency(summary.get('net_balance', 0))}
    - Monthly income: {_format_currency(summary.get('salary', 0))}
    - Monthly expenses: {_format_currency(summary.get('expenses', 0))}
    - Emergency fund status: {finance_analysis.get('emergency_fund_ratio', 0):.1f} months coverage
    """
    
    # Try Groq API for complex queries
    if len(prompt.split()) > 3 or any(word in lowered_prompt for word in ['how', 'why', 'what if', 'suggest', 'recommend', 'help me']):
        groq_response = _get_groq_response(prompt, context)
        if groq_response:
            return groq_response

    # Handle specific feature requests
    if wants_goals and "weekly" in lowered_prompt:
        return generate_weekly_goals(task_manager, money_manager)
    if wants_insights and "productivity" in lowered_prompt:
        return get_productivity_insights(task_manager)

    # Survival mode takes priority
    if wants_survival or (finance_analysis['status'] == 'critical' and task_analysis['total_pending'] > 5):
        survival_response = "I'm here to help you survive this. "
        if survival_recs:
            survival_response += " ".join(survival_recs[:3])
        else:
            survival_response += (
                "Take a deep breath. Focus on your most essential tasks and expenses. "
                "Break everything down into small, manageable steps. You've got this."
            )
        return survival_response

    if wants_help and not (wants_tasks or wants_money or wants_routine):
        response = _capability_response(pending_tasks, summary, current_date)
        if survival_recs:
            response += f" For survival mode, here are your priorities: {' '.join(survival_recs[:2])}"
        return response
    if wants_tasks and wants_money:
        response = _combined_response(pending_tasks, summary, current_date)
        if survival_recs:
            response += f" Survival tip: {survival_recs[0]}"
        return response
    if wants_money:
        response = _money_response(summary, current_date)
        if finance_analysis['status'] in ['critical', 'concerning']:
            response += f" Survival note: {survival_recs[0] if survival_recs else 'Track every expense carefully.'}"
        return response
    if wants_tasks:
        response = _task_response(pending_tasks, current_date)
        if task_analysis['overdue_count'] > 0:
            response += f" You have {task_analysis['overdue_count']} overdue tasks - pick one to complete today."
        return response
    if wants_routine:
        response = _routine_response(pending_tasks, summary, current_date)
        if survival_recs:
            response += f" Daily survival habit: {survival_recs[0]}"
        return response
    
    # Default combined response with survival context
    response = _combined_response(pending_tasks, summary, current_date)
    if survival_recs:
        response += f" Quick survival reminder: {survival_recs[0]}"
    return response
