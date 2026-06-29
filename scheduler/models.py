from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Job:
    pid: str
    name: str
    arrival_time: int
    burst_time: int
    remaining_time: int
    aging_factor: float
    waiting_time: int = 0
    turnaround_time: int | None = None
    status: str = "ready"
    completed_at: int | None = None
    effective_priority: float = field(default=0.0, init=False)

    def refresh_effective_priority(self) -> float:
        priority = self.remaining_time - (self.waiting_time * self.aging_factor)
        self.effective_priority = round(max(priority, 0.0), 2)
        return self.effective_priority

    def to_dict(self) -> dict[str, object]:
        self.refresh_effective_priority()
        return {
            "pid": self.pid,
            "name": self.name,
            "arrival_time": self.arrival_time,
            "burst_time": self.burst_time,
            "remaining_time": self.remaining_time,
            "waiting_time": self.waiting_time,
            "turnaround_time": self.turnaround_time,
            "aging_factor": self.aging_factor,
            "status": self.status,
            "completed_at": self.completed_at,
            "effective_priority": self.effective_priority,
        }
