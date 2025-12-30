# AudioMixMentor

AudioMixMentor is a web app that analyzes vocal, instrumental, and full mix audio files and returns senior-engineer style feedback. It computes loudness (EBU R128), true peak, spectral balance, dynamics, stereo/phase, noise floor, and a suite of mix-specific diagnostics. Mix mode supports optional mastering A/B comparison against a reference track.

## Features
- Modes: Vocal, Instrumental, Mix
- Genre-aware targets (12+ profiles + sub-variants)
- Loudness (LUFS integrated + short-term), true peak, crest factor, dynamic range
- Spectral balance, stereo width, phase correlation, masking conflicts
- BPM and key estimation (instrumental + mix)
- A/B mastering comparison (mix mode)
- Async job queue with polling
- Seeded demo mode (no upload required)

## Requirements
- Python 3.11+ (Docker uses 3.12)
- FFmpeg + libsndfile for broad audio format support

## Quick Start (Local)
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 5005
```
Then open `http://localhost:5005`.

## Docker
```bash
docker compose up --build
```
Open `http://localhost:5005`.

## Demo Mode
Use the "Run Demo Mode" button in the UI to get a seeded report without uploading audio.

## API Endpoints
- `POST /api/jobs` (multipart form)
  - `mode`: `vocal` | `instrumental` | `mix`
  - `genre`: string
  - `vocal_style`: `rap` | `singing` | `both` (vocal mode only)
  - `audio`: audio file
  - `reference`: optional audio file for mix A/B
  - `demo`: `true` for demo mode
- `GET /api/jobs/{job_id}`
- `GET /api/genres`

## Result Schema
See `schemas/analysis_result.schema.json`.
