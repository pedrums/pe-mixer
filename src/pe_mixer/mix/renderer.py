"""Audio-Rendering und Summierung."""

import shutil
import subprocess
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import soundfile as sf

from pe_mixer.mix.dsp import (
    SimpleReverb,
    apply_gain,
    apply_highpass,
    compressor,
    create_highpass_sos,
    noise_gate,
    pan_mono_to_stereo,
    pan_stereo,
    peak_limiter,
)
from pe_mixer.mix.planner import MixPlan


def render_mix(
    tracks: dict[str, Path],
    mix_plan: MixPlan,
    output_dir: Path,
    base_name: str = "mix",
    block_size: int = 65536,
    force: bool = False,
    export_tracks: bool = False,
    cut_sec: float = 0.5,
    source_dir: Path | None = None,
) -> dict[str, Path]:
    """
    Rendert die Spuren nach dem Mixplan blockweise zu einer Summe mit Subgruppen-Processing:
    - Drums-Subgruppe mit Compressor & Reverb
    - Vocals-Subgruppe mit Compressor & Reverb
    - Master-Limiter & Normalisierung
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if not tracks:
        raise ValueError("Keine Spuren zum Mischen vorhanden.")

    # 1. Metadaten aller Spuren ermitteln (Samplerate, max. Frames)
    sound_files: dict[str, sf.SoundFile] = {}
    master_sr = None
    max_frames = 0

    try:
        for filename, path in tracks.items():
            f = sf.SoundFile(str(path))
            sound_files[filename] = f
            if master_sr is None:
                master_sr = f.samplerate
            elif f.samplerate != master_sr:
                raise ValueError(
                    f"Inkonsistente Samplerate bei {filename}: {f.samplerate} Hz (erwartet {master_sr} Hz)"
                )
            max_frames = max(max_frames, len(f))

        assert master_sr is not None

        # Calculate cut frames offset
        cut_frames = int(cut_sec * master_sr) if cut_sec > 0 else 0
        if cut_frames > 0:
            for f_obj in sound_files.values():
                seek_pos = min(cut_frames, len(f_obj))
                f_obj.seek(seek_pos)
            max_frames = max(0, max_frames - cut_frames)

        # 2. Filter und Zustände initialisieren
        filters: dict[str, tuple[np.ndarray, np.ndarray | None]] = {}
        for filename, params in mix_plan.tracks.items():
            if params.highpass_hz and params.highpass_hz > 15.0:
                sos = create_highpass_sos(params.highpass_hz, master_sr)
                filters[filename] = (sos, None)

        # 3. Subgruppen-Reverb initialisieren (subtil, um Verzerrung zu vermeiden)
        drums_reverb = SimpleReverb(sr=master_sr, room_size=0.25, decay_time_sec=1.2)
        vocals_reverb = SimpleReverb(sr=master_sr, room_size=0.3, decay_time_sec=1.5)
        guitars_keys_reverb = SimpleReverb(sr=master_sr, room_size=0.35, decay_time_sec=1.4)

        # Handle tracks-tmp directory if export_tracks is enabled
        tracks_tmp_base = None
        step_writers: dict[str, dict[str, sf.SoundFile]] = {}
        steps_list = [
            "01_raw_trimmed",
            "02_highpass",
            "04_gate",
            "05_compressor",
            "07_gain",
            "08_panned",
        ]

        if export_tracks:
            ref_dir = source_dir if source_dir and source_dir.is_dir() else output_dir
            tracks_tmp_base = ref_dir / "tracks-tmp"
            if force and tracks_tmp_base.exists():
                shutil.rmtree(tracks_tmp_base)
            
            tracks_tmp_base.mkdir(parents=True, exist_ok=True)
            for step in steps_list:
                step_dir = tracks_tmp_base / step
                step_dir.mkdir(parents=True, exist_ok=True)
                step_writers[step] = {}
                for filename in tracks.keys():
                    stem_name = Path(filename).stem
                    out_track_path = step_dir / f"{stem_name}.wav"
                    # Determine channels for writer based on whether panned/stereo or raw
                    # Raw tracks can be mono or stereo; let's check file info
                    f_obj = sound_files[filename]
                    ch_count = f_obj.channels
                    # After panning, blocks are always 2 channels (stereo). For steps 1-7, keep original channel count.
                    step_writers[step][filename] = sf.SoundFile(
                        str(out_track_path),
                        mode="w",
                        samplerate=master_sr,
                        channels=ch_count if step != "08_panned" else 2,
                        subtype="FLOAT",
                    )

        # 4. Temporäre Summen-Datei streamen mit Subgruppen
        temp_sum_path = output_dir / f".temp_{base_name}_sum.wav"
        with sf.SoundFile(
            str(temp_sum_path),
            mode="w",
            samplerate=master_sr,
            channels=2,
            subtype="FLOAT",
        ) as sum_out:
            frames_processed = 0
            while frames_processed < max_frames:
                current_block_len = min(block_size, max_frames - frames_processed)

                # Subgruppen-Puffer
                drums_block = np.zeros((current_block_len, 2), dtype=np.float32)
                vocals_block = np.zeros((current_block_len, 2), dtype=np.float32)
                guitars_keys_block = np.zeros((current_block_len, 2), dtype=np.float32)
                other_block = np.zeros((current_block_len, 2), dtype=np.float32)

                for filename, sf_obj in sound_files.items():
                    params = mix_plan.tracks.get(filename)
                    if not params:
                        continue

                    raw_block = sf_obj.read(current_block_len, dtype="float32")
                    if len(raw_block) == 0:
                        continue

                    block_len = len(raw_block)
                    if export_tracks:
                        step_writers["01_raw_trimmed"][filename].write(raw_block[:block_len])

                    # Highpass Filter
                    if filename in filters:
                        sos, zi = filters[filename]
                        filtered_block, new_zi = apply_highpass(raw_block, sos, zi)
                        filters[filename] = (sos, new_zi)
                        track_audio = filtered_block
                    else:
                        track_audio = raw_block

                    if export_tracks:
                        step_writers["02_highpass"][filename].write(track_audio[:block_len])

                    # Pro-Spur Kette: Gate -> Compressor (ohne künstliche Pre/Post-Normalisierung)
                    if params.compressor_enabled:
                        track_audio = noise_gate(
                            track_audio,
                            threshold_db=-40.0,
                            ratio=10.0,
                            attack_ms=2.0,
                            release_ms=80.0,
                            sr=master_sr,
                        )

                        if export_tracks:
                            step_writers["04_gate"][filename].write(track_audio[:block_len])

                        track_audio = compressor(
                            track_audio,
                            threshold_db=params.compressor_threshold,
                            ratio=params.compressor_ratio,
                            attack_ms=params.compressor_attack,
                            release_ms=params.compressor_release,
                            makeup_gain_db=params.compressor_makeup,
                            sr=master_sr,
                        )

                        if export_tracks:
                            step_writers["05_compressor"][filename].write(track_audio[:block_len])
                    else:
                        if export_tracks:
                            step_writers["04_gate"][filename].write(track_audio[:block_len])
                            step_writers["05_compressor"][filename].write(track_audio[:block_len])

                    # Gain anwenden
                    track_audio = apply_gain(track_audio, params.gain_db)

                    if export_tracks:
                        step_writers["07_gain"][filename].write(track_audio[:block_len])

                    # Panning (Mono vs Stereo)
                    if track_audio.ndim == 1 or track_audio.shape[1] == 1:
                        stereo_block = pan_mono_to_stereo(track_audio, params.pan)
                    else:
                        stereo_block = pan_stereo(track_audio, params.pan)

                    if export_tracks:
                        step_writers["08_panned"][filename].write(stereo_block[:block_len])

                    # Routen zu Subgruppe basierend auf Track-Gruppe
                    track_group = params.group.lower() if params.group else ""

                    if "drum" in track_group:
                        drums_block[:block_len] += stereo_block
                    elif "vocal" in track_group:
                        vocals_block[:block_len] += stereo_block
                    elif "guitar" in track_group or "key" in track_group:
                        guitars_keys_block[:block_len] += stereo_block
                    else:
                        other_block[:block_len] += stereo_block

                # Subgruppen-Processing: Compressor + Reverb
                # Drums: knackiger Sound mit kürzerem Release, sanfte Kompression
                drums_block = compressor(
                    drums_block,
                    threshold_db=-20.0,
                    ratio=2.5,
                    attack_ms=8.0,
                    release_ms=100.0,
                    makeup_gain_db=0.5,
                    sr=master_sr,
                )
                drums_wet = drums_reverb.process(drums_block)
                drums_block = 0.85 * drums_block + 0.15 * drums_wet

                # Vocals: wärmerer Sound mit längerer Release, sanfte Kompression
                vocals_block = compressor(
                    vocals_block,
                    threshold_db=-18.0,
                    ratio=2.0,
                    attack_ms=10.0,
                    release_ms=120.0,
                    makeup_gain_db=0.3,
                    sr=master_sr,
                )
                vocals_wet = vocals_reverb.process(vocals_block)
                vocals_block = 0.80 * vocals_block + 0.20 * vocals_wet

                # Guitars & Keys: Raumhall für E-Gitarren und Keyboards
                guitars_keys_block = compressor(
                    guitars_keys_block,
                    threshold_db=-18.0,
                    ratio=2.0,
                    attack_ms=10.0,
                    release_ms=100.0,
                    makeup_gain_db=0.3,
                    sr=master_sr,
                )
                guitars_keys_wet = guitars_keys_reverb.process(guitars_keys_block)
                guitars_keys_block = 0.85 * guitars_keys_block + 0.15 * guitars_keys_wet

                # Subgruppen auf Master summieren
                sum_block = drums_block + vocals_block + guitars_keys_block + other_block

                sum_out.write(sum_block)
                frames_processed += current_block_len

        # 5. Master Normalisierung & Limiter
        master_audio, _ = sf.read(str(temp_sum_path), dtype="float32")

        # LUFS der Summe messen
        meter = pyln.Meter(master_sr)
        try:
            current_sum_lufs = float(meter.integrated_loudness(master_audio))
        except Exception:
            current_sum_lufs = -24.0

        target_lufs = mix_plan.master.target_lufs
        if current_sum_lufs > -70.0:
            norm_gain_db = target_lufs - current_sum_lufs
            # Maximal +15 dB Master-Boost erlauben
            norm_gain_db = min(15.0, max(-18.0, norm_gain_db))
        else:
            norm_gain_db = 0.0

        # Master Gain anwenden
        master_audio = apply_gain(master_audio, norm_gain_db)

        # Master Limiter
        master_audio = peak_limiter(
            master_audio,
            ceiling_db=mix_plan.master.limiter_ceiling_db,
            sr=master_sr,
        )

        # 5. Export mit Dateinamen basierend auf base_name (nur MP3)
        mp3_path = output_dir / f"{base_name}.mp3"
        temp_flac_path = output_dir / f".temp_{base_name}.flac"

        # Temporäres FLAC für ffmpeg erstellen
        sf.write(str(temp_flac_path), master_audio, master_sr, format="FLAC", subtype="PCM_24")

        mp3_written = False
        if shutil.which("ffmpeg"):
            try:
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-i",
                        str(temp_flac_path),
                        "-b:a",
                        "192k",
                        str(mp3_path),
                    ],
                    check=True,
                    capture_output=True,
                )
                mp3_written = True
            except Exception:
                pass

        if not mp3_written:
            try:
                if "MP3" in sf.available_formats():
                    sf.write(str(mp3_path), master_audio, master_sr, format="MP3")
                    mp3_written = True
            except Exception:
                pass

        # Temporäres FLAC aufräumen
        if temp_flac_path.exists():
            temp_flac_path.unlink()

        # Temp Datei aufräumen
        if temp_sum_path.exists():
            temp_sum_path.unlink()

        output_files = {}
        if mp3_written and mp3_path.exists():
            output_files["mp3"] = mp3_path

        return output_files

    finally:
        if export_tracks and step_writers:
            for step_dict in step_writers.values():
                for writer in step_dict.values():
                    try:
                        writer.close()
                    except Exception:
                        pass
        for sf_obj in sound_files.values():
            sf_obj.close()
