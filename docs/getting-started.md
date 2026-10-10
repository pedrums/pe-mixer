# Installation & Schnellstart

## 1. Voraussetzungen
- [uv](https://github.com/astral-sh/uv)
- [FFmpeg](https://ffmpeg.org/) (für MP3-Export)

## 2. Installation
```bash
uv sync
```

## 3. Befehle

### Mix ausführen (Single Mode)
```bash
uv run pe-mixer mix /pfad/zum/song --setup probe_Matscher
```

### Bulk-Mix (Alle Unterordner als Songs verarbeiten)
```bash
uv run pe-mixer mix /pfad/zu/proben --bulk --setup probe_Matscher
```

### Spuren für Debugging exportieren (`--export-tracks`)
Um die Spuren stufenweise nach jedem DSP-Schritt in `tracks-tmp/` zu untersuchen:
```bash
uv run pe-mixer mix /pfad/zum/song --setup probe_Matscher --export-tracks --force
```

### Anfangs-Knacken entfernen (`--cut`)
Überspringt standardmäßig die ersten `0.5` Sekunden (zum Deaktivieren `--cut 0.0`):
```bash
uv run pe-mixer mix /pfad/zum/song --setup probe_Matscher --cut 0.5
```
