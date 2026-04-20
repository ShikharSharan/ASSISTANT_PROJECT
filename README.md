# Assistant Pro

Assistant Pro is a local PyQt desktop app for managing tasks, money entries, and lightweight AI-style daily guidance.

It currently includes:

- A home dashboard with task stats, focus suggestions, and AI nudges
- A dedicated tasks page for filtering and managing pending work
- A money page for tracking income, expenses, EMI, credit payments, and personal lending/borrowing
- A local assistant chat view that uses your saved task and money data to generate simple coaching responses
- SQLite-backed storage with AI-analysis-friendly lifecycle tables for both tasks and money

## Tech Stack

- Python 3.10+
- PyQt6
- SQLite
- Groq API (optional, for enhanced AI responses)
- `unittest` for tests

## Setup

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

### Optional: Groq AI Integration

For enhanced AI responses, you can integrate with Groq's API:

1. Get an API key from [Groq Console](https://console.groq.com/)
2. Create a `.env` file in the project root:
   ```
   GROQ_API_KEY=your_actual_api_key_here
   ```

The app will automatically use Groq for complex queries while falling back to the built-in AI for simple responses.

## Run The App

```bash
python3 main.py
```

You can also install it as a package and use the GUI entry point:

```bash
python3 -m pip install .
assistant-pro
```

## Run Tests

```bash
python3 -m unittest -q
```

## Project Layout

```text
assistant_project/
├── app/
│   ├── ai.py
│   ├── backend.py
│   ├── errors.py
│   ├── models.py
│   ├── sqlite_storage.py
│   ├── storage_base.py
│   ├── ui.py
│   └── validation.py
├── data/
│   └── assistant.db
├── tests/
├── config.py
├── logging_conf.py
├── main.py
├── requirements.txt
└── setup.py
```

## Storage Design

The app stores data locally in SQLite at `data/assistant.db`.

### Tasks

Task storage is lifecycle-based and analysis-ready:

- `task_core`: permanent task identity and normalized text
- `task_active`: ongoing tasks only
- `task_completed`: completed tasks only
- `task_events`: lifecycle history such as created/completed
- `task_analysis_view`, `task_daily_stats_view`: views intended to help future AI/reporting features

For safety, legacy task rows are preserved in `tasks_legacy` after migration.

Task schema reference:

```text
task_core
- id INTEGER PRIMARY KEY
- title_raw TEXT NOT NULL
- title_clean TEXT NOT NULL
- description_raw TEXT NOT NULL DEFAULT ''
- description_clean TEXT NOT NULL DEFAULT ''
- created_at TEXT NOT NULL
- updated_at TEXT NOT NULL
- dedup_key TEXT NOT NULL
- source TEXT NOT NULL DEFAULT 'app'
- project_name TEXT NOT NULL DEFAULT ''
- parent_task_id INTEGER NULL -> task_core.id

task_active
- task_id INTEGER PRIMARY KEY -> task_core.id
- priority TEXT NOT NULL CHECK Low|Medium|High
- status TEXT NOT NULL CHECK pending|in_progress|blocked
- due_at TEXT NULL
- scheduled_for TEXT NULL
- started_at TEXT NULL
- estimated_minutes INTEGER NULL
- energy_level TEXT NOT NULL CHECK low|medium|high
- context_name TEXT NOT NULL DEFAULT ''
- blocked_reason TEXT NOT NULL DEFAULT ''
- last_touched_at TEXT NOT NULL

task_completed
- task_id INTEGER PRIMARY KEY -> task_core.id
- priority TEXT NOT NULL CHECK Low|Medium|High
- status_when_completed TEXT NOT NULL CHECK pending|in_progress|blocked
- completed_at TEXT NOT NULL
- actual_minutes INTEGER NULL
- completion_reason TEXT NOT NULL DEFAULT 'done'
- completion_note TEXT NOT NULL DEFAULT ''

task_events
- id INTEGER PRIMARY KEY AUTOINCREMENT
- task_id INTEGER NOT NULL -> task_core.id
- event_type TEXT NOT NULL CHECK created|completed|reopened|updated|migrated
- event_at TEXT NOT NULL
- from_state TEXT NOT NULL DEFAULT ''
- to_state TEXT NOT NULL DEFAULT ''
- payload_json TEXT NOT NULL DEFAULT '{}'

tasks_legacy
- preserved backup of the old single-table task model after migration
```

Task analysis views:

- `task_analysis_view`: one AI-friendly row per task with raw/clean text, lifecycle stage, priority, scheduling fields, completion fields, and computed `age_days`
- `task_daily_stats_view`: per-day created/completed counts for trend analysis

### Money

The current money UI still uses the existing entry types:

- `Income`
- `Expense`
- `EMI`
- `Credit`
- `Given`
- `Taken`

Under the hood, money data is also normalized for future analysis:

- `money_entries`: UI-facing source rows
- `money_entry_kinds`: semantic meaning of each entry type
- `money_counterparties`: reusable people/entities
- `money_entry_facts`: normalized AI-friendly facts
- `money_analysis_view`, `money_monthly_breakdown_view`: analysis views

Money schema reference:

```text
money_entries
- id INTEGER PRIMARY KEY AUTOINCREMENT
- entry_type TEXT NOT NULL CHECK Income|Expense|EMI|Credit|Given|Taken
- amount REAL NOT NULL CHECK amount > 0
- date TEXT NOT NULL
- note TEXT NOT NULL DEFAULT ''
- person TEXT NOT NULL DEFAULT ''

money_entry_kinds
- key TEXT PRIMARY KEY
- display_name TEXT NOT NULL
- flow_direction TEXT NOT NULL CHECK inflow|outflow
- analysis_group TEXT NOT NULL CHECK income|expense|liability|loan
- counts_as_income INTEGER NOT NULL CHECK 0|1
- counts_as_expense INTEGER NOT NULL CHECK 0|1
- counts_as_emi INTEGER NOT NULL CHECK 0|1
- counts_as_credit INTEGER NOT NULL CHECK 0|1
- counts_as_receivable INTEGER NOT NULL CHECK 0|1
- counts_as_payable INTEGER NOT NULL CHECK 0|1
- counterparty_kind TEXT NOT NULL CHECK none|person|institution

money_counterparties
- id INTEGER PRIMARY KEY AUTOINCREMENT
- normalized_name TEXT NOT NULL
- display_name TEXT NOT NULL
- kind TEXT NOT NULL CHECK person|institution
- UNIQUE(normalized_name, kind)

money_entry_facts
- entry_id INTEGER PRIMARY KEY -> money_entries.id
- kind_key TEXT NOT NULL -> money_entry_kinds.key
- flow_direction TEXT NOT NULL CHECK inflow|outflow
- analysis_group TEXT NOT NULL CHECK income|expense|liability|loan
- occurred_at TEXT NOT NULL
- entered_at TEXT NOT NULL
- amount_minor INTEGER NOT NULL
- signed_amount_minor INTEGER NOT NULL
- currency_code TEXT NOT NULL DEFAULT 'INR'
- note_raw TEXT NOT NULL DEFAULT ''
- note_clean TEXT NOT NULL DEFAULT ''
- counterparty_id INTEGER NULL -> money_counterparties.id
- counterparty_name TEXT NOT NULL DEFAULT ''
- counterparty_kind TEXT NOT NULL CHECK none|person|institution
- month_key TEXT NOT NULL
```

Seeded money kind metadata:

```text
Income  -> inflow  | income    | counterparty none
Expense -> outflow | expense   | counterparty none
EMI     -> outflow | liability | counterparty institution
Credit  -> outflow | liability | counterparty institution
Given   -> outflow | loan      | counterparty person
Taken   -> inflow  | loan      | counterparty person
```

Money analysis views:

- `money_analysis_view`: one normalized row per entry with both source facts and analysis flags such as `counts_as_income`, `counts_as_expense`, `counts_as_emi`, and loan/payable markers
- `money_monthly_breakdown_view`: grouped monthly totals by money kind and analysis group

## Current Behavior Notes

- Duplicate pending tasks with the same title, description, and priority are blocked
- Existing data migrations happen automatically when the app starts
- Everything is local; there is no cloud sync or external AI API call in the current implementation

## Packaging

The package metadata is defined in `setup.py`, with a GUI entry point named `assistant-pro`.
