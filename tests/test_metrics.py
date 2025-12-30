import numpy as np

from app.analysis.metrics import compute_loudness, compute_spectral, compute_stereo


def test_loudness_metrics():
    sr = 48000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    audio = 0.1 * np.sin(2 * np.pi * 440 * t)
    audio = audio[:, None]

    loudness = compute_loudness(audio, sr)
    assert loudness.integrated_lufs < 0
    assert loudness.true_peak_db <= 0


def test_spectral_metrics():
    sr = 48000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    audio = 0.1 * np.sin(2 * np.pi * 440 * t)
    audio = audio[:, None]

    spectral = compute_spectral(audio, sr)
    assert spectral.centroid_hz > 0


def test_stereo_metrics():
    sr = 48000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    left = 0.1 * np.sin(2 * np.pi * 440 * t)
    right = 0.1 * np.sin(2 * np.pi * 880 * t)
    audio = np.stack([left, right], axis=1)

    stereo = compute_stereo(audio)
    assert stereo.width >= 0
