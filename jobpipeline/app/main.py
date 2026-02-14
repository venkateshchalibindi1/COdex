from __future__ import annotations

import argparse
import sys
import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from jobpipeline.core.orchestrator import PipelineOrchestrator
from jobpipeline.storage.repository import JobRepository
from jobpipeline.utils.config import load_config
from jobpipeline.utils.logging_utils import setup_logging


class JobPipelineWindow(QMainWindow):
    def __init__(self, config_path: str) -> None:
        super().__init__()
        self.setWindowTitle("JobPipeline")
        self.resize(1250, 760)
        self.config_path = config_path
        self.config = load_config(config_path)
        self.repo = JobRepository()
        self.orchestrator = PipelineOrchestrator(self.config, self.repo)

        root = QWidget()
        root_layout = QVBoxLayout(root)

        top = QHBoxLayout()
        self.summary = QLabel("No runs yet")
        run_btn = QPushButton("Run pipeline now")
        run_btn.clicked.connect(self.run_pipeline)
        top.addWidget(self.summary)
        top.addWidget(run_btn)
        root_layout.addLayout(top)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "New", "Review", "Applied", "Interview", "Rejected", "Archived"])
        self.grade_filter = QComboBox()
        self.grade_filter.addItems(["All", "A", "B", "C", "D"])
        self.remote_filter = QComboBox()
        self.remote_filter.addItems(["All", "Y", "N", "Unknown"])
        for cb in (self.status_filter, self.grade_filter, self.remote_filter):
            cb.currentTextChanged.connect(self.refresh_jobs)

        filters = QHBoxLayout()
        filters.addWidget(QLabel("Status"))
        filters.addWidget(self.status_filter)
        filters.addWidget(QLabel("Grade"))
        filters.addWidget(self.grade_filter)
        filters.addWidget(QLabel("Remote"))
        filters.addWidget(self.remote_filter)
        root_layout.addLayout(filters)

        split = QSplitter(Qt.Horizontal)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["Job ID", "Company", "Title", "Location", "Remote", "Grade", "Status", "Link"])
        self.table.cellClicked.connect(self.show_detail)
        split.addWidget(self.table)

        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.status_edit = QComboBox()
        self.status_edit.addItems(["New", "Review", "Applied", "Interview", "Rejected", "Archived"])
        self.notes_edit = QTextEdit()
        save_btn = QPushButton("Save status/notes")
        save_btn.clicked.connect(self.save_status_notes)
        open_btn = QPushButton("Open link")
        open_btn.clicked.connect(self.open_link)
        detail_layout.addWidget(QLabel("Why score / job details"))
        detail_layout.addWidget(self.details)
        detail_layout.addWidget(QLabel("Status"))
        detail_layout.addWidget(self.status_edit)
        detail_layout.addWidget(QLabel("Notes"))
        detail_layout.addWidget(self.notes_edit)
        detail_layout.addWidget(save_btn)
        detail_layout.addWidget(open_btn)
        split.addWidget(detail)
        root_layout.addWidget(split)

        settings = QWidget()
        form = QFormLayout(settings)
        self.excel_path = QLineEdit(self.config["excel_path"])
        self.discovery_enabled = QCheckBox()
        self.discovery_enabled.setChecked(bool(self.config["discovery"]["enabled"]))
        self.playwright_enabled = QCheckBox()
        self.playwright_enabled.setChecked(bool(self.config["collector"]["use_playwright"]))
        form.addRow("Excel path", self.excel_path)
        form.addRow("Web discovery", self.discovery_enabled)
        form.addRow("JS-heavy fetch", self.playwright_enabled)
        root_layout.addWidget(settings)

        self.setCentralWidget(root)
        self.selected_job_id: str | None = None
        self.selected_link: str | None = None
        self.refresh_jobs()
        self.refresh_summary()

    def run_pipeline(self) -> None:
        counts = self.orchestrator.run()
        QMessageBox.information(self, "Run completed", f"Counts: {counts}")
        self.refresh_jobs()
        self.refresh_summary()

    def refresh_summary(self) -> None:
        runs = self.repo.list_runs()
        if not runs:
            self.summary.setText("No runs yet")
            return
        latest = runs[0]
        self.summary.setText(
            f"Last run #{latest['run_id']}: found={latest['num_found']} collected={latest['num_collected']} failed={latest['num_failed']} merged={latest['num_merged']} exported={latest['num_exported']}"
        )

    def refresh_jobs(self) -> None:
        rows = self.repo.list_jobs()
        status = self.status_filter.currentText()
        grade = self.grade_filter.currentText()
        remote = self.remote_filter.currentText()
        filtered = []
        for row in rows:
            if status != "All" and row["user_status"] != status:
                continue
            if grade != "All" and row["fit_grade"] != grade:
                continue
            if remote != "All" and row["remote_flag"] != remote:
                continue
            filtered.append(row)

        self.table.setRowCount(len(filtered))
        for idx, row in enumerate(filtered):
            vals = [
                row["job_id"],
                row["company"],
                row["title"],
                row["location_text"],
                row["remote_flag"],
                row["fit_grade"],
                row["user_status"],
                row["canonical_url"],
            ]
            for col, value in enumerate(vals):
                self.table.setItem(idx, col, QTableWidgetItem(str(value or "")))

    def show_detail(self, row: int, _: int) -> None:
        self.selected_job_id = self.table.item(row, 0).text()
        self.selected_link = self.table.item(row, 7).text()
        jobs = {j["job_id"]: j for j in self.repo.list_jobs()}
        job = jobs.get(self.selected_job_id)
        if not job:
            return
        self.details.setText(
            f"{job['title']} @ {job['company']}\n"
            f"Fit: {job['fit_score']} ({job['fit_grade']})\n"
            f"Notes: {job['fit_notes']}\n\n"
            f"Description:\n{job['description_raw'][:2500]}"
        )
        self.status_edit.setCurrentText(job["user_status"])
        self.notes_edit.setText(job["user_notes"] or "")

    def save_status_notes(self) -> None:
        if not self.selected_job_id:
            return
        self.repo.update_user_fields(self.selected_job_id, self.status_edit.currentText(), self.notes_edit.toPlainText())
        self.refresh_jobs()

    def open_link(self) -> None:
        if self.selected_link:
            webbrowser.open(self.selected_link)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()
    setup_logging()
    app = QApplication(sys.argv)
    window = JobPipelineWindow(args.config)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
