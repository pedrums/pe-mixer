# CLI-Referenz

Der `pe-mixer` bietet folgende Hauptbefehle:

## `mix`
Rendert einen Rough Mix (Single oder Bulk).
```bash
uv run pe-mixer mix [INPUT_DIR] [OPTIONS]
```
**Optionen:**
- `--setup / -s`: Name des Setups (Default aus `.env` oder `probe`).
- `--output / -o`: Zielordner für das Ergebnis.
- `--bulk / -b`: Verarbeitet alle Unterordner als Songs.
- `--force / -f`: Ignoriert gecachte Analysen und berechnet neu.
- `--export-tracks`: Schreibt Einzelspuren nach jedem DSP-Schritt in `tracks-tmp/`.
- `--cut`: Sekunden, die am Anfang übersprungen werden (Default: `0.5`).

## `analyze`
Analysiert Spuren und zeigt Peak, LUFS und Crest-Faktor.
```bash
uv run pe-mixer analyze [INPUT_DIR]
```

## `create-setup`
Generiert ein neues YAML-Setup automatisch aus einem Ordner mit Multitrack-Dateien.
```bash
uv run pe-mixer create-setup --source [INPUT_DIR] --name [SETUP_NAME]
```

## `cut`
Schneidet Sekunden am Anfang einer Audio-Datei ab.
```bash
uv run pe-mixer cut [FILE] --sec [SECONDS]
```
