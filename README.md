# pe-mixer

Automatisches Grobmix-Tool für Bandproben und Live-Mitschnitte von Multitrack-WAV- und FLAC-Dateien.

> **Dokumentation:** Ausführliche Anleitungen, Konfigurationsmöglichkeiten und API-Referenzen findest du in der [pe-mixer Dokumentation](docs/index.md).

## Schnellstart

```bash
# Einzelner Song-Mix
uv run pe-mixer mix /pfad/zum/song --setup probe_Matscher

# Bulk-Modus (verarbeitet alle Unterordner als Songs)
uv run pe-mixer mix /pfad/zu/proben --bulk --setup probe_Matscher
```
