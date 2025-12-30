import numpy as np

from app.analysis.bpm_key import estimate_bpm, estimate_key


def test_bpm_estimate_on_pulse():
    sr = 48000
    duration = 4.0
    samples = int(sr * duration)
    audio = np.zeros(samples, dtype=np.float32)
    interval = int(sr * 0.5)  # 120 BPM
    for i in range(0, samples, interval):
        audio[i:i + 200] = 1.0
    audio = audio[:, None]

    tempo = estimate_bpm(audio, sr)
    assert tempo.bpm > 0
    assert 0.0 <= tempo.confidence <= 1.0


def test_key_estimate_returns_string():
    sr = 48000
    t = np.linspace(0, 2.0, int(sr * 2.0), endpoint=False)
    audio = 0.1 * np.sin(2 * np.pi * 440 * t)
    audio = audio[:, None]

    key = estimate_key(audio, sr)
    assert isinstance(key.key, str)
