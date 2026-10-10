# TODO - pe-flac-mixer (Stand: 09.10.2026)

## Bisherige Erfolge
1. **WAV-Dateien Integration**: Projekt unterstützt FLAC und WAV vollständig.
2. **Endungsunabhängiges Setup-Matching**: Setups in `setups/*.yml` können nun ohne Dateiendung konfiguriert werden; das Tool matcht Spuren flexibel unabhängig von `.flac` oder `.wav`.
3. **Setup-Dateien bereinigt**: Alle Beispiel-Setups (`probe.yml`, `gig.yml`, `probe_Matscher.yml`, `probe_Mattl.yml`) wurden auf endungslose Kanalschlüssel umgestellt.
4. **--force Schalter**: Hinzugefügt für `analyze` und `mix`, um gecachte `_analysis.json`-Dateien zu ignorieren und frisch zu analysieren/rendern.
5. **E-Gitarren-Pegel**: E-Gitarren-Gruppe im Setup auf `-20 LUFS` angehoben.

---

## Aktuelles Problem & Nächste Schritte für Morgen
- **Problem**: Der Versuch einer blockweisen Einzelspur-Normalisierung, Gates und Kompression direkt im Python-Streaming-Renderer führte zu **Rauschen und Knacksen**.
- **Lösungsidee für morgen**: 
  - Die manuelle DSP-Kette (Gate + Kompressor + Pre/Post-Normalisierung pro Block) im Renderer entfernen und stattdessen auf saubere, stabile Gain- und Kompressionsmethoden zurückgreifen.
  - Alternativ prüfen, ob die Dynamikverdichtung eleganter über die bestehenden Setup-Gruppen-Level und den Master-Limiter geregelt werden kann, statt rohe Einzelspuren in Python blockweise zu verändern.
  - Das `--force` Feature nutzen, um saubere Testläufe zu machen.
