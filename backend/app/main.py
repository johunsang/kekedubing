from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import wave
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import argostranslate.translate
import argostranslate.package
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

ROOT = Path(os.getenv("APP_ROOT", "/app")).resolve()
WEB_DIR = Path(os.getenv("WEB_DIR", ROOT / "web")).resolve()
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data")).resolve()
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "0"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024 if MAX_UPLOAD_MB > 0 else 0
SUBTITLE_FONT = os.getenv("SUBTITLE_FONT", "Noto Sans")
MIN_DUB_SPEED = float(os.getenv("MIN_DUB_SPEED", "0.85"))
MAX_DUB_SPEED = float(os.getenv("MAX_DUB_SPEED", "1.75"))
LANGUAGE_SUBTITLE_FONTS = {
    "ar": "Noto Naskh Arabic",
    "hi": "Noto Sans Devanagari",
    "ja": "Noto Sans CJK JP",
    "ko": "Noto Sans CJK KR",
}
SUPERTONIC_LANGUAGES = [
    {"code": "en", "label": "English"},
    {"code": "ko", "label": "Korean"},
    {"code": "ja", "label": "Japanese"},
    {"code": "ar", "label": "Arabic"},
    {"code": "bg", "label": "Bulgarian"},
    {"code": "cs", "label": "Czech"},
    {"code": "da", "label": "Danish"},
    {"code": "de", "label": "German"},
    {"code": "el", "label": "Greek"},
    {"code": "es", "label": "Spanish"},
    {"code": "et", "label": "Estonian"},
    {"code": "fi", "label": "Finnish"},
    {"code": "fr", "label": "French"},
    {"code": "hi", "label": "Hindi"},
    {"code": "hr", "label": "Croatian"},
    {"code": "hu", "label": "Hungarian"},
    {"code": "id", "label": "Indonesian"},
    {"code": "it", "label": "Italian"},
    {"code": "lt", "label": "Lithuanian"},
    {"code": "lv", "label": "Latvian"},
    {"code": "nl", "label": "Dutch"},
    {"code": "pl", "label": "Polish"},
    {"code": "pt", "label": "Portuguese"},
    {"code": "ro", "label": "Romanian"},
    {"code": "ru", "label": "Russian"},
    {"code": "sk", "label": "Slovak"},
    {"code": "sl", "label": "Slovenian"},
    {"code": "sv", "label": "Swedish"},
    {"code": "tr", "label": "Turkish"},
    {"code": "uk", "label": "Ukrainian"},
    {"code": "vi", "label": "Vietnamese"},
]
SUPERTONIC_VOICES = [
    {"code": "M1", "label": "Male 1 (M1)"},
    {"code": "M2", "label": "Male 2 (M2)"},
    {"code": "M3", "label": "Male 3 (M3)"},
    {"code": "M4", "label": "Male 4 (M4)"},
    {"code": "M5", "label": "Male 5 (M5)"},
    {"code": "F1", "label": "Female 1 (F1)"},
    {"code": "F2", "label": "Female 2 (F2)"},
    {"code": "F3", "label": "Female 3 (F3)"},
    {"code": "F4", "label": "Female 4 (F4)"},
    {"code": "F5", "label": "Female 5 (F5)"},
]
SUPERTONIC_LANGUAGE_CODES = {item["code"] for item in SUPERTONIC_LANGUAGES}
SUPERTONIC_VOICE_CODES = {item["code"] for item in SUPERTONIC_VOICES}
SUBTITLE_STYLES = [
    {"code": "clean", "label": "Clean white", "force_style": "FontSize=15,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=120"},
    {"code": "bold", "label": "Bold outline", "force_style": "FontSize=18,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=4,Shadow=1,Alignment=2,MarginV=130"},
    {"code": "yellow", "label": "Yellow creator", "force_style": "FontSize=18,Bold=1,PrimaryColour=&H0000D7FF,OutlineColour=&H00000000,BorderStyle=1,Outline=4,Shadow=1,Alignment=2,MarginV=130"},
    {"code": "boxed", "label": "Boxed caption", "force_style": "FontSize=16,Bold=1,PrimaryColour=&H00FFFFFF,BackColour=&H99000000,OutlineColour=&H99000000,BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=110"},
    {"code": "shorts_punch", "label": "Shorts punch", "force_style": "FontSize=20,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,BorderStyle=1,Outline=5,Shadow=0,Alignment=2,MarginV=150"},
    {"code": "tiktok_pop", "label": "TikTok pop", "force_style": "FontSize=19,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00FF4DD8,BorderStyle=1,Outline=3,Shadow=2,Alignment=2,MarginV=135"},
    {"code": "reels_blue", "label": "Reels blue", "force_style": "FontSize=18,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00FF8A2A,BorderStyle=1,Outline=4,Shadow=1,Alignment=2,MarginV=135"},
    {"code": "news_lower", "label": "News lower", "force_style": "FontSize=15,Bold=1,PrimaryColour=&H00FFFFFF,BackColour=&HCC101820,OutlineColour=&HCC101820,BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=70"},
    {"code": "breaking_red", "label": "Breaking red", "force_style": "FontSize=16,Bold=1,PrimaryColour=&H00FFFFFF,BackColour=&HCC1717D9,OutlineColour=&HCC1717D9,BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=80"},
    {"code": "cinema", "label": "Cinema", "force_style": "FontSize=14,PrimaryColour=&H00F2F2F2,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,Alignment=2,MarginV=90"},
    {"code": "cinema_gold", "label": "Cinema gold", "force_style": "FontSize=15,Bold=1,PrimaryColour=&H0000CCFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=1,Alignment=2,MarginV=95"},
    {"code": "documentary", "label": "Documentary", "force_style": "FontSize=14,PrimaryColour=&H00E8E8E8,OutlineColour=&H00323232,BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=95"},
    {"code": "minimal_top", "label": "Minimal top", "force_style": "FontSize=14,PrimaryColour=&H00FFFFFF,OutlineColour=&H66000000,BorderStyle=1,Outline=1,Shadow=0,Alignment=8,MarginV=70"},
    {"code": "minimal_bottom", "label": "Minimal bottom", "force_style": "FontSize=14,PrimaryColour=&H00FFFFFF,OutlineColour=&H66000000,BorderStyle=1,Outline=1,Shadow=0,Alignment=2,MarginV=95"},
    {"code": "neon_green", "label": "Neon green", "force_style": "FontSize=18,Bold=1,PrimaryColour=&H005CFF6A,OutlineColour=&H00001810,BorderStyle=1,Outline=4,Shadow=2,Alignment=2,MarginV=135"},
    {"code": "neon_cyan", "label": "Neon cyan", "force_style": "FontSize=18,Bold=1,PrimaryColour=&H00FFE45C,OutlineColour=&H00202000,BorderStyle=1,Outline=4,Shadow=2,Alignment=2,MarginV=135"},
    {"code": "neon_pink", "label": "Neon pink", "force_style": "FontSize=18,Bold=1,PrimaryColour=&H00C85CFF,OutlineColour=&H00200020,BorderStyle=1,Outline=4,Shadow=2,Alignment=2,MarginV=135"},
    {"code": "white_shadow", "label": "White shadow", "force_style": "FontSize=17,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=3,Alignment=2,MarginV=125"},
    {"code": "black_box", "label": "Black box", "force_style": "FontSize=16,Bold=1,PrimaryColour=&H00FFFFFF,BackColour=&HE0000000,OutlineColour=&HE0000000,BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=110"},
    {"code": "white_box", "label": "White box", "force_style": "FontSize=16,Bold=1,PrimaryColour=&H00171717,BackColour=&HEEFFFFFF,OutlineColour=&HEEFFFFFF,BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=110"},
    {"code": "blue_box", "label": "Blue box", "force_style": "FontSize=16,Bold=1,PrimaryColour=&H00FFFFFF,BackColour=&HCC9A4A10,OutlineColour=&HCC9A4A10,BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=110"},
    {"code": "orange_box", "label": "Orange box", "force_style": "FontSize=16,Bold=1,PrimaryColour=&H00FFFFFF,BackColour=&HCC1A7AFF,OutlineColour=&HCC1A7AFF,BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=110"},
    {"code": "karaoke_yellow", "label": "Karaoke yellow", "force_style": "FontSize=19,Bold=1,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=4,Shadow=1,Alignment=2,MarginV=140"},
    {"code": "karaoke_purple", "label": "Karaoke purple", "force_style": "FontSize=19,Bold=1,PrimaryColour=&H00FF66CC,OutlineColour=&H00000000,BorderStyle=1,Outline=4,Shadow=1,Alignment=2,MarginV=140"},
    {"code": "podcast", "label": "Podcast", "force_style": "FontSize=15,Bold=1,PrimaryColour=&H00F7F7F7,BackColour=&HB0302520,OutlineColour=&HB0302520,BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=100"},
    {"code": "lecture", "label": "Lecture", "force_style": "FontSize=14,PrimaryColour=&H00242424,BackColour=&HEEFAFAFA,OutlineColour=&HEEFAFAFA,BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=90"},
    {"code": "gaming", "label": "Gaming", "force_style": "FontSize=18,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H0000AAFF,BorderStyle=1,Outline=4,Shadow=2,Alignment=2,MarginV=135"},
    {"code": "sports", "label": "Sports", "force_style": "FontSize=18,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00008000,BorderStyle=1,Outline=4,Shadow=2,Alignment=2,MarginV=135"},
    {"code": "beauty", "label": "Beauty", "force_style": "FontSize=17,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00D88CFF,BorderStyle=1,Outline=3,Shadow=1,Alignment=2,MarginV=125"},
    {"code": "food", "label": "Food", "force_style": "FontSize=17,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00008CFF,BorderStyle=1,Outline=3,Shadow=1,Alignment=2,MarginV=125"},
    {"code": "travel", "label": "Travel", "force_style": "FontSize=16,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00A07020,BorderStyle=1,Outline=3,Shadow=1,Alignment=2,MarginV=115"},
    {"code": "finance", "label": "Finance", "force_style": "FontSize=15,Bold=1,PrimaryColour=&H00FFFFFF,BackColour=&HCC1F7A1F,OutlineColour=&HCC1F7A1F,BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=95"},
    {"code": "warning", "label": "Warning", "force_style": "FontSize=17,Bold=1,PrimaryColour=&H0000D7FF,BackColour=&HCC000000,OutlineColour=&HCC000000,BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=120"},
    {"code": "soft_gray", "label": "Soft gray", "force_style": "FontSize=15,PrimaryColour=&H00E6E6E6,OutlineColour=&H00222222,BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=100"},
    {"code": "large_accessible", "label": "Large accessible", "force_style": "FontSize=22,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=5,Shadow=0,Alignment=2,MarginV=155"},
]
SUBTITLE_STYLE_CODES = {item["code"] for item in SUBTITLE_STYLES}
SUBTITLE_POSITIONS = [
    {"code": "bottom", "label": "Bottom", "force_style": "Alignment=2,MarginV=120"},
    {"code": "lower_third", "label": "Lower third", "force_style": "Alignment=2,MarginV=210"},
    {"code": "middle", "label": "Middle", "force_style": "Alignment=5,MarginV=0"},
    {"code": "top", "label": "Top", "force_style": "Alignment=8,MarginV=80"},
]
SUBTITLE_POSITION_CODES = {item["code"] for item in SUBTITLE_POSITIONS}
_SUPERTONIC_TTS: Any | None = None
OUTPUT_DIR = DATA_DIR / "output" / "merged"
TMP_DIR = DATA_DIR / "tmp"
STORE_PATH = DATA_DIR / "store.json"
UPLOAD_DIR = DATA_DIR / "uploads"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="케케더빙 Local Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def run_command(args: list[str], *, timeout: int = 300) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            args,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=f"missing executable: {args[0]}") from exc
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or exc.stdout or b"").decode("utf-8", errors="replace").strip()
        raise HTTPException(status_code=500, detail=message or str(exc)) from exc


def audio_prompt(style: str, duration: float) -> str:
    prompts = {
        "calm": "soft lo-fi instrumental background music, warm pads, gentle beat, no vocals",
        "upbeat": "bright upbeat commercial instrumental background music, light percussion, no vocals",
        "cinematic": "cinematic inspirational instrumental background music, soft strings, no vocals",
    }
    base = prompts.get(style, prompts["calm"])
    return f"{base}, {int(duration)} seconds"


def translate_text(text: str, source: str, target: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    if source == target:
        return text
    try:
        return argostranslate.translate.translate(text, source, target).strip()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"local translation failed: {exc}") from exc


def translate_with_pivot(text: str, source: str, target: str) -> str:
    if source == "auto":
        source = "en"
    if source == target:
        return text
    try:
        direct = translate_text(text, source, target)
        if direct and direct != text:
            return direct
    except HTTPException:
        direct = ""
    if source != "en" and target != "en":
        return translate_text(translate_text(text, source, "en"), "en", target)
    if direct:
        return direct
    raise HTTPException(status_code=500, detail=f"Translation model is not installed: {source}->{target}")


def fmt_srt_time(seconds: float) -> str:
    ms = max(0, int(round(seconds * 1000)))
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def media_duration(path: Path) -> float:
    try:
        result = run_command(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            timeout=60,
        )
        return float(result.stdout.decode("utf-8", errors="replace").strip() or 0)
    except Exception:
        return 0.0


def media_dimensions(path: Path) -> tuple[int, int]:
    try:
        result = run_command(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "csv=s=x:p=0",
                str(path),
            ],
            timeout=60,
        )
        width, height = result.stdout.decode("utf-8", errors="replace").strip().split("x")
        return int(width), int(height)
    except Exception:
        return 0, 0


def to_srt(segments: list[dict[str, Any]], target_lang: str) -> str:
    blocks: list[str] = []
    for index, segment in enumerate(segments, start=1):
        text = translate_with_pivot(segment["text"], segment.get("language") or "auto", target_lang)
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        blocks.append(
            f"{index}\n{fmt_srt_time(segment['start'])} --> {fmt_srt_time(segment['end'])}\n{text}"
        )
    return "\n\n".join(blocks)


def parse_srt(srt_text: str) -> list[dict[str, Any]]:
    pattern = re.compile(
        r"(?:^|\n)\s*(?:\d+\s*)?\n?"
        r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*\n"
        r"(.+?)(?=\n\s*\n|\Z)",
        re.S,
    )
    entries: list[dict[str, Any]] = []
    for match in pattern.finditer("\n" + srt_text.strip()):
        text = re.sub(r"\s+", " ", match.group(3)).strip()
        if text:
            entries.append(
                {
                    "start": parse_srt_time(match.group(1)),
                    "end": parse_srt_time(match.group(2)),
                    "text": text,
                }
            )
    return entries


def parse_srt_time(value: str) -> float:
    hours, minutes, rest = value.replace(",", ".").split(":")
    seconds, millis = rest.split(".")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis[:3]) / 1000


def safe_path(path: str) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    candidate = candidate.resolve()
    if not candidate.exists():
        raise HTTPException(status_code=404, detail=f"file not found: {path}")
    return candidate


def validate_video_options(target_lang: str, voice: str, subtitle_style: str) -> None:
    if target_lang not in SUPERTONIC_LANGUAGE_CODES:
        raise HTTPException(status_code=400, detail=f"Unsupported Supertonic language: {target_lang}")
    if voice not in SUPERTONIC_VOICE_CODES:
        raise HTTPException(status_code=400, detail=f"Unsupported Supertonic voice: {voice}")
    if subtitle_style not in SUBTITLE_STYLE_CODES:
        raise HTTPException(status_code=400, detail=f"Unsupported subtitle style: {subtitle_style}")


def validate_subtitle_position(position: str) -> str:
    selected = position or os.getenv("SUBTITLE_POSITION", "bottom")
    if selected not in SUBTITLE_POSITION_CODES:
        raise HTTPException(status_code=400, detail=f"Unsupported subtitle position: {selected}")
    return selected


def validate_subtitle_size(value: Any) -> int:
    try:
        size = int(float(value))
    except Exception:
        size = int(os.getenv("SUBTITLE_SIZE", "100"))
    return max(50, min(250, size))


def validate_source_lang(source_lang: str) -> str | None:
    if not source_lang or source_lang == "auto":
        return None
    if source_lang not in SUPERTONIC_LANGUAGE_CODES:
        raise HTTPException(status_code=400, detail=f"Unsupported source language: {source_lang}")
    return source_lang


def installed_translation_pairs() -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    try:
        languages = argostranslate.translate.get_installed_languages()
    except Exception:
        return pairs
    for source in languages:
        for target in languages:
            if source.code == target.code:
                continue
            try:
                source.get_translation(target)
            except Exception:
                continue
            pairs.add((source.code, target.code))
    return pairs


def install_translation_pair(source: str, target: str) -> bool:
    if source == target:
        return True
    if (source, target) in installed_translation_pairs():
        return True
    argostranslate.package.update_package_index()
    package = next(
        (
            item
            for item in argostranslate.package.get_available_packages()
            if item.from_code == source and item.to_code == target
        ),
        None,
    )
    if package is None:
        return False
    path = package.download()
    argostranslate.package.install_from_path(path)
    return True


def required_translation_pairs(source_lang: str, target_lang: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    source = None if source_lang in {"", "auto"} else source_lang
    if source and source != "en":
        pairs.append((source, "en"))
    if target_lang != "en":
        pairs.append(("en", target_lang))
    return pairs


def language_resource_status() -> dict[str, Any]:
    pairs = installed_translation_pairs()
    source_ready = {"auto", "en"}
    target_ready = {"en"}
    for source, target in pairs:
        if target == "en":
            source_ready.add(source)
        if source == "en":
            target_ready.add(target)
    return {
        "installed_pairs": sorted([{"source": source, "target": target} for source, target in pairs], key=lambda item: (item["source"], item["target"])),
        "source_ready": sorted(source_ready),
        "target_ready": sorted(target_ready),
    }


def load_store() -> dict[str, Any]:
    if not STORE_PATH.exists():
        return {}
    try:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_store(store: dict[str, Any]) -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "success": True,
        "project": "케케더빙",
        "backend": "python",
        "max_upload_mb": MAX_UPLOAD_MB,
        "max_upload_bytes": MAX_UPLOAD_BYTES,
        "ffmpeg": shutil.which("ffmpeg"),
        "tts": "supertonic",
    }

@app.get("/api/config")
def config() -> dict[str, Any]:
    resources = language_resource_status()
    return {
        "success": True,
        "max_upload_mb": MAX_UPLOAD_MB,
        "max_upload_bytes": MAX_UPLOAD_BYTES,
        "target_languages": SUPERTONIC_LANGUAGES,
        "voices": SUPERTONIC_VOICES,
        "subtitle_styles": [{"code": item["code"], "label": item["label"]} for item in SUBTITLE_STYLES],
        "subtitle_positions": [{"code": item["code"], "label": item["label"]} for item in SUBTITLE_POSITIONS],
        "source_languages": [{"code": "auto", "label": "Auto detect"}, *SUPERTONIC_LANGUAGES],
        "language_resources": resources,
        "default_target_lang": os.getenv("DEFAULT_TARGET_LANG", "en"),
        "default_source_lang": os.getenv("DEFAULT_SOURCE_LANG", "auto"),
        "default_voice": os.getenv("SUPERTONIC_VOICE", "M1"),
        "default_subtitle_style": os.getenv("SUBTITLE_STYLE", "bold"),
        "default_subtitle_position": os.getenv("SUBTITLE_POSITION", "bottom"),
        "default_subtitle_size": validate_subtitle_size(os.getenv("SUBTITLE_SIZE", "100")),
    }


@app.get("/api/video-sites")
def video_sites() -> dict[str, Any]:
    try:
        from yt_dlp.extractor import gen_extractors
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"yt-dlp is required: {exc}") from exc

    sites = sorted(
        {
            str(getattr(extractor, "IE_NAME", "")).replace(":", " / ")
            for extractor in gen_extractors()
            if getattr(extractor, "IE_NAME", None)
        },
        key=str.lower,
    )
    return {
        "success": True,
        "count": len(sites),
        "sites": sites,
    }


@app.post("/api/download-language-resources")
async def download_language_resources(request: Request) -> dict[str, Any]:
    payload = await request.json()
    source_lang = str(payload.get("source_lang") or "auto")
    target_lang = str(payload.get("target_lang") or os.getenv("DEFAULT_TARGET_LANG", "en"))
    if source_lang not in {"", "auto"}:
        validate_source_lang(source_lang)
    if target_lang not in SUPERTONIC_LANGUAGE_CODES:
        raise HTTPException(status_code=400, detail=f"Unsupported target language: {target_lang}")

    before = installed_translation_pairs()
    results = []
    for source, target in required_translation_pairs(source_lang, target_lang):
        ok = install_translation_pair(source, target)
        results.append({"source": source, "target": target, "installed": ok})
    after = installed_translation_pairs()
    return {
        "success": all(item["installed"] for item in results),
        "translation_pairs": results,
        "language_resources": language_resource_status(),
        "installed_pairs_count": len(after),
        "new_pairs_count": len(after - before),
        "font": LANGUAGE_SUBTITLE_FONTS.get(target_lang, SUBTITLE_FONT),
        "fonts": "Noto fonts are bundled in Docker and linked in the web UI.",
    }


@app.post("/api/open-output-folder")
def open_output_folder() -> dict[str, Any]:
    opener = shutil.which("open") or shutil.which("xdg-open")
    if not opener:
        return {"success": True, "path": str(OUTPUT_DIR), "opened": False}
    subprocess.Popen([opener, str(OUTPUT_DIR)])
    return {"success": True, "path": str(OUTPUT_DIR), "opened": True}


@app.get("/api/auth/me")
def auth_me() -> dict[str, Any]:
    return {"loggedIn": True, "authenticated": True, "user": {"email": "local@bbarit.dev"}}


@app.get("/api/access/check")
def access_check() -> dict[str, Any]:
    return {"ok": True, "has_access": True}


@app.get("/remote-api/access/check")
def remote_access_check() -> dict[str, Any]:
    return {"ok": True, "has_access": True}


@app.get("/remote-api/crawl-usage/check")
def crawl_usage_check() -> dict[str, Any]:
    return {"daily": 0, "monthly": 0, "daily_limit": 999999, "monthly_limit": 999999}


@app.post("/remote-api/crawl-usage/record")
async def crawl_usage_record(_: Request) -> dict[str, Any]:
    return {"success": True}


@app.get("/api/store/{key}")
def store_get(key: str) -> dict[str, Any]:
    store = load_store()
    return {"success": True, "value": store.get(key)}


@app.post("/api/store")
async def store_set(request: Request) -> dict[str, Any]:
    payload = await request.json()
    key = str(payload.get("key") or "")
    if not key:
        raise HTTPException(status_code=400, detail="key required")
    store = load_store()
    store[key] = payload.get("value")
    save_store(store)
    return {"success": True}


@app.delete("/api/store/{key}")
def store_delete(key: str) -> dict[str, Any]:
    store = load_store()
    store.pop(key, None)
    save_store(store)
    return {"success": True}


@app.get("/api/xiaohongshu/history")
def xiaohongshu_history() -> dict[str, Any]:
    return {"success": True, "items": []}


@app.get("/api/settings")
def settings() -> dict[str, str]:
    return {"gemini_api_key": "local-python-backend"}


@app.post("/api/settings")
async def save_settings(_: Request) -> dict[str, Any]:
    return {"success": True, "mode": "local-python-backend"}


@app.get("/api/gemini-key")
def gemini_key() -> dict[str, str]:
    return {"key": "local-python-backend"}


@app.post("/api/translate")
async def translate(request: Request) -> dict[str, Any]:
    payload = await request.json()
    text = str(payload.get("text") or "")
    target = str(payload.get("to") or payload.get("target_lang") or "zh")
    source = str(payload.get("from") or payload.get("source_lang") or ("ko" if target == "zh" else "zh"))
    translated = translate_with_pivot(text, source, target)
    return {"success": True, "text": text, "translated": translated, "to": target}


@app.post("/api/transcribe-translate")
async def transcribe_translate(request: Request) -> dict[str, Any]:
    payload = await request.json()
    target_lang = str(payload.get("target_lang") or "zh")
    source_lang = payload.get("source_lang") or None
    video_path = payload.get("video_path")
    title = str(payload.get("title") or "")
    desc = str(payload.get("desc") or "")
    duration = float(payload.get("duration") or 30)

    segments: list[dict[str, Any]] = []
    if video_path:
        try:
            from faster_whisper import WhisperModel
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"faster-whisper is not available: {exc}") from exc

        media = safe_path(str(video_path))
        model_size = os.getenv("WHISPER_MODEL", "small")
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        raw_segments, info = model.transcribe(
            str(media),
            language=source_lang,
            vad_filter=True,
            beam_size=5,
        )
        detected = source_lang or getattr(info, "language", None) or "en"
        for segment in raw_segments:
            segments.append(
                {
                    "start": float(segment.start),
                    "end": float(segment.end),
                    "text": segment.text.strip(),
                    "language": detected,
                }
            )

    if not segments:
        source_text = "\n".join(part for part in (title, desc) if part).strip()
        if not source_text:
            raise HTTPException(status_code=400, detail="video_path or text metadata is required")
        translated = translate_with_pivot(source_text, "ko", target_lang)
        segments = [{"start": 0.0, "end": duration, "text": translated, "language": target_lang}]
        srt = to_srt(segments, target_lang)
    else:
        srt = to_srt(segments, target_lang)

    return {"success": True, "srt": srt, "segments": segments, "target_lang": target_lang}


@app.post("/api/upload-video")
async def upload_video(file: UploadFile = File(...)) -> dict[str, Any]:
    output = save_upload(file)
    return media_payload(output)


def media_payload(path: Path) -> dict[str, Any]:
    width, height = media_dimensions(path)
    return {
        "success": True,
        "source_id": path.stem,
        "title": path.stem,
        "video_path": str(path),
        "play_url": f"/api/media/uploads/{path.name}",
        "video_duration": media_duration(path),
        "width": width,
        "height": height,
    }


def save_upload(file: UploadFile, *, max_bytes: int = MAX_UPLOAD_BYTES) -> Path:
    name = Path(file.filename or "upload.mp4").name
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(name).stem).strip("._") or "upload"
    suffix = Path(name).suffix.lower() or ".mp4"
    if suffix not in {".mp4", ".mov", ".m4v", ".webm", ".mkv"}:
        raise HTTPException(status_code=400, detail="Unsupported video file.")
    output = UPLOAD_DIR / f"{stem}_{int(time.time()*1000)}{suffix}"
    total = 0
    with output.open("wb") as handle:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if max_bytes and total > max_bytes:
                handle.close()
                output.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail=f"Upload limit is {MAX_UPLOAD_MB}MB.")
            handle.write(chunk)
    return output


def download_remote_video(url: str) -> Path:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=400, detail="A valid http or https video URL is required.")

    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", parsed.netloc).strip("._") or "remote"
    output_template = str(UPLOAD_DIR / f"{stem}_{int(time.time()*1000)}.%(ext)s")
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--no-playlist",
        "-f",
        "bv*[height<=1080]+ba/b[height<=1080]/b",
        "--merge-output-format",
        "mp4",
        "-o",
        output_template,
        url,
    ]
    if MAX_UPLOAD_BYTES:
        command[5:5] = ["--max-filesize", str(MAX_UPLOAD_BYTES)]
    run_command(command, timeout=86400)
    candidates = sorted(UPLOAD_DIR.glob(f"{stem}_*"), key=lambda path: path.stat().st_mtime, reverse=True)
    for candidate in candidates:
        if candidate.suffix.lower() in {".mp4", ".mov", ".m4v", ".webm", ".mkv"}:
            if MAX_UPLOAD_BYTES and candidate.stat().st_size > MAX_UPLOAD_BYTES:
                candidate.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail=f"Downloaded video is over {MAX_UPLOAD_MB}MB.")
            return candidate
    raise HTTPException(status_code=500, detail="yt-dlp did not produce a supported video file.")


@app.post("/api/import-video-url")
async def import_video_url(request: Request) -> dict[str, Any]:
    payload = await request.json()
    url = str(payload.get("url") or "").strip()
    media = download_remote_video(url)
    result = media_payload(media)
    result["source_url"] = url
    return result


@app.post("/api/edit-video")
async def edit_video(request: Request) -> dict[str, Any]:
    payload = await request.json()
    media = safe_path(str(payload.get("video_path") or ""))
    start = max(0.0, float(payload.get("trim_start") or 0))
    end_value = payload.get("trim_end")
    end = float(end_value) if end_value not in (None, "") else 0.0
    blur = max(0.0, min(40.0, float(payload.get("blur_strength") or 0)))
    blur_box = payload.get("blur_box") if isinstance(payload.get("blur_box"), dict) else {}

    source_duration = media_duration(media)
    if end <= 0 or end > source_duration:
        end = source_duration
    if end and end <= start:
        raise HTTPException(status_code=400, detail="Trim end must be after trim start.")

    output = UPLOAD_DIR / f"edited_{media.stem}_{int(time.time()*1000)}.mp4"
    args = ["ffmpeg", "-y"]
    if start > 0:
        args += ["-ss", f"{start:.3f}"]
    args += ["-i", str(media)]
    if end:
        args += ["-t", f"{max(0.1, end - start):.3f}"]
    if blur > 0 and blur_box:
        width, height = media_dimensions(media)
        x = max(0, min(width, int(float(blur_box.get("x") or 0) * width)))
        y = max(0, min(height, int(float(blur_box.get("y") or 0) * height)))
        box_w = max(2, min(width - x, int(float(blur_box.get("width") or 0) * width)))
        box_h = max(2, min(height - y, int(float(blur_box.get("height") or 0) * height)))
        if width and height and box_w > 2 and box_h > 2:
            args += [
                "-filter_complex",
                f"[0:v]split[base][crop];[crop]crop={box_w}:{box_h}:{x}:{y},boxblur={blur:.1f}:1[blurred];[base][blurred]overlay={x}:{y}[v]",
                "-map",
                "[v]",
                "-map",
                "0:a?",
            ]
        else:
            args += ["-map", "0:v", "-map", "0:a?"]
    else:
        args += ["-map", "0:v", "-map", "0:a?"]
    args += [
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "20",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(output),
    ]
    run_command(args, timeout=86400)
    result = media_payload(output)
    result["edited"] = True
    result["trim_start"] = start
    result["trim_end"] = end
    result["blur_strength"] = blur
    return result


def transcribe_segments(media: Path, target_lang: str, source_lang: str | None = None) -> tuple[str, list[dict[str, Any]]]:
    try:
        from faster_whisper import WhisperModel
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"faster-whisper is not available: {exc}") from exc

    model_size = os.getenv("WHISPER_MODEL", "small")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    requested_lang = source_lang if source_lang and source_lang != "auto" else None
    raw_segments, info = model.transcribe(str(media), language=requested_lang, vad_filter=True, beam_size=5)
    detected_lang = requested_lang or getattr(info, "language", None) or "en"
    entries: list[dict[str, Any]] = []
    for segment in raw_segments:
        source_text = segment.text.strip()
        if not source_text:
            continue
        text = translate_with_pivot(source_text, detected_lang, target_lang)
        entries.append(
            {
                "start": float(segment.start),
                "end": float(segment.end),
                "source_text": source_text,
                "text": re.sub(r"\s+", " ", text).strip(),
                "language": target_lang,
            }
        )
    return detected_lang, entries


def get_supertonic_tts() -> Any:
    global _SUPERTONIC_TTS
    if _SUPERTONIC_TTS is None:
        try:
            from supertonic import TTS
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"supertonic is required: {exc}") from exc
        _SUPERTONIC_TTS = TTS(auto_download=True)
    return _SUPERTONIC_TTS


def synthesize_tts(text: str, out_wav: Path, *, lang: str, voice: str | None = None) -> None:
    if lang not in SUPERTONIC_LANGUAGE_CODES:
        raise HTTPException(status_code=400, detail=f"Unsupported Supertonic language: {lang}")
    selected_voice = voice or os.getenv("SUPERTONIC_VOICE", "M1")
    if selected_voice not in SUPERTONIC_VOICE_CODES:
        raise HTTPException(status_code=400, detail=f"Unsupported Supertonic voice: {selected_voice}")

    tts = get_supertonic_tts()
    style = tts.get_voice_style(voice_name=selected_voice)
    with tempfile.TemporaryDirectory(dir=TMP_DIR) as tmp:
        raw_wav = Path(tmp) / "supertonic.wav"
        wav, _duration = tts.synthesize(
            text,
            voice_style=style,
            lang=lang,
            total_steps=int(os.getenv("SUPERTONIC_STEPS", "8")),
            speed=float(os.getenv("SUPERTONIC_SPEED", "1.05")),
            max_chunk_length=int(os.getenv("SUPERTONIC_MAX_CHUNK_LENGTH", "300")),
            silence_duration=float(os.getenv("SUPERTONIC_SILENCE_DURATION", "0.3")),
        )
        tts.save_audio(wav, str(raw_wav))
        run_command(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(raw_wav),
                "-ar",
                "24000",
                "-ac",
                "1",
                "-sample_fmt",
                "s16",
                str(out_wav),
            ],
            timeout=120,
        )


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as wav:
        frames = wav.getnframes()
        rate = wav.getframerate()
    return frames / rate if rate else 0.0


def atempo_chain(speed: float) -> str:
    speed = max(0.25, min(32.0, speed))
    parts: list[str] = []
    while speed > 2.0:
        parts.append("atempo=2.0")
        speed /= 2.0
    while speed < 0.5:
        parts.append("atempo=0.5")
        speed /= 0.5
    parts.append(f"atempo={speed:.4f}")
    return ",".join(parts)


def fit_wav_to_duration(input_wav: Path, output_wav: Path, target_seconds: float) -> None:
    target_seconds = max(0.15, target_seconds)
    current_seconds = wav_duration(input_wav)
    if current_seconds <= 0:
        shutil.copyfile(input_wav, output_wav)
        return

    speed = max(MIN_DUB_SPEED, min(MAX_DUB_SPEED, current_seconds / max(0.05, target_seconds * 0.96)))
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_wav),
            "-filter:a",
            atempo_chain(speed),
            "-ar",
            "24000",
            "-ac",
            "1",
            "-sample_fmt",
            "s16",
            str(output_wav),
        ],
        timeout=120,
    )


def wrap_subtitle_text(text: str, *, width: int = 28, max_lines: int = 2) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return ""
    wrapped = textwrap.wrap(clean, width=width, break_long_words=False, break_on_hyphens=False)
    if len(wrapped) <= max_lines:
        return "\n".join(wrapped)
    return "\n".join(wrapped)


def compact_for_timing(text: str, seconds: float) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    return clean


def split_long_entries(entries: list[dict[str, Any]], *, max_chars: int = 54, max_seconds: float = 3.2) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for entry in entries:
        text = re.sub(r"\s+", " ", str(entry.get("text") or "")).strip()
        start = float(entry.get("start") or 0)
        end = float(entry.get("end") or start)
        duration = max(0.15, end - start)
        if len(text) <= max_chars and duration <= max_seconds:
            entry = dict(entry)
            entry["text"] = compact_for_timing(text, duration)
            result.append(entry)
            continue

        parts = [part.strip() for part in re.split(r"(?<=[.!?。！？])\s+", text) if part.strip()]
        if len(parts) < 2:
            parts = textwrap.wrap(text, width=max_chars, break_long_words=False, break_on_hyphens=False) or [text]
        total_chars = max(1, sum(len(part) for part in parts))
        cursor = start
        for index, part in enumerate(parts):
            if index == len(parts) - 1:
                part_end = end
            else:
                part_duration = duration * (len(part) / total_chars)
                part_end = min(end, cursor + max(0.5, part_duration))
            new_entry = dict(entry)
            new_entry["start"] = cursor
            new_entry["end"] = part_end
            new_entry["text"] = compact_for_timing(part, part_end - cursor)
            result.append(new_entry)
            cursor = part_end
    return result


def rebalance_entry_timing(entries: list[dict[str, Any]], media_duration_seconds: float) -> list[dict[str, Any]]:
    adjusted = [dict(entry) for entry in entries]
    for index, entry in enumerate(adjusted):
        text = str(entry.get("text") or "")
        start = float(entry.get("start") or 0)
        end = float(entry.get("end") or start)
        duration = max(0.15, end - start)
        estimated_speech = max(0.35, len(text) / 13.0)
        wanted = min(estimated_speech / MAX_DUB_SPEED, estimated_speech / max(MIN_DUB_SPEED, 0.1))
        if wanted > duration:
            next_start = float(adjusted[index + 1].get("start")) if index + 1 < len(adjusted) else media_duration_seconds
            entry["end"] = min(next_start, media_duration_seconds, start + wanted)
    return adjusted


def build_aligned_dub(
    entries: list[dict[str, Any]],
    duration: float,
    out_wav: Path,
    *,
    lang: str,
    voice: str,
) -> None:
    sample_rate = 24000
    total_samples = max(int((duration + 1.0) * sample_rate), sample_rate)
    mix = bytearray(total_samples * 2)
    with tempfile.TemporaryDirectory(dir=TMP_DIR) as tmp:
        tmp_dir = Path(tmp)
        for index, entry in enumerate(entries):
            text = str(entry.get("text") or "").strip()
            if not text:
                continue
            speech = tmp_dir / f"tts_{index}.wav"
            fitted = tmp_dir / f"tts_{index}.fit.wav"
            synthesize_tts(text, speech, lang=lang, voice=voice)
            segment_seconds = max(0.15, float(entry.get("end") or 0) - float(entry.get("start") or 0))
            fit_wav_to_duration(speech, fitted, segment_seconds)
            with wave.open(str(fitted), "rb") as wav:
                frames = wav.readframes(wav.getnframes())
            start = max(0, int(float(entry.get("start") or 0) * sample_rate) * 2)
            end = min(len(mix), start + len(frames))
            if end > start:
                mix[start:end] = frames[: end - start]
    with wave.open(str(out_wav), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(bytes(mix))


def write_srt(entries: list[dict[str, Any]]) -> str:
    blocks = []
    for index, entry in enumerate(entries, start=1):
        text = wrap_subtitle_text(str(entry["text"]))
        blocks.append(
            f"{index}\n{fmt_srt_time(float(entry['start']))} --> {fmt_srt_time(float(entry['end']))}\n{text}"
        )
    return "\n\n".join(blocks)


def subtitle_filter(srt_path: Path, style: str, target_lang: str, position: str, size_percent: int) -> str:
    selected = next((item for item in SUBTITLE_STYLES if item["code"] == style), SUBTITLE_STYLES[1])
    selected_position = next((item for item in SUBTITLE_POSITIONS if item["code"] == position), SUBTITLE_POSITIONS[0])
    font = LANGUAGE_SUBTITLE_FONTS.get(target_lang, SUBTITLE_FONT)
    scaled_style = scale_subtitle_style(selected["force_style"], size_percent)
    return f"subtitles={srt_path}:force_style='FontName={font},{scaled_style},{selected_position['force_style']}'"


def scale_subtitle_style(style: str, size_percent: int) -> str:
    def replace_font_size(match: re.Match[str]) -> str:
        value = int(match.group(1))
        scaled = max(8, min(64, round(value * size_percent / 100)))
        return f"FontSize={scaled}"

    return re.sub(r"FontSize=(\d+)", replace_font_size, style)


@app.post("/api/auto-dub")
async def auto_dub(
    file: UploadFile = File(...),
    source_lang: str = "auto",
    target_lang: str = "en",
    voice: str = "M1",
    subtitle_style: str = "bold",
    subtitle_position: str = "bottom",
    subtitle_size: int = 100,
) -> dict[str, Any]:
    validate_video_options(target_lang, voice, subtitle_style)
    selected_subtitle_position = validate_subtitle_position(subtitle_position)
    selected_subtitle_size = validate_subtitle_size(subtitle_size)
    selected_source_lang = validate_source_lang(source_lang)
    media = save_upload(file)
    return dub_media(media, source_lang=selected_source_lang, target_lang=target_lang, voice=voice, subtitle_style=subtitle_style, subtitle_position=selected_subtitle_position, subtitle_size=selected_subtitle_size)


@app.post("/api/auto-dub-url")
async def auto_dub_url(request: Request) -> dict[str, Any]:
    payload = await request.json()
    url = str(payload.get("url") or "").strip()
    source_lang = str(payload.get("source_lang") or os.getenv("DEFAULT_SOURCE_LANG", "auto"))
    target_lang = str(payload.get("target_lang") or os.getenv("DEFAULT_TARGET_LANG", "en"))
    voice = str(payload.get("voice") or os.getenv("SUPERTONIC_VOICE", "M1"))
    subtitle_style = str(payload.get("subtitle_style") or os.getenv("SUBTITLE_STYLE", "bold"))
    subtitle_position = str(payload.get("subtitle_position") or os.getenv("SUBTITLE_POSITION", "bottom"))
    subtitle_size = validate_subtitle_size(payload.get("subtitle_size") or os.getenv("SUBTITLE_SIZE", "100"))
    validate_video_options(target_lang, voice, subtitle_style)
    selected_subtitle_position = validate_subtitle_position(subtitle_position)
    selected_source_lang = validate_source_lang(source_lang)
    media = download_remote_video(url)
    result = dub_media(media, source_lang=selected_source_lang, target_lang=target_lang, voice=voice, subtitle_style=subtitle_style, subtitle_position=selected_subtitle_position, subtitle_size=subtitle_size)
    result["source_url"] = url
    return result


@app.post("/api/auto-dub-existing")
async def auto_dub_existing(request: Request) -> dict[str, Any]:
    payload = await request.json()
    source_lang = str(payload.get("source_lang") or os.getenv("DEFAULT_SOURCE_LANG", "auto"))
    target_lang = str(payload.get("target_lang") or os.getenv("DEFAULT_TARGET_LANG", "en"))
    voice = str(payload.get("voice") or os.getenv("SUPERTONIC_VOICE", "M1"))
    subtitle_style = str(payload.get("subtitle_style") or os.getenv("SUBTITLE_STYLE", "bold"))
    subtitle_position = str(payload.get("subtitle_position") or os.getenv("SUBTITLE_POSITION", "bottom"))
    subtitle_size = validate_subtitle_size(payload.get("subtitle_size") or os.getenv("SUBTITLE_SIZE", "100"))
    validate_video_options(target_lang, voice, subtitle_style)
    selected_subtitle_position = validate_subtitle_position(subtitle_position)
    selected_source_lang = validate_source_lang(source_lang)
    media = safe_path(str(payload.get("video_path") or ""))
    return dub_media(media, source_lang=selected_source_lang, target_lang=target_lang, voice=voice, subtitle_style=subtitle_style, subtitle_position=selected_subtitle_position, subtitle_size=subtitle_size)


def dub_media(
    media: Path,
    *,
    source_lang: str | None,
    target_lang: str,
    voice: str,
    subtitle_style: str,
    subtitle_position: str,
    subtitle_size: int,
) -> dict[str, Any]:
    duration = media_duration(media)
    detected_source_lang, entries = transcribe_segments(media, target_lang, source_lang)
    if not entries:
        raise HTTPException(status_code=400, detail="No speech was detected.")
    entries = split_long_entries(entries)
    entries = rebalance_entry_timing(entries, duration or max(float(entry["end"]) for entry in entries))

    timeline_duration = duration or max(float(entry["end"]) for entry in entries)
    srt_text = write_srt(entries)
    output_path = OUTPUT_DIR / f"kekedubing_{media.stem}_{int(time.time()*1000)}.mp4"
    with tempfile.TemporaryDirectory(dir=TMP_DIR) as tmp:
        tmp_dir = Path(tmp)
        dub_wav = tmp_dir / "dub.wav"
        srt_path = tmp_dir / "subs.srt"
        build_aligned_dub(entries, timeline_duration, dub_wav, lang=target_lang, voice=voice)
        srt_path.write_text(srt_text, encoding="utf-8")
        run_command(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(media),
                "-i",
                str(dub_wav),
                "-vf",
                subtitle_filter(srt_path, subtitle_style, target_lang, subtitle_position, subtitle_size),
                "-map",
                "0:v",
                "-map",
                "1:a",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "20",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                str(output_path),
            ],
            timeout=86400,
        )

    return {
        "success": True,
        "source_language": detected_source_lang,
        "target_language": target_lang,
        "voice": voice,
        "subtitle_style": subtitle_style,
        "subtitle_position": subtitle_position,
        "subtitle_size": subtitle_size,
        "srt": srt_text,
        "segments": entries,
        "input_path": str(media),
        "output_path": str(output_path),
        "play_url": f"/api/media/merged/{output_path.name}",
        "download_url": f"/api/media/merged/{output_path.name}",
    }


@app.post("/api/tts")
async def tts(request: Request) -> dict[str, Any]:
    payload = await request.json()
    text = str(payload.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text required")

    with tempfile.TemporaryDirectory(dir=TMP_DIR) as tmp:
        out_wav = Path(tmp) / "speech.wav"
        lang = str(payload.get("lang") or payload.get("target_lang") or os.getenv("DEFAULT_TARGET_LANG", "en"))
        voice = str(payload.get("voice") or os.getenv("SUPERTONIC_VOICE", "M1"))
        synthesize_tts(text, out_wav, lang=lang, voice=voice)
        encoded = base64.b64encode(out_wav.read_bytes()).decode("ascii")
    return {"success": True, "audio_data": encoded, "mime_type": "audio/wav", "voice": voice, "lang": lang}


@app.post("/api/voice-preview")
async def voice_preview(request: Request) -> dict[str, Any]:
    payload = await request.json()
    lang = str(payload.get("lang") or os.getenv("DEFAULT_TARGET_LANG", "en"))
    voice = str(payload.get("voice") or os.getenv("SUPERTONIC_VOICE", "M1"))
    text = str(payload.get("text") or "This is a Supertonic voice preview.").strip()
    with tempfile.TemporaryDirectory(dir=TMP_DIR) as tmp:
        out_wav = Path(tmp) / "preview.wav"
        synthesize_tts(text, out_wav, lang=lang, voice=voice)
        encoded = base64.b64encode(out_wav.read_bytes()).decode("ascii")
    return {"success": True, "audio_data": encoded, "mime_type": "audio/wav", "voice": voice, "lang": lang}


@app.post("/api/bgm")
async def bgm(request: Request) -> dict[str, Any]:
    payload = await request.json()
    duration = max(1.0, min(float(payload.get("duration") or 30), 600.0))
    style = str(payload.get("style") or "calm")
    provider = str(payload.get("provider") or os.getenv("BGM_PROVIDER", "procedural")).lower()
    if provider == "musicgen":
        try:
            from scipy.io import wavfile
            from transformers import pipeline
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="MusicGen provider is not installed. Build with ENABLE_MUSICGEN=1.",
            ) from exc
        max_duration = min(duration, float(os.getenv("MUSICGEN_MAX_SECONDS", "20")))
        with tempfile.TemporaryDirectory(dir=TMP_DIR) as tmp:
            raw_wav = Path(tmp) / "musicgen.wav"
            out_wav = Path(tmp) / "bgm.wav"
            pipe = pipeline("text-to-audio", os.getenv("MUSICGEN_MODEL", "facebook/musicgen-small"))
            music = pipe(
                audio_prompt(style, max_duration),
                forward_params={"do_sample": True, "max_new_tokens": int(max_duration * 50)},
            )
            wavfile.write(str(raw_wav), rate=music["sampling_rate"], data=music["audio"])
            run_command(
                [
                    "ffmpeg",
                    "-y",
                    "-stream_loop",
                    "-1",
                    "-i",
                    str(raw_wav),
                    "-t",
                    f"{duration:.2f}",
                    "-filter:a",
                    "volume=0.18,afade=t=in:d=1,afade=t=out:d=2",
                    "-ar",
                    "24000",
                    "-ac",
                    "1",
                    str(out_wav),
                ],
                timeout=300,
            )
            encoded = base64.b64encode(out_wav.read_bytes()).decode("ascii")
        return {"success": True, "audio_data": encoded, "mime_type": "audio/wav", "provider": "musicgen"}

    freq = {"calm": "220", "upbeat": "330", "cinematic": "146"}.get(style, "220")
    with tempfile.TemporaryDirectory(dir=TMP_DIR) as tmp:
        out_wav = Path(tmp) / "bgm.wav"
        run_command(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency={freq}:sample_rate=44100:duration={duration}",
                "-filter:a",
                "volume=0.06,afade=t=in:d=1,afade=t=out:d=2",
                "-ar",
                "24000",
                "-ac",
                "1",
                str(out_wav),
            ],
            timeout=120,
        )
        encoded = base64.b64encode(out_wav.read_bytes()).decode("ascii")
    return {"success": True, "audio_data": encoded, "mime_type": "audio/wav", "provider": "procedural"}


@app.post("/api/merge-video")
async def merge_video(request: Request) -> dict[str, Any]:
    payload = await request.json()
    video_path = payload.get("video_path")
    if not video_path:
        raise HTTPException(status_code=400, detail="video_path required")
    media = safe_path(str(video_path))
    output_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(payload.get("output_name") or f"dubbed_{int(time.time()*1000)}"))
    if not output_name.endswith(".mp4"):
        output_name += ".mp4"
    output_path = OUTPUT_DIR / output_name

    audio_data = payload.get("audio_data") or ""
    srt_text = payload.get("srt_text") or ""
    with tempfile.TemporaryDirectory(dir=TMP_DIR) as tmp:
        tmp_dir = Path(tmp)
        inputs = ["-y", "-i", str(media)]
        filter_args: list[str] = []
        map_args = ["-map", "0:v"]
        audio_path: Path | None = None
        if audio_data:
            audio_path = tmp_dir / "dub.wav"
            audio_path.write_bytes(base64.b64decode(audio_data))
            inputs += ["-i", str(audio_path)]
            map_args += ["-map", "1:a", "-c:a", "aac", "-b:a", "192k", "-shortest"]
        else:
            map_args += ["-map", "0:a?", "-c:a", "copy"]

        video_codec = ["-c:v", "copy"]
        if srt_text.strip():
            srt_path = tmp_dir / "subs.srt"
            srt_path.write_text(srt_text, encoding="utf-8")
            filter_args = ["-vf", f"subtitles={srt_path}"]
            video_codec = ["-c:v", "libx264", "-preset", "fast", "-crf", "20"]

        args = ["ffmpeg", *inputs, *filter_args, *map_args, *video_codec, str(output_path)]
        run_command(args, timeout=900)

    return {
        "success": True,
        "output_path": str(output_path),
        "play_url": f"/api/media/merged/{output_path.name}",
        "thumbnail_url": "",
    }


@app.get("/api/media/merged/{name}")
def merged_media(name: str) -> FileResponse:
    path = (OUTPUT_DIR / Path(name).name).resolve()
    if not path.exists() or OUTPUT_DIR.resolve() not in path.parents:
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(path)


@app.get("/api/media/uploads/{name}")
def uploaded_media(name: str) -> FileResponse:
    path = (UPLOAD_DIR / Path(name).name).resolve()
    if not path.exists() or UPLOAD_DIR.resolve() not in path.parents:
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(path)


@app.get("/")
def index() -> Response:
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        return JSONResponse({"success": False, "error": f"WEB_DIR not found: {WEB_DIR}"}, status_code=500)
    return Response(
        index_path.read_text(encoding="utf-8"),
        media_type="text/html",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"},
    )


if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
else:
    @app.get("/")
    def missing_web() -> JSONResponse:
        return JSONResponse({"success": False, "error": f"WEB_DIR not found: {WEB_DIR}"}, status_code=500)
