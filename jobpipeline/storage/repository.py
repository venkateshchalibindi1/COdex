from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from jobpipeline.core.models import CanonicalJob


class JobRepository:
    def __init__(self, db_path: str = "data/jobpipeline.db") -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                source_domain TEXT,
                source_name TEXT,
                job_url TEXT,
                canonical_url TEXT UNIQUE,
                apply_url TEXT,
                title TEXT,
                company TEXT,
                location_text TEXT,
                remote_flag TEXT,
                employment_type TEXT,
                posted_date TEXT,
                collected_at TEXT,
                description_raw TEXT,
                salary_text TEXT,
                skills_extracted TEXT,
                fetch_status TEXT,
                failure_reason TEXT,
                first_seen TEXT,
                last_seen TEXT,
                repost_count INTEGER,
                merged_from TEXT,
                fit_score INTEGER,
                fit_grade TEXT,
                fit_notes TEXT,
                missing_must_have TEXT,
                flags TEXT,
                user_status TEXT,
                user_notes TEXT
            );
            CREATE TABLE IF NOT EXISTS job_sources_seen (
                job_id TEXT,
                source_name TEXT,
                source_domain TEXT,
                seen_at TEXT
            );
            CREATE TABLE IF NOT EXISTS runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT,
                finished_at TEXT,
                num_found INTEGER,
                num_collected INTEGER,
                num_failed INTEGER,
                num_merged INTEGER,
                num_exported INTEGER
            );
            CREATE TABLE IF NOT EXISTS run_errors (
                run_id INTEGER,
                domain TEXT,
                reason TEXT,
                trace_summary TEXT
            );
            """
        )
        self.conn.commit()

    def upsert_job(self, job: CanonicalJob) -> None:
        existing = self.conn.execute("SELECT user_status, user_notes, first_seen, source_name FROM jobs WHERE job_id=?", (job.job_id,)).fetchone()
        user_status = existing["user_status"] if existing else job.user_status
        user_notes = existing["user_notes"] if existing else job.user_notes
        first_seen = existing["first_seen"] if existing else job.first_seen
        source_name = existing["source_name"] if existing else job.source_name
        if existing and job.source_name not in source_name.split(","):
            source_name = f"{source_name},{job.source_name}"

        self.conn.execute(
            """
            INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(job_id) DO UPDATE SET
                source_domain=excluded.source_domain,
                source_name=excluded.source_name,
                job_url=excluded.job_url,
                canonical_url=excluded.canonical_url,
                apply_url=excluded.apply_url,
                title=excluded.title,
                company=excluded.company,
                location_text=excluded.location_text,
                remote_flag=excluded.remote_flag,
                employment_type=excluded.employment_type,
                posted_date=excluded.posted_date,
                collected_at=excluded.collected_at,
                description_raw=excluded.description_raw,
                salary_text=excluded.salary_text,
                skills_extracted=excluded.skills_extracted,
                fetch_status=excluded.fetch_status,
                failure_reason=excluded.failure_reason,
                first_seen=excluded.first_seen,
                last_seen=excluded.last_seen,
                repost_count=excluded.repost_count,
                merged_from=excluded.merged_from,
                fit_score=excluded.fit_score,
                fit_grade=excluded.fit_grade,
                fit_notes=excluded.fit_notes,
                missing_must_have=excluded.missing_must_have,
                flags=excluded.flags,
                user_status=excluded.user_status,
                user_notes=excluded.user_notes
            """,
            (
                job.job_id,
                job.source_domain,
                source_name,
                job.job_url,
                job.canonical_url,
                job.apply_url,
                job.title,
                job.company,
                job.location_text,
                job.remote_flag,
                job.employment_type,
                job.posted_date,
                job.collected_at,
                job.description_raw,
                job.salary_text,
                json.dumps(job.skills_extracted),
                job.fetch_status,
                job.failure_reason,
                first_seen,
                job.last_seen,
                job.repost_count,
                json.dumps(job.merged_from),
                job.fit_score,
                job.fit_grade,
                job.fit_notes,
                json.dumps(job.missing_must_have),
                json.dumps(job.flags),
                user_status,
                user_notes,
            ),
        )
        self.conn.execute(
            "INSERT INTO job_sources_seen VALUES (?,?,?,?)",
            (job.job_id, job.source_name, job.source_domain, job.last_seen),
        )
        self.conn.commit()

    def list_jobs(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM jobs ORDER BY last_seen DESC").fetchall()

    def update_user_fields(self, job_id: str, status: str, notes: str) -> None:
        self.conn.execute("UPDATE jobs SET user_status=?, user_notes=? WHERE job_id=?", (status, notes, job_id))
        self.conn.commit()

    def create_run(self, started_at: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO runs(started_at, finished_at, num_found, num_collected, num_failed, num_merged, num_exported) VALUES (?,?,?,?,?,?,?)",
            (started_at, started_at, 0, 0, 0, 0, 0),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def finish_run(self, run_id: int, finished_at: str, counts: dict[str, int]) -> None:
        self.conn.execute(
            "UPDATE runs SET finished_at=?, num_found=?, num_collected=?, num_failed=?, num_merged=?, num_exported=? WHERE run_id=?",
            (
                finished_at,
                counts.get("found", 0),
                counts.get("collected", 0),
                counts.get("failed", 0),
                counts.get("merged", 0),
                counts.get("exported", 0),
                run_id,
            ),
        )
        self.conn.commit()

    def add_run_error(self, run_id: int, domain: str, reason: str, trace_summary: str = "") -> None:
        self.conn.execute(
            "INSERT INTO run_errors VALUES (?,?,?,?)",
            (run_id, domain, reason, trace_summary),
        )
        self.conn.commit()

    def list_runs(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM runs ORDER BY run_id DESC").fetchall()

    def list_failures(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM run_errors ORDER BY run_id DESC").fetchall()
