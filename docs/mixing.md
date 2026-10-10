# DSP-Kette & Mixing-Engine

Der `pe-mixer` arbeitet mit einer stabilen, blockbasierten Streaming-DSP-Kette:

1. **Einlesen & Start-Cut (`--cut`)**: Überspringt Hardware-Einschaltklicks am Anfang (Standard: 0.5s).
2. **Highpass-Filter**: Entfernt Rumpel- und Infraschall-Frequenzen (angepasst an das Instrument).
3. **Kompressor (Optional)**: Sanfte Dynamikverdichtung pro Kanal (wenn in der YAML aktiviert).
4. **Setup-Gain & Panning**: Lautstärke-Anpassung und Stereoverteilung (Mono-Panning via Constant-Power Pan Law).
5. **Subgruppen-Processing**: Zusammenfassung in Subgruppen (Drums, Vocals, Guitars/Keys) mit dezenter Subgruppen-Kompression und Raumhall.
6. **Master Limiter & LUFS Normalisierung**: Integrierte LUFS-Messung (Ziel: -14 LUFS) und Brickwall-Peak-Limiter (-0.5 dBFS Ceiling) für einen sauberen, druckvollen MP3-Export.

---

## Pro-Tipp: Individuelle Instrumenten-Lautheiten (z.B. Akustikgitarre)

Wenn du möchtest, dass ein bestimmtes Instrument (wie z. B. die Akustikgitarre) einen ganz eigenen, von der Standard-Gruppe abweichenden Lautstärke-Pegel bekommt, kannst du in deiner Setup-YAML (`setups/*.yml`) eine **eigene Gruppe** anlegen:

1. Ordne dem Kanal in der YAML eine eigene Gruppe zu (z. B. `group: acoustic_guitar` statt `guitars`):
   ```yaml
   channels:
     "16 A-GITARRE":
       name: A-Gitarre
       group: acoustic_guitar
       type: mono
       pan: 0.45
   ```
2. Definiere für diese neue Gruppe direkt im `group_levels`-Block dein gewünschtes LUFS-Ziel:
   ```yaml
   group_levels:
     acoustic_guitar: -18.0   # Eigener Zielpegel (z.B. lauter oder leiser als die normale Gitarrengruppe)
   ```
