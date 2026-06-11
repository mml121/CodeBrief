import time
from dataclasses import dataclass, field


@dataclass
class Metrics:
    start_time: float = field(default_factory=time.time)
    files_processed: int = 0
    files_skipped: int = 0
    skip_reasons: list[str] = field(default_factory=list)
    total_tokens: int = 0
    chunk_count: int = 0
    llm_request_count: int = 0
    retry_count: int = 0
    failed_requests: int = 0
    response_times: list[float] = field(default_factory=list)

    def elapsed(self) -> float:
        return round(time.time() - self.start_time, 2)

    def avg_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return round(sum(self.response_times) / len(self.response_times), 2)