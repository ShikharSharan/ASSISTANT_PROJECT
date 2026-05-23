import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
from .errors import AssistantDataError, RecordNotFoundError, ValidationError
from .storage_base import StorageBase
from .models import Task, MoneyEntry
from .validation import (
    MONEY_ENTRY_TYPES,
    normalize_money_entry_input,
    normalize_period,
    normalize_record_id,
    normalize_task_input,
)
from config import DB_PATH

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

MONEY_ENTRY_KIND_ROWS = (
    ("Income", "Income", "inflow", "income", 1, 0, 0, 0, 0, 0, "none"),
    ("Expense", "Expense", "outflow", "expense", 0, 1, 0, 0, 0, 0, "none"),
    ("EMI", "EMI", "outflow", "liability", 0, 1, 1, 0, 0, 0, "institution"),
    ("Credit", "Credit", "outflow", "liability", 0, 1, 0, 1, 0, 0, "institution"),
    ("Given", "Given", "outflow", "loan", 0, 0, 0, 0, 1, 0, "person"),
    ("Taken", "Taken", "inflow", "loan", 0, 0, 0, 0, 0, 1, "person"),
)

class SQLiteStorage(StorageBase):
    def __init__(self):
        self.db_path = Path(DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, timeout=5.0)
        self.conn.row_factory = sqlite3.Row
        self._configure_connection()
        self._init_db()

    def _configure_connection(self):
        self.conn.execute("PRAGMA busy_timeout = 5000")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA foreign_keys = ON")

    def _init_db(self):
        try:
            with self.conn:
                cur = self.conn.cursor()
                existing_tables = {
                    row["name"]
                    for row in cur.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    ).fetchall()
                }
                if "tasks" in existing_tables and "tasks_legacy" not in existing_tables:
                    legacy_columns = {
                        row["name"]
                        for row in cur.execute("PRAGMA table_info(tasks)").fetchall()
                    }
                    if "completed_at" not in legacy_columns:
                        cur.execute("ALTER TABLE tasks ADD COLUMN completed_at TEXT")
                    cur.execute("ALTER TABLE tasks RENAME TO tasks_legacy")
                    existing_tables.remove("tasks")
                    existing_tables.add("tasks_legacy")
                elif "tasks_legacy" in existing_tables:
                    legacy_columns = {
                        row["name"]
                        for row in cur.execute("PRAGMA table_info(tasks_legacy)").fetchall()
                    }
                    if "completed_at" not in legacy_columns:
                        cur.execute("ALTER TABLE tasks_legacy ADD COLUMN completed_at TEXT")

                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS task_core (
                        id INTEGER PRIMARY KEY,
                        title_raw TEXT NOT NULL CHECK (length(trim(title_raw)) > 0),
                        title_clean TEXT NOT NULL,
                        description_raw TEXT NOT NULL DEFAULT '',
                        description_clean TEXT NOT NULL DEFAULT '',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        dedup_key TEXT NOT NULL,
                        source TEXT NOT NULL DEFAULT 'app',
                        project_name TEXT NOT NULL DEFAULT '',
                        parent_task_id INTEGER,
                        FOREIGN KEY (parent_task_id) REFERENCES task_core(id)
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS task_active (
                        task_id INTEGER PRIMARY KEY,
                        priority TEXT NOT NULL DEFAULT 'Medium'
                            CHECK (priority IN ('Low', 'Medium', 'High')),
                        status TEXT NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending', 'in_progress', 'blocked')),
                        due_at TEXT,
                        scheduled_for TEXT,
                        started_at TEXT,
                        estimated_minutes INTEGER,
                        energy_level TEXT NOT NULL DEFAULT 'medium'
                            CHECK (energy_level IN ('low', 'medium', 'high')),
                        context_name TEXT NOT NULL DEFAULT '',
                        blocked_reason TEXT NOT NULL DEFAULT '',
                        last_touched_at TEXT NOT NULL,
                        FOREIGN KEY (task_id) REFERENCES task_core(id) ON DELETE CASCADE
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS task_completed (
                        task_id INTEGER PRIMARY KEY,
                        priority TEXT NOT NULL DEFAULT 'Medium'
                            CHECK (priority IN ('Low', 'Medium', 'High')),
                        status_when_completed TEXT NOT NULL DEFAULT 'pending'
                            CHECK (status_when_completed IN ('pending', 'in_progress', 'blocked')),
                        completed_at TEXT NOT NULL,
                        actual_minutes INTEGER,
                        completion_reason TEXT NOT NULL DEFAULT 'done',
                        completion_note TEXT NOT NULL DEFAULT '',
                        FOREIGN KEY (task_id) REFERENCES task_core(id) ON DELETE CASCADE
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS task_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id INTEGER NOT NULL,
                        event_type TEXT NOT NULL
                            CHECK (event_type IN ('created', 'completed', 'reopened', 'updated', 'migrated')),
                        event_at TEXT NOT NULL,
                        from_state TEXT NOT NULL DEFAULT '',
                        to_state TEXT NOT NULL DEFAULT '',
                        payload_json TEXT NOT NULL DEFAULT '{}',
                        FOREIGN KEY (task_id) REFERENCES task_core(id) ON DELETE CASCADE
                    );
                    """
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_task_core_created_at "
                    "ON task_core (created_at DESC, id DESC)"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_task_core_dedup_key "
                    "ON task_core (dedup_key)"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_task_active_priority_touch "
                    "ON task_active (priority, last_touched_at DESC, task_id DESC)"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_task_completed_completed_at "
                    "ON task_completed (completed_at DESC, task_id DESC)"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_task_events_task_time "
                    "ON task_events (task_id, event_at DESC, id DESC)"
                )
                self._create_task_analysis_views(cur)
                self._backfill_task_lifecycle(cur)
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS money_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entry_type TEXT NOT NULL
                            CHECK (entry_type IN ('Income', 'Expense', 'EMI', 'Credit', 'Given', 'Taken')),
                        amount REAL NOT NULL CHECK (amount > 0),
                        date TEXT NOT NULL,
                        note TEXT NOT NULL DEFAULT '',
                        person TEXT NOT NULL DEFAULT ''
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS money_entry_kinds (
                        key TEXT PRIMARY KEY,
                        display_name TEXT NOT NULL,
                        flow_direction TEXT NOT NULL
                            CHECK (flow_direction IN ('inflow', 'outflow')),
                        analysis_group TEXT NOT NULL
                            CHECK (analysis_group IN ('income', 'expense', 'liability', 'loan')),
                        counts_as_income INTEGER NOT NULL DEFAULT 0
                            CHECK (counts_as_income IN (0, 1)),
                        counts_as_expense INTEGER NOT NULL DEFAULT 0
                            CHECK (counts_as_expense IN (0, 1)),
                        counts_as_emi INTEGER NOT NULL DEFAULT 0
                            CHECK (counts_as_emi IN (0, 1)),
                        counts_as_credit INTEGER NOT NULL DEFAULT 0
                            CHECK (counts_as_credit IN (0, 1)),
                        counts_as_receivable INTEGER NOT NULL DEFAULT 0
                            CHECK (counts_as_receivable IN (0, 1)),
                        counts_as_payable INTEGER NOT NULL DEFAULT 0
                            CHECK (counts_as_payable IN (0, 1)),
                        counterparty_kind TEXT NOT NULL DEFAULT 'none'
                            CHECK (counterparty_kind IN ('none', 'person', 'institution'))
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS money_counterparties (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        normalized_name TEXT NOT NULL,
                        display_name TEXT NOT NULL,
                        kind TEXT NOT NULL
                            CHECK (kind IN ('person', 'institution')),
                        UNIQUE (normalized_name, kind)
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS money_entry_facts (
                        entry_id INTEGER PRIMARY KEY,
                        kind_key TEXT NOT NULL,
                        flow_direction TEXT NOT NULL
                            CHECK (flow_direction IN ('inflow', 'outflow')),
                        analysis_group TEXT NOT NULL
                            CHECK (analysis_group IN ('income', 'expense', 'liability', 'loan')),
                        occurred_at TEXT NOT NULL,
                        entered_at TEXT NOT NULL,
                        amount_minor INTEGER NOT NULL,
                        signed_amount_minor INTEGER NOT NULL,
                        currency_code TEXT NOT NULL DEFAULT 'INR',
                        note_raw TEXT NOT NULL DEFAULT '',
                        note_clean TEXT NOT NULL DEFAULT '',
                        counterparty_id INTEGER,
                        counterparty_name TEXT NOT NULL DEFAULT '',
                        counterparty_kind TEXT NOT NULL DEFAULT 'none'
                            CHECK (counterparty_kind IN ('none', 'person', 'institution')),
                        month_key TEXT NOT NULL,
                        FOREIGN KEY (entry_id) REFERENCES money_entries(id) ON DELETE CASCADE,
                        FOREIGN KEY (kind_key) REFERENCES money_entry_kinds(key),
                        FOREIGN KEY (counterparty_id) REFERENCES money_counterparties(id)
                    );
                    """
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_money_entries_date_type "
                    "ON money_entries (date DESC, entry_type, id DESC)"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_money_entry_facts_month_kind "
                    "ON money_entry_facts (month_key, kind_key, occurred_at DESC, entry_id DESC)"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_money_entry_facts_counterparty "
                    "ON money_entry_facts (counterparty_id, occurred_at DESC)"
                )
                self._seed_money_entry_kinds(cur)
                self._create_money_analysis_triggers(cur)
                self._create_money_analysis_views(cur)
                self._backfill_money_analysis(cur)
        except sqlite3.Error as exc:
            raise AssistantDataError("Unable to initialize the local database.") from exc

    def _seed_money_entry_kinds(self, cur: sqlite3.Cursor) -> None:
        for row in MONEY_ENTRY_KIND_ROWS:
            cur.execute(
                """
                INSERT INTO money_entry_kinds (
                    key,
                    display_name,
                    flow_direction,
                    analysis_group,
                    counts_as_income,
                    counts_as_expense,
                    counts_as_emi,
                    counts_as_credit,
                    counts_as_receivable,
                    counts_as_payable,
                    counterparty_kind
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    display_name = excluded.display_name,
                    flow_direction = excluded.flow_direction,
                    analysis_group = excluded.analysis_group,
                    counts_as_income = excluded.counts_as_income,
                    counts_as_expense = excluded.counts_as_expense,
                    counts_as_emi = excluded.counts_as_emi,
                    counts_as_credit = excluded.counts_as_credit,
                    counts_as_receivable = excluded.counts_as_receivable,
                    counts_as_payable = excluded.counts_as_payable,
                    counterparty_kind = excluded.counterparty_kind
                """,
                row,
            )

    def _create_money_analysis_triggers(self, cur: sqlite3.Cursor) -> None:
        cur.execute("DROP TRIGGER IF EXISTS trg_money_entries_analysis_insert")
        cur.execute("DROP TRIGGER IF EXISTS trg_money_entries_analysis_update")
        cur.execute(
            """
            CREATE TRIGGER trg_money_entries_analysis_insert
            AFTER INSERT ON money_entries
            BEGIN
                INSERT OR IGNORE INTO money_counterparties (normalized_name, display_name, kind)
                SELECT
                    lower(trim(NEW.person)),
                    trim(NEW.person),
                    'person'
                WHERE trim(COALESCE(NEW.person, '')) <> '';

                INSERT OR REPLACE INTO money_entry_facts (
                    entry_id,
                    kind_key,
                    flow_direction,
                    analysis_group,
                    occurred_at,
                    entered_at,
                    amount_minor,
                    signed_amount_minor,
                    currency_code,
                    note_raw,
                    note_clean,
                    counterparty_id,
                    counterparty_name,
                    counterparty_kind,
                    month_key
                )
                VALUES (
                    NEW.id,
                    NEW.entry_type,
                    (SELECT flow_direction FROM money_entry_kinds WHERE key = NEW.entry_type),
                    (SELECT analysis_group FROM money_entry_kinds WHERE key = NEW.entry_type),
                    NEW.date,
                    NEW.date,
                    CAST(ROUND(NEW.amount * 100) AS INTEGER),
                    CASE
                        WHEN (SELECT flow_direction FROM money_entry_kinds WHERE key = NEW.entry_type) = 'inflow'
                            THEN CAST(ROUND(NEW.amount * 100) AS INTEGER)
                        ELSE -CAST(ROUND(NEW.amount * 100) AS INTEGER)
                    END,
                    'INR',
                    COALESCE(NEW.note, ''),
                    trim(
                        replace(
                            replace(
                                replace(COALESCE(NEW.note, ''), char(13), ' '),
                                char(10),
                                ' '
                            ),
                            char(9),
                            ' '
                        )
                    ),
                    CASE
                        WHEN trim(COALESCE(NEW.person, '')) = '' THEN NULL
                        ELSE (
                            SELECT id
                            FROM money_counterparties
                            WHERE normalized_name = lower(trim(NEW.person))
                              AND kind = 'person'
                            LIMIT 1
                        )
                    END,
                    COALESCE(trim(NEW.person), ''),
                    CASE
                        WHEN trim(COALESCE(NEW.person, '')) = '' THEN 'none'
                        ELSE (SELECT counterparty_kind FROM money_entry_kinds WHERE key = NEW.entry_type)
                    END,
                    substr(NEW.date, 1, 7)
                );
            END
            """
        )
        cur.execute(
            """
            CREATE TRIGGER trg_money_entries_analysis_update
            AFTER UPDATE ON money_entries
            BEGIN
                INSERT OR IGNORE INTO money_counterparties (normalized_name, display_name, kind)
                SELECT
                    lower(trim(NEW.person)),
                    trim(NEW.person),
                    'person'
                WHERE trim(COALESCE(NEW.person, '')) <> '';

                INSERT OR REPLACE INTO money_entry_facts (
                    entry_id,
                    kind_key,
                    flow_direction,
                    analysis_group,
                    occurred_at,
                    entered_at,
                    amount_minor,
                    signed_amount_minor,
                    currency_code,
                    note_raw,
                    note_clean,
                    counterparty_id,
                    counterparty_name,
                    counterparty_kind,
                    month_key
                )
                VALUES (
                    NEW.id,
                    NEW.entry_type,
                    (SELECT flow_direction FROM money_entry_kinds WHERE key = NEW.entry_type),
                    (SELECT analysis_group FROM money_entry_kinds WHERE key = NEW.entry_type),
                    NEW.date,
                    NEW.date,
                    CAST(ROUND(NEW.amount * 100) AS INTEGER),
                    CASE
                        WHEN (SELECT flow_direction FROM money_entry_kinds WHERE key = NEW.entry_type) = 'inflow'
                            THEN CAST(ROUND(NEW.amount * 100) AS INTEGER)
                        ELSE -CAST(ROUND(NEW.amount * 100) AS INTEGER)
                    END,
                    'INR',
                    COALESCE(NEW.note, ''),
                    trim(
                        replace(
                            replace(
                                replace(COALESCE(NEW.note, ''), char(13), ' '),
                                char(10),
                                ' '
                            ),
                            char(9),
                            ' '
                        )
                    ),
                    CASE
                        WHEN trim(COALESCE(NEW.person, '')) = '' THEN NULL
                        ELSE (
                            SELECT id
                            FROM money_counterparties
                            WHERE normalized_name = lower(trim(NEW.person))
                              AND kind = 'person'
                            LIMIT 1
                        )
                    END,
                    COALESCE(trim(NEW.person), ''),
                    CASE
                        WHEN trim(COALESCE(NEW.person, '')) = '' THEN 'none'
                        ELSE (SELECT counterparty_kind FROM money_entry_kinds WHERE key = NEW.entry_type)
                    END,
                    substr(NEW.date, 1, 7)
                );
            END
            """
        )

    def _create_money_analysis_views(self, cur: sqlite3.Cursor) -> None:
        cur.execute("DROP VIEW IF EXISTS money_analysis_view")
        cur.execute(
            """
            CREATE VIEW money_analysis_view AS
            SELECT
                f.entry_id,
                f.kind_key,
                k.display_name AS kind_name,
                f.flow_direction,
                f.analysis_group,
                f.occurred_at,
                f.entered_at,
                f.amount_minor,
                f.signed_amount_minor,
                f.currency_code,
                f.note_raw,
                f.note_clean,
                f.counterparty_id,
                f.counterparty_name,
                f.counterparty_kind,
                f.month_key,
                k.counts_as_income,
                k.counts_as_expense,
                k.counts_as_emi,
                k.counts_as_credit,
                k.counts_as_receivable,
                k.counts_as_payable
            FROM money_entry_facts f
            JOIN money_entry_kinds k ON k.key = f.kind_key
            """
        )
        cur.execute("DROP VIEW IF EXISTS money_monthly_breakdown_view")
        cur.execute(
            """
            CREATE VIEW money_monthly_breakdown_view AS
            SELECT
                f.month_key,
                f.kind_key,
                k.analysis_group,
                COUNT(*) AS entry_count,
                SUM(f.amount_minor) AS total_amount_minor,
                SUM(f.signed_amount_minor) AS total_signed_amount_minor
            FROM money_entry_facts f
            JOIN money_entry_kinds k ON k.key = f.kind_key
            GROUP BY f.month_key, f.kind_key, k.analysis_group
            """
        )

    def _backfill_money_analysis(self, cur: sqlite3.Cursor) -> None:
        cur.execute(
            """
            INSERT OR IGNORE INTO money_counterparties (normalized_name, display_name, kind)
            SELECT DISTINCT
                lower(trim(person)) AS normalized_name,
                trim(person) AS display_name,
                'person' AS kind
            FROM money_entries
            WHERE trim(COALESCE(person, '')) <> ''
            """
        )
        cur.execute("DELETE FROM money_entry_facts")
        cur.execute(
            """
            INSERT INTO money_entry_facts (
                entry_id,
                kind_key,
                flow_direction,
                analysis_group,
                occurred_at,
                entered_at,
                amount_minor,
                signed_amount_minor,
                currency_code,
                note_raw,
                note_clean,
                counterparty_id,
                counterparty_name,
                counterparty_kind,
                month_key
            )
            SELECT
                e.id,
                e.entry_type,
                k.flow_direction,
                k.analysis_group,
                e.date,
                e.date,
                CAST(ROUND(e.amount * 100) AS INTEGER),
                CASE
                    WHEN k.flow_direction = 'inflow' THEN CAST(ROUND(e.amount * 100) AS INTEGER)
                    ELSE -CAST(ROUND(e.amount * 100) AS INTEGER)
                END,
                'INR',
                COALESCE(e.note, ''),
                trim(
                    replace(
                        replace(
                            replace(COALESCE(e.note, ''), char(13), ' '),
                            char(10),
                            ' '
                        ),
                        char(9),
                        ' '
                    )
                ),
                CASE
                    WHEN trim(COALESCE(e.person, '')) = '' THEN NULL
                    ELSE (
                        SELECT c.id
                        FROM money_counterparties c
                        WHERE c.normalized_name = lower(trim(e.person))
                          AND c.kind = 'person'
                        LIMIT 1
                    )
                END,
                COALESCE(trim(e.person), ''),
                CASE
                    WHEN trim(COALESCE(e.person, '')) = '' THEN 'none'
                    ELSE k.counterparty_kind
                END,
                substr(e.date, 1, 7)
            FROM money_entries e
            JOIN money_entry_kinds k ON k.key = e.entry_type
            """
        )

    def _create_task_analysis_views(self, cur: sqlite3.Cursor) -> None:
        cur.execute("DROP VIEW IF EXISTS task_analysis_view")
        cur.execute(
            """
            CREATE VIEW task_analysis_view AS
            SELECT
                c.id AS task_id,
                c.title_raw,
                c.title_clean,
                c.description_raw,
                c.description_clean,
                c.created_at,
                c.updated_at,
                c.dedup_key,
                c.source,
                c.project_name,
                CASE
                    WHEN a.task_id IS NOT NULL THEN 'active'
                    WHEN d.task_id IS NOT NULL THEN 'completed'
                    ELSE 'unknown'
                END AS lifecycle_stage,
                COALESCE(a.priority, d.priority) AS priority,
                a.status AS active_status,
                a.due_at,
                a.scheduled_for,
                a.started_at,
                a.estimated_minutes,
                a.energy_level,
                a.context_name,
                a.blocked_reason,
                a.last_touched_at,
                d.completed_at,
                d.actual_minutes,
                d.completion_reason,
                d.completion_note,
                CAST(
                    julianday(COALESCE(d.completed_at, CURRENT_TIMESTAMP)) - julianday(c.created_at)
                    AS REAL
                ) AS age_days
            FROM task_core c
            LEFT JOIN task_active a ON a.task_id = c.id
            LEFT JOIN task_completed d ON d.task_id = c.id
            """
        )
        cur.execute("DROP VIEW IF EXISTS task_daily_stats_view")
        cur.execute(
            """
            CREATE VIEW task_daily_stats_view AS
            SELECT
                day_key,
                SUM(created_count) AS created_count,
                SUM(completed_count) AS completed_count
            FROM (
                SELECT substr(created_at, 1, 10) AS day_key, COUNT(*) AS created_count, 0 AS completed_count
                FROM task_core
                GROUP BY substr(created_at, 1, 10)
                UNION ALL
                SELECT substr(completed_at, 1, 10) AS day_key, 0 AS created_count, COUNT(*) AS completed_count
                FROM task_completed
                GROUP BY substr(completed_at, 1, 10)
            )
            GROUP BY day_key
            """
        )

    def _task_dedup_key(self, title: str, description: str, priority: str) -> str:
        normalized_title, normalized_description, normalized_priority = normalize_task_input(
            title,
            description,
            priority,
        )
        return f"{normalized_title.lower()}|{normalized_description.lower()}|{normalized_priority}"

    def _backfill_task_lifecycle(self, cur: sqlite3.Cursor) -> None:
        tables = {
            row["name"]
            for row in cur.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        if "tasks_legacy" not in tables:
            return

        existing_core_ids = {
            row["id"]
            for row in cur.execute("SELECT id FROM task_core").fetchall()
        }
        legacy_rows = cur.execute("SELECT * FROM tasks_legacy ORDER BY id").fetchall()
        for row in legacy_rows:
            normalized_title, normalized_description, normalized_priority = normalize_task_input(
                row["title"],
                row["description"] or "",
                row["priority"] or "Medium",
            )
            created_at = row["date"] or datetime.now().strftime(DATE_FORMAT)
            updated_at = row["completed_at"] or created_at
            dedup_key = self._task_dedup_key(
                normalized_title,
                normalized_description,
                normalized_priority,
            )

            cur.execute(
                """
                INSERT OR IGNORE INTO task_core (
                    id,
                    title_raw,
                    title_clean,
                    description_raw,
                    description_clean,
                    created_at,
                    updated_at,
                    dedup_key,
                    source,
                    project_name
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["id"],
                    normalized_title,
                    normalized_title,
                    normalized_description,
                    normalized_description,
                    created_at,
                    updated_at,
                    dedup_key,
                    "legacy_migration",
                    "",
                ),
            )

            if row["done"]:
                completed_at = row["completed_at"] or created_at
                cur.execute("DELETE FROM task_active WHERE task_id = ?", (row["id"],))
                cur.execute(
                    """
                    INSERT OR REPLACE INTO task_completed (
                        task_id,
                        priority,
                        status_when_completed,
                        completed_at,
                        completion_reason,
                        completion_note
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"],
                        normalized_priority,
                        "pending",
                        completed_at,
                        "done",
                        "",
                    ),
                )
            else:
                cur.execute("DELETE FROM task_completed WHERE task_id = ?", (row["id"],))
                cur.execute(
                    """
                    INSERT OR REPLACE INTO task_active (
                        task_id,
                        priority,
                        status,
                        last_touched_at
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        row["id"],
                        normalized_priority,
                        "pending",
                        created_at,
                    ),
                )

            if row["id"] not in existing_core_ids:
                cur.execute(
                    """
                    INSERT INTO task_events (
                        task_id,
                        event_type,
                        event_at,
                        from_state,
                        to_state,
                        payload_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"],
                        "created",
                        created_at,
                        "",
                        "pending",
                        "{}",
                    ),
                )
                if row["done"]:
                    cur.execute(
                        """
                        INSERT INTO task_events (
                            task_id,
                            event_type,
                            event_at,
                            from_state,
                            to_state,
                            payload_json
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            row["id"],
                            "completed",
                            row["completed_at"] or created_at,
                            "pending",
                            "completed",
                            "{}",
                        ),
                    )

    def _execute_read(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        try:
            return self.conn.execute(query, params).fetchall()
        except sqlite3.Error as exc:
            raise AssistantDataError("Unable to read data from the local database.") from exc

    def _execute_write(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        try:
            with self.conn:
                return self.conn.execute(query, params)
        except sqlite3.Error as exc:
            raise AssistantDataError("Unable to save data to the local database.") from exc

    def _row_exists(self, table_name: str, record_id: int) -> bool:
        key_column = {
            "task_active": "task_id",
            "task_completed": "task_id",
            "money_entry_facts": "entry_id",
        }.get(table_name, "id")
        try:
            row = self.conn.execute(
                f"SELECT 1 FROM {table_name} WHERE {key_column} = ? LIMIT 1",
                (record_id,),
            ).fetchone()
        except sqlite3.Error as exc:
            raise AssistantDataError("Unable to read data from the local database.") from exc
        return row is not None

    # ---- tasks ----
    def insert_task(self, title: str, description: str, priority: str) -> int:
        normalized_title, normalized_description, normalized_priority = normalize_task_input(
            title,
            description,
            priority,
        )
        now_str = datetime.now().strftime(DATE_FORMAT)
        dedup_key = self._task_dedup_key(
            normalized_title,
            normalized_description,
            normalized_priority,
        )
        try:
            with self.conn:
                cur = self.conn.execute(
                    """
                    INSERT INTO task_core (
                        title_raw,
                        title_clean,
                        description_raw,
                        description_clean,
                        created_at,
                        updated_at,
                        dedup_key,
                        source,
                        project_name
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        normalized_title,
                        normalized_title,
                        normalized_description,
                        normalized_description,
                        now_str,
                        now_str,
                        dedup_key,
                        "app",
                        "",
                    ),
                )
                task_id = cur.lastrowid
                self.conn.execute(
                    """
                    INSERT INTO task_active (
                        task_id,
                        priority,
                        status,
                        last_touched_at
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        task_id,
                        normalized_priority,
                        "pending",
                        now_str,
                    ),
                )
                self.conn.execute(
                    """
                    INSERT INTO task_events (
                        task_id,
                        event_type,
                        event_at,
                        from_state,
                        to_state,
                        payload_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task_id,
                        "created",
                        now_str,
                        "",
                        "pending",
                        "{}",
                    ),
                )
        except sqlite3.Error as exc:
            raise AssistantDataError("Unable to save data to the local database.") from exc
        return task_id

    def get_tasks(self, done: int) -> List[Task]:
        if done not in (0, 1):
            raise ValidationError("Task status filter must be 0 or 1.")
        if done == 0:
            rows = self._execute_read(
                """
                SELECT
                    c.id,
                    c.title_clean AS title,
                    c.description_clean AS description,
                    c.created_at AS date,
                    NULL AS completed_at,
                    a.priority
                FROM task_core c
                JOIN task_active a ON a.task_id = c.id
                ORDER BY c.created_at DESC, c.id DESC
                """
            )
        else:
            rows = self._execute_read(
                """
                SELECT
                    c.id,
                    c.title_clean AS title,
                    c.description_clean AS description,
                    c.created_at AS date,
                    d.completed_at,
                    d.priority
                FROM task_core c
                JOIN task_completed d ON d.task_id = c.id
                ORDER BY d.completed_at DESC, c.id DESC
                """
            )
        tasks: List[Task] = []
        for r in rows:
            tasks.append(
                Task(
                    id=r["id"],
                    title=r["title"],
                    description=r["description"] or "",
                    date=datetime.fromisoformat(r["date"]) if r["date"] else None,
                    completed_at=datetime.fromisoformat(r["completed_at"]) if r["completed_at"] else None,
                    priority=r["priority"] or "Medium",
                    done=bool(done),
                )
            )
        return tasks

    def mark_task_done(self, task_id: int) -> None:
        normalized_task_id = normalize_record_id(task_id, "Task")
        now_str = datetime.now().strftime(DATE_FORMAT)
        try:
            active_row = self.conn.execute(
                """
                SELECT priority, status
                FROM task_active
                WHERE task_id = ?
                """,
                (normalized_task_id,),
            ).fetchone()
        except sqlite3.Error as exc:
            raise AssistantDataError("Unable to read data from the local database.") from exc

        if active_row is None:
            if self._row_exists("task_completed", normalized_task_id):
                return
            if not self._row_exists("task_core", normalized_task_id):
                raise RecordNotFoundError("Task not found.")
            raise AssistantDataError("Unable to update task status because the active task record is missing.")

        try:
            with self.conn:
                self.conn.execute("DELETE FROM task_active WHERE task_id = ?", (normalized_task_id,))
                self.conn.execute(
                    """
                    INSERT OR REPLACE INTO task_completed (
                        task_id,
                        priority,
                        status_when_completed,
                        completed_at,
                        completion_reason,
                        completion_note
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        normalized_task_id,
                        active_row["priority"] or "Medium",
                        active_row["status"] or "pending",
                        now_str,
                        "done",
                        "",
                    ),
                )
                self.conn.execute(
                    "UPDATE task_core SET updated_at = ? WHERE id = ?",
                    (now_str, normalized_task_id),
                )
                self.conn.execute(
                    """
                    INSERT INTO task_events (
                        task_id,
                        event_type,
                        event_at,
                        from_state,
                        to_state,
                        payload_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        normalized_task_id,
                        "completed",
                        now_str,
                        active_row["status"] or "pending",
                        "completed",
                        "{}",
                    ),
                )
        except sqlite3.Error as exc:
            raise AssistantDataError("Unable to save data to the local database.") from exc

    # ---- money ----
    def insert_money_entry(self, entry_type: str, amount: float, note: str, person: str) -> int:
        normalized_type, normalized_amount, normalized_note, normalized_person = normalize_money_entry_input(
            entry_type,
            amount,
            note,
            person,
        )
        now_str = datetime.now().strftime(DATE_FORMAT)
        cur = self._execute_write(
            "INSERT INTO money_entries (entry_type, amount, date, note, person) "
            "VALUES (?, ?, ?, ?, ?)",
            (normalized_type, normalized_amount, now_str, normalized_note, normalized_person),
        )
        return cur.lastrowid

    def update_money_entry(self, entry_id: int, entry_type: str, amount: float, note: str, person: str) -> None:
        normalized_entry_id = normalize_record_id(entry_id, "Money entry")
        normalized_type, normalized_amount, normalized_note, normalized_person = normalize_money_entry_input(
            entry_type,
            amount,
            note,
            person,
        )
        cur = self._execute_write(
            """
            UPDATE money_entries
            SET entry_type = ?, amount = ?, note = ?, person = ?
            WHERE id = ?
            """,
            (
                normalized_type,
                normalized_amount,
                normalized_note,
                normalized_person,
                normalized_entry_id,
            ),
        )
        if cur.rowcount == 0 and not self._row_exists("money_entries", normalized_entry_id):
            raise RecordNotFoundError("Money entry not found.")

    def delete_money_entry(self, entry_id: int) -> None:
        normalized_entry_id = normalize_record_id(entry_id, "Money entry")
        cur = self._execute_write("DELETE FROM money_entries WHERE id = ?", (normalized_entry_id,))
        if cur.rowcount == 0:
            raise RecordNotFoundError("Money entry not found.")

    def _money_where_clause(
        self,
        year: int | None = None,
        month: int | None = None,
        entry_type: str | None = None,
    ) -> tuple[str, list]:
        start_str, end_str = self._money_period_bounds(year=year, month=month)
        conditions = []
        params = []

        if start_str is not None and end_str is not None:
            conditions.extend(["date >= ?", "date < ?"])
            params.extend([start_str, end_str])

        if entry_type:
            if entry_type not in MONEY_ENTRY_TYPES:
                raise ValidationError("Money entry type is invalid.")
            conditions.append("entry_type = ?")
            params.append(entry_type)

        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        return where_clause, params

    def _money_period_bounds(
        self,
        year: int | None = None,
        month: int | None = None,
    ) -> tuple[str | None, str | None]:
        normalized_year, normalized_month = normalize_period(year=year, month=month)
        if normalized_year is None or normalized_month is None:
            return None, None
        start = datetime(normalized_year, normalized_month, 1)
        if normalized_month == 12:
            end = datetime(normalized_year + 1, 1, 1)
        else:
            end = datetime(normalized_year, normalized_month + 1, 1)
        return start.strftime(DATE_FORMAT), end.strftime(DATE_FORMAT)

    def get_money_entries(
        self,
        year: int | None = None,
        month: int | None = None,
        entry_type: str | None = None,
    ) -> List[MoneyEntry]:
        where_clause, params = self._money_where_clause(year, month, entry_type)
        rows = self._execute_read(
            f"SELECT * FROM money_entries{where_clause} ORDER BY date DESC, id DESC",
            tuple(params),
        )
        entries: List[MoneyEntry] = []
        for r in rows:
            entries.append(
                MoneyEntry(
                    id=r["id"],
                    entry_type=r["entry_type"],
                    amount=r["amount"],
                    date=datetime.fromisoformat(r["date"]),
                    note=r["note"] or "",
                    person=r["person"] or "",
                )
            )
        return entries

    def get_money_summary(
        self,
        year: int | None = None,
        month: int | None = None,
    ) -> Tuple[float, float, float, float, float]:
        start_str, end_str = self._money_period_bounds(year=year, month=month)

        def sum_for(flag_column: str) -> float:
            conditions = [f"k.{flag_column} = 1"]
            params: list[str] = []
            if start_str is not None and end_str is not None:
                conditions.extend(["f.occurred_at >= ?", "f.occurred_at < ?"])
                params.extend([start_str, end_str])
            where_clause = f" WHERE {' AND '.join(conditions)}"
            q = (
                "SELECT COALESCE(SUM(f.amount_minor), 0) AS total_minor "
                "FROM money_entry_facts f "
                "JOIN money_entry_kinds k ON k.key = f.kind_key"
                f"{where_clause}"
            )
            try:
                row = self.conn.execute(q, tuple(params)).fetchone()
            except sqlite3.Error as exc:
                raise AssistantDataError("Unable to read data from the local database.") from exc
            total_minor = row["total_minor"] if row else 0
            return total_minor / 100.0

        salary = sum_for("counts_as_income")
        expenses = sum_for("counts_as_expense")
        emi = sum_for("counts_as_emi")
        credit = sum_for("counts_as_credit")
        owes_you = sum_for("counts_as_receivable")
        return salary, expenses, emi, credit, owes_you
