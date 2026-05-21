# kekedubing install

## Docker

```bash
docker compose up --build
```

Open:

```text
https://127.0.0.1:8801/
```

## Mac without Docker

Double-click:

```text
scripts/run-local-mac.command
```

Or run:

```bash
chmod +x scripts/run-local-mac.command
./scripts/run-local-mac.command
```

## Windows without Docker

Open PowerShell in this folder and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\run-local-windows.ps1
```

Then open:

```text
https://127.0.0.1:8801/
```

The first run installs Python packages and can take a while. Language models can be downloaded from the app with the Download button beside Target language.
