from redis import Redis
from rq import Queue

from config import settings


class OrchestrationQueue:
    """
    Lightweight orchestration adapter using Redis + RQ.

    This is intentionally minimal so it can be swapped with Temporal
    or another workflow engine in production.
    """

    def __init__(self, redis_url: str) -> None:
        self._redis = Redis.from_url(redis_url)
        self._job_queue = Queue("jobs", connection=self._redis)
        self._run_queue = Queue("runs", connection=self._redis)

    def enqueue_extraction(self, job_id: str) -> None:
        # The worker side will implement `extractor.worker.process_job`.
        self._job_queue.enqueue("extractor.worker.process_job", job_id=job_id)

    def enqueue_test_run(self, job_id: str, test_id: str) -> str:
        """
        Enqueue a test run into the runner queue.
        Returns the Redis/RQ job id which we treat as runId.
        """
        rq_job = self._run_queue.enqueue(
            "runner.worker.run_test",
            job_id=job_id,
            test_id=test_id,
        )
        return rq_job.id


queue_adapter = OrchestrationQueue(settings.redis_url)

