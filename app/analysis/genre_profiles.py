from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from ..config import settings


_cache: Dict[str, Any] = {}


def load_profiles(path: str | None = None) -> Dict[str, Any]:
    profile_path = Path(path or settings.genre_profiles_path)
    if profile_path in _cache:
        return _cache[profile_path]
    data = json.loads(profile_path.read_text(encoding="utf-8"))
    _cache[profile_path] = data
    return data


def get_profile(genre: str, mode: str, vocal_style: str | None = None) -> Dict[str, Any]:
    profiles = load_profiles()
    genre_key = genre if genre in profiles else "default"
    profile = profiles[genre_key]
    mode_profile = profile.get("modes", {}).get(mode, {})

    if vocal_style and mode == "vocal":
        vocal_profiles = profile.get("vocal_styles", {})
        mode_profile = {**mode_profile, **vocal_profiles.get(vocal_style, {})}

    return mode_profile
