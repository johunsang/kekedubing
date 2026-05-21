# kekedubing

`kekedubing`은 영상 파일 또는 지원 사이트의 영상 URL을 로컬 서버에서 가져와 번역, 더빙, 자막 번인, 간단한 블러 편집까지 처리하는 오픈소스 도구입니다.

API 사용을 최소화하고 가능한 한 로컬 모델과 로컬 실행 환경을 사용하도록 설계했습니다.

## 핵심 기능

- 로컬 영상 업로드
- 지원 사이트 영상 URL 가져오기
- 지원 사이트 1,800개 이상 검색 모달
- 사이트 카테고리 필터: Social, Video, Music, News, Sports, Learning, Adult, Other
- 원본/다운로드 영상 미리보기
- 영상 위에 사각형 블러 영역 직접 그리기
- 소스 언어 자동 감지 또는 직접 선택
- 타겟 언어 선택
- 필요한 번역 모델 다운로드 버튼
- Supertonic 음성 선택 및 미리듣기
- 자막 위치 선택: Bottom, Lower third, Middle, Top
- 자막 크기 조절
- 35개 자막 스타일 프리셋
- 결과 영상 다운로드
- 결과 폴더 바로 열기

## 기술 스펙

| 영역 | 기술 |
| --- | --- |
| Backend | Python, FastAPI, Uvicorn |
| Frontend | 단일 HTML/CSS/JavaScript 앱 |
| Speech-to-text | faster-whisper |
| Translation | Argos Translate 로컬 모델 |
| Text-to-speech | Supertonic |
| Video processing | FFmpeg, FFprobe |
| URL import | yt-dlp |
| Subtitle rendering | FFmpeg subtitles filter, ASS force_style |
| Fonts | Noto font packages, Google Noto Fonts |
| Container | Docker, Docker Compose |

## 처리 파이프라인

 1. 파일 업로드 또는 영상 URL 입력
 2. 서버가 영상을 저장하거나 `yt-dlp`로 다운로드
 3. 원본 영상을 미리보기로 표시
 4. 필요하면 사각형 블러 영역 적용
 5. Whisper가 음성을 텍스트로 변환
 6. Argos Translate가 타겟 언어로 번역
 7. Supertonic이 번역문을 음성으로 합성
 8. 구간 길이에 맞춰 더빙 속도 조정
 9. FFmpeg가 더빙 오디오와 자막을 영상에 번인
10. 결과 MP4 다운로드

## 로컬 모델과 리소스

번역 모델은 처음부터 전부 받지 않습니다. 앱에서 타겟 언어 옆 `Download` 버튼을 누르면 현재 선택한 소스/타겟 언어에 필요한 Argos 모델을 내려받습니다.

이미 설치된 언어는 선택 목록에 `(Installed)`로 표시됩니다.

더빙 속도는 너무 빠르거나 느려지지 않도록 기본 범위가 있습니다.

```text
MIN_DUB_SPEED=0.85
MAX_DUB_SPEED=1.75
```

## 실행 주소

```text
https://127.0.0.1:8801/
```

로컬 개발 인증서를 사용하므로 브라우저에서 인증서 경고가 나올 수 있습니다.

## Docker 실행

```bash
docker compose up --build
```

## Docker 없이 Mac 실행

```bash
chmod +x scripts/run-local-mac.command
./scripts/run-local-mac.command
```

또는 Finder에서 `scripts/run-local-mac.command`를 더블클릭합니다.

## Docker 없이 Windows 실행

PowerShell을 프로젝트 폴더에서 열고 실행합니다.

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\run-local-windows.ps1
```

## 환경 변수

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `MAX_UPLOAD_MB` | `0` | 0이면 업로드 크기 제한 없음 |
| `WHISPER_MODEL` | `small` | faster-whisper 모델 크기 |
| `DEFAULT_SOURCE_LANG` | `auto` | 기본 소스 언어 |
| `DEFAULT_TARGET_LANG` | `en` | 기본 타겟 언어 |
| `SUPERTONIC_VOICE` | `M1` | 기본 Supertonic 목소리 |
| `SUBTITLE_STYLE` | `bold` | 기본 자막 스타일 |
| `SUBTITLE_POSITION` | `bottom` | 기본 자막 위치 |
| `SUBTITLE_SIZE` | `100` | 기본 자막 크기 퍼센트 |
| `SUBTITLE_FONT` | `Noto Sans` | 기본 자막 폰트 |
| `MIN_DUB_SPEED` | `0.85` | 더빙 최소 배속 |
| `MAX_DUB_SPEED` | `1.75` | 더빙 최대 배속 |

## 출력 폴더

```text
data/output/merged
```

앱의 `Open output folder` 버튼으로 바로 열 수 있습니다.

## 주의

- 긴 영상은 Whisper, TTS, FFmpeg 인코딩 때문에 오래 걸릴 수 있습니다.
- CPU만 사용하는 환경에서는 첫 실행과 긴 영상 처리가 느릴 수 있습니다.
- URL 다운로드는 사이트 정책과 네트워크 상태에 따라 실패할 수 있습니다.
- 다운로드/더빙할 영상의 권리는 사용자가 직접 확인해야 합니다.

## 라이선스

MIT License