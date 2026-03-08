from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, List


@dataclass
class SensorSample:
    timestamp: float
    ax: float
    ay: float
    az: float
    gx: float
    gy: float
    gz: float


class SlidingWindowBuffer:
    def __init__(self, window_size: int = 128, step_size: int = 10) -> None:
        if window_size <= 0:
            raise ValueError("window_size must be > 0")
        if step_size <= 0:
            raise ValueError("step_size must be > 0")

        self.window_size = window_size
        self.step_size = step_size
        self._samples: Deque[SensorSample] = deque(maxlen=window_size)
        self._samples_since_emit = 0

    def __len__(self) -> int:
        return len(self._samples)

    def add_sample(self, sample: SensorSample) -> bool:
        self._samples.append(sample)
        self._samples_since_emit += 1

        if len(self._samples) < self.window_size:
            return False

        if self._samples_since_emit < self.step_size:
            return False

        self._samples_since_emit = 0
        return True

    def is_ready(self) -> bool:
        return len(self._samples) == self.window_size

    def to_matrix(self) -> List[List[float]]:
        # Keep fixed axis order expected by downstream feature extraction.
        return [
            [sample.ax, sample.ay, sample.az, sample.gx, sample.gy, sample.gz]
            for sample in self._samples
        ]

    def time_bounds(self) -> tuple[float, float]:
        if not self._samples:
            return 0.0, 0.0
        return self._samples[0].timestamp, self._samples[-1].timestamp
