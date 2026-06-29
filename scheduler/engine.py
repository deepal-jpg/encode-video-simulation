from __future__ import annotations

import threading
import time
from typing import Any

from .models import Job


class SchedulerEngine:
    def __init__(
        self,
        tick_seconds: float = 1.0,
        aging_factor: float = 0.35,
        autostart: bool = True,
        max_logs: int = 200,
    ) -> None:
        self.tick_seconds = tick_seconds
        self.aging_factor = aging_factor
        self.max_logs = max_logs
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._job_counter = 0
        self.clock_seconds = 0
        self.running_job: Job | None = None
        self.ready_queue: list[Job] = []
        self.completed_jobs: list[Job] = []
        self.event_log: list[str] = []
        if autostart:
            self.start()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.tick_seconds + 1)

    def reset(self) -> None:
        with self._lock:
            self._job_counter = 0
            self.clock_seconds = 0
            self.running_job = None
            self.ready_queue.clear()
            self.completed_jobs.clear()
            self.event_log.clear()
            self._log_locked("System reset. Global clock returned to 00:00.")

    def add_job(self, name: str, burst_time: int) -> Job:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Job name is required.")
        if burst_time <= 0:
            raise ValueError("Burst time must be a positive integer.")

        with self._lock:
            self._job_counter += 1
            job = Job(
                pid=f"VID-{self._job_counter}",
                name=clean_name,
                arrival_time=self.clock_seconds,
                burst_time=burst_time,
                remaining_time=burst_time,
                aging_factor=self.aging_factor,
            )
            job.refresh_effective_priority()
            self.ready_queue.append(job)
            self._log_locked(
                f"[{self.format_clock(self.clock_seconds)}] Arrival -> {job.pid} "
                f"({job.name}) joined the ready queue with burst {job.burst_time}s."
            )
            self._evaluate_schedule_locked()
            return job

    def tick(self) -> None:
        with self._lock:
            self.clock_seconds += 1
            for job in self.ready_queue:
                job.waiting_time += 1
                job.refresh_effective_priority()

            if self.running_job is not None:
                self.running_job.remaining_time = max(self.running_job.remaining_time - 1, 0)

            if self.running_job is not None and self.running_job.remaining_time == 0:
                completed_job = self.running_job
                completed_job.status = "completed"
                completed_job.completed_at = self.clock_seconds
                completed_job.turnaround_time = self.clock_seconds - completed_job.arrival_time
                completed_job.refresh_effective_priority()
                self.completed_jobs.append(completed_job)
                self._log_locked(
                    f"[{self.format_clock(self.clock_seconds)}] Complete -> {completed_job.pid} "
                    f"finished in {completed_job.turnaround_time}s turnaround."
                )
                self.running_job = None

            self._evaluate_schedule_locked()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            ready_queue = sorted(self.ready_queue, key=self._priority_key)
            return {
                "clock_seconds": self.clock_seconds,
                "clock_label": self.format_clock(self.clock_seconds),
                "running_job": self.running_job.to_dict() if self.running_job else None,
                "ready_queue": [job.to_dict() for job in ready_queue],
                "completed_jobs": [job.to_dict() for job in self.completed_jobs[-5:]],
                "event_log": list(self.event_log),
                "stats": {
                    "total_jobs": self._job_counter,
                    "queue_size": len(self.ready_queue),
                    "completed_count": len(self.completed_jobs),
                    "cpu_state": "busy" if self.running_job else "idle",
                },
                "config": {
                    "aging_factor": self.aging_factor,
                    "tick_seconds": self.tick_seconds,
                },
            }

    def _run_loop(self) -> None:
        while not self._stop_event.wait(self.tick_seconds):
            self.tick()

    def _evaluate_schedule_locked(self) -> None:
        candidate = self._best_ready_job_locked()
        if candidate is None:
            return

        if self.running_job is None:
            self._dispatch_job_locked(candidate, reason="dispatch")
            return

        current_score = self.running_job.remaining_time
        candidate_score = candidate.refresh_effective_priority()
        if candidate_score < current_score:
            previous_job = self.running_job
            previous_job.status = "ready"
            previous_job.refresh_effective_priority()
            self.ready_queue.append(previous_job)
            self.running_job = None
            self._log_locked(
                f"[{self.format_clock(self.clock_seconds)}] Context switch -> "
                f"{previous_job.pid} paused, {candidate.pid} takes the CPU."
            )
            self._dispatch_job_locked(candidate, reason="resume")

    def _best_ready_job_locked(self) -> Job | None:
        if not self.ready_queue:
            return None
        return min(self.ready_queue, key=self._priority_key)

    def _dispatch_job_locked(self, job: Job, reason: str) -> None:
        self.ready_queue = [queued_job for queued_job in self.ready_queue if queued_job.pid != job.pid]
        job.status = "running"
        job.refresh_effective_priority()
        self.running_job = job
        verb = "Started" if reason == "dispatch" else "Resumed"
        self._log_locked(
            f"[{self.format_clock(self.clock_seconds)}] {verb} -> {job.pid} "
            f"({job.name}) is now using the CPU."
        )

    def _priority_key(self, job: Job) -> tuple[float, int, str]:
        return (job.refresh_effective_priority(), job.arrival_time, job.pid)

    def _log_locked(self, message: str) -> None:
        self.event_log.append(message)
        if len(self.event_log) > self.max_logs:
            self.event_log = self.event_log[-self.max_logs :]

    @staticmethod
    def format_clock(seconds: int) -> str:
        minutes, remaining_seconds = divmod(seconds, 60)
        return f"{minutes:02d}:{remaining_seconds:02d}"
