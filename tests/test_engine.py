import unittest

from scheduler import SchedulerEngine


class SchedulerEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = SchedulerEngine(autostart=False, aging_factor=0.5)

    def test_shorter_job_preempts_running_job(self) -> None:
        first = self.engine.add_job("Video_A", 8)
        second = self.engine.add_job("Video_B", 3)

        self.assertEqual(self.engine.running_job.pid, second.pid)
        self.assertEqual(len(self.engine.ready_queue), 1)
        self.assertEqual(self.engine.ready_queue[0].pid, first.pid)

    def test_aging_changes_ready_queue_selection(self) -> None:
        self.engine.add_job("Long_Current", 6)
        aged = self.engine.add_job("Older_Waiting", 7)

        for _ in range(4):
            self.engine.tick()

        newer = self.engine.add_job("Newer_Shortish", 5)

        self.assertEqual(self.engine.running_job.name, "Long_Current")
        self.assertEqual({job.pid for job in self.engine.ready_queue}, {aged.pid, newer.pid})

        for _ in range(2):
            self.engine.tick()

        self.assertEqual(self.engine.running_job.pid, aged.pid)

    def test_completed_jobs_record_turnaround(self) -> None:
        job = self.engine.add_job("Tiny", 1)
        self.engine.tick()

        self.assertIsNone(self.engine.running_job)
        self.assertEqual(len(self.engine.completed_jobs), 1)
        self.assertEqual(self.engine.completed_jobs[0].pid, job.pid)
        self.assertEqual(self.engine.completed_jobs[0].turnaround_time, 1)


if __name__ == "__main__":
    unittest.main()
