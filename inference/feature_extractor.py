from __future__ import annotations

import numpy as np


def _safe_entropy(values: np.ndarray, bins: int = 16) -> float:
    hist, _ = np.histogram(values, bins=bins, density=True)
    hist = hist[hist > 0]
    if hist.size == 0:
        return 0.0
    return float(-np.sum(hist * np.log(hist + 1e-12)))


def _axis_feature_block(axis_values: np.ndarray) -> np.ndarray:
    mean = np.mean(axis_values)
    std = np.std(axis_values)
    min_v = np.min(axis_values)
    max_v = np.max(axis_values)
    median = np.median(axis_values)
    q25 = np.percentile(axis_values, 25)
    q75 = np.percentile(axis_values, 75)
    energy = np.mean(axis_values ** 2)
    entropy = _safe_entropy(axis_values)

    fft_mag = np.abs(np.fft.rfft(axis_values))
    fft_energy = np.mean(fft_mag ** 2)
    fft_peak = np.max(fft_mag)
    fft_mean = np.mean(fft_mag)
    fft_std = np.std(fft_mag)

    return np.array([
        mean,
        std,
        min_v,
        max_v,
        median,
        q25,
        q75,
        energy,
        entropy,
        fft_energy,
        fft_peak,
        fft_mean,
        fft_std,
    ], dtype=np.float32)


def extract_feature_vector(window_matrix: np.ndarray, expected_dim: int) -> np.ndarray:
    if window_matrix.ndim != 2 or window_matrix.shape[1] != 6:
        raise ValueError("window_matrix must have shape [N, 6]")

    acc = window_matrix[:, :3]
    gyro = window_matrix[:, 3:]

    blocks = []

    for axis in range(3):
        blocks.append(_axis_feature_block(acc[:, axis]))
    for axis in range(3):
        blocks.append(_axis_feature_block(gyro[:, axis]))

    acc_mag = np.linalg.norm(acc, axis=1)
    gyro_mag = np.linalg.norm(gyro, axis=1)
    blocks.append(_axis_feature_block(acc_mag))
    blocks.append(_axis_feature_block(gyro_mag))

    # Cross-axis correlations help capture posture transitions.
    corr_features = []
    for source in (acc, gyro):
        corr = np.corrcoef(source.T)
        corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
        corr_features.extend([
            corr[0, 1],
            corr[0, 2],
            corr[1, 2],
        ])
    blocks.append(np.array(corr_features, dtype=np.float32))

    base_features = np.concatenate(blocks).astype(np.float32)

    if base_features.size >= expected_dim:
        return base_features[:expected_dim]

    pad = np.zeros(expected_dim - base_features.size, dtype=np.float32)
    return np.concatenate([base_features, pad], axis=0)
