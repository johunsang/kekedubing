# 케케더빙

Local-first AI video translation, dubbing, subtitle burning, and simple video privacy editing.

**케케더빙** (`kekedubing`) is an open-source desktop-friendly web app for creators who want to translate and dub videos locally. Upload a video or paste a supported video URL, preview the source, draw a blur box if needed, choose source/target languages, select a Supertonic voice, pick subtitle style/position/size, then render a dubbed MP4 with burned subtitles.

한국어 문서: [README.ko.md](README.ko.md)

English docs: [README.en.md](README.en.md)

## Screenshots

![케케더빙 app overview](docs/screenshots/app-overview.png)

![Supported video sites modal](docs/screenshots/supported-sites-modal.png)

## Why

Many dubbing tools depend on cloud APIs, accounts, or paid workflows. **케케더빙** is built around a local server and local models where possible:

- speech recognition runs with `faster-whisper`
- translation runs with local `Argos Translate` models
- voice synthesis uses `Supertonic`
- video import uses `yt-dlp`
- rendering uses `FFmpeg`
- the UI runs as a simple local web app

## Features

- Upload local videos: `mp4`, `mov`, `m4v`, `webm`, `mkv`
- Import video URLs from 1,800+ supported sites
- Browse supported sites in a searchable modal
- Filter sites by category: Social, Video, Music, News, Sports, Learning, Adult, Other
- Preview the source video before rendering
- Draw a rectangular blur area directly on the preview video
- Auto-detect source language or choose it manually
- Choose target language
- Download missing local translation models from the UI
- Show already installed languages with `(Installed)`
- Choose and preview Supertonic voices
- Pick subtitle style from 35 presets
- Choose subtitle position: Bottom, Lower third, Middle, Top
- Adjust subtitle size
- Limit dub speed to avoid voices becoming too fast or too slow
- Burn subtitles into the final video
- Download the final MP4
- Open the output folder from the app

## Tech Stack

| Area | Technology |
| --- | --- |
| Backend | Python, FastAPI, Uvicorn |
| Frontend | Single-file HTML/CSS/JavaScript |
| Speech-to-text | faster-whisper |
| Translation | Argos Translate local models |
| Text-to-speech | Supertonic |
| Video processing | FFmpeg, FFprobe |
| URL import | yt-dlp |
| Subtitle rendering | FFmpeg subtitles filter, ASS `force_style` |
| Fonts | Noto fonts, Google Noto Fonts |
| Packaging | Docker, Docker Compose |

## Pipeline

1. Upload a file or paste a video URL.
2. The backend stores the upload or downloads the URL with `yt-dlp`.
3. The source video appears in the preview panel.
4. Optionally draw and apply a rectangular blur area.
5. `faster-whisper` transcribes the source audio.
6. `Argos Translate` translates text into the target language.
7. `Supertonic` synthesizes the translated voice.
8. The dubbed audio is speed-adjusted within a natural range.
9. `FFmpeg` burns subtitles and muxes the dubbed audio.
10. The final MP4 is saved to `data/output/merged`.

## Quick Start With Docker

```bash
git clone https://github.com/johunsang/kekedubing.git
cd kekedubing
docker compose up --build
```

Open:

```text
https://127.0.0.1:8801/
```

The app uses a local development certificate, so your browser may show a warning.

## Run Without Docker

### Mac

```bash
chmod +x scripts/run-local-mac.command
./scripts/run-local-mac.command
```

You can also double-click `scripts/run-local-mac.command` in Finder.

### Windows

Open PowerShell in the project folder:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\run-local-windows.ps1
```

## Language Resources

Translation models are installed on demand. Choose source and target languages, then click `Download` beside Target language.

Installed languages are marked with `(Installed)` in the language selectors.

## Subtitle Controls

The app supports:

- 35 subtitle style presets
- subtitle position: Bottom, Lower third, Middle, Top
- subtitle size percentage
- language-aware Noto font selection

## Dub Timing

The app prevents extreme speech speed by bounding dub tempo:

```text
MIN_DUB_SPEED=0.85
MAX_DUB_SPEED=1.75
```

You can tune those values with environment variables.

## Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `MAX_UPLOAD_MB` | `0` | `0` means no upload size limit |
| `WHISPER_MODEL` | `small` | faster-whisper model size |
| `DEFAULT_SOURCE_LANG` | `auto` | default source language |
| `DEFAULT_TARGET_LANG` | `en` | default target language |
| `SUPERTONIC_VOICE` | `M1` | default Supertonic voice |
| `SUBTITLE_STYLE` | `bold` | default subtitle style |
| `SUBTITLE_POSITION` | `bottom` | default subtitle position |
| `SUBTITLE_SIZE` | `100` | default subtitle size percent |
| `SUBTITLE_FONT` | `Noto Sans` | default subtitle font |
| `MIN_DUB_SPEED` | `0.85` | minimum dub tempo |
| `MAX_DUB_SPEED` | `1.75` | maximum dub tempo |
| `SUPERTONIC_STEPS` | `8` | Supertonic synthesis steps |
| `SUPERTONIC_SPEED` | `1.05` | Supertonic base speech speed |

## Output

Final rendered videos are saved here:

```text
data/output/merged
```

Use `Open output folder` in the UI to open it directly.

## Notes And Limits

- Long videos can take a long time because transcription, TTS, and FFmpeg rendering are CPU-heavy.
- The first run can be slow because models may need to download.
- URL imports depend on each site's availability and policy.
- Users are responsible for rights and permissions for downloaded or dubbed videos.
- Docker is recommended for reproducible installs, but Mac and Windows local scripts are included.

## SEO Keywords

local AI video dubbing, video translation, AI dubbing, subtitle burner, subtitle generator, faster-whisper, Whisper transcription, Argos Translate, Supertonic TTS, FFmpeg video tool, yt-dlp video import, multilingual dubbing, local video editor, shorts dubbing, creator localization.

## License

MIT License. See [LICENSE](LICENSE).
