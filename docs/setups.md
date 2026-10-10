# Setups & Konfiguration

Setups definieren das Routing, Instrumenten-Zuordnungen, Panning und Ziel-Lautheiten (LUFS) pro Gruppe.

## Setup-Dateien
Beispiel-Setups liegen unter `setups/` (z. B. `probe_Matscher.yml`, `probe_Mattl.yml`).

### Gruppen-Lautheiten (`group_levels`)
```yaml
group_levels:
  vocals lead: -10.0      # Lead-Gesang (präsent im Vordergrund)
  vocals background: -22.0 # Background / Chor
  drums: -21.0
  bass: -21.0
  guitars: -23.0
  keys: -23.0
  other: -23.0
```

### Lokale Setups (Bulk-Modus Overrides)
Im Bulk-Modus sucht der Mixer in jedem Song-Unterordner automatisch nach einer `setup*.yml` (z. B. `setup_Matscher.yml`), um individuelle Besetzungen pro Song zu unterstützen.
