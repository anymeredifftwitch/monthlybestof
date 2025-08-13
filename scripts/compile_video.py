#!/usr/bin/env python3
import subprocess
import os
import json
import sys
import shutil

# --- Chemins des fichiers ---
INPUT_PATHS_JSON = os.path.join("data", "downloaded_clip_paths.json")
OUTPUT_VIDEO_PATH = os.path.join("output", "compiled_video.mp4")
CLIPS_LIST_TXT = os.path.join("data", "clips_list.txt")

# --- Chemins intro / outro ---
ASSETS_DIR = os.path.join("assets")
INTRO_PATH = os.path.join(ASSETS_DIR, "intro.mp4")
OUTRO_PATH = os.path.join(ASSETS_DIR, "outro.mp4")

# Dossier temporaire pour les fichiers préparés (timestamps régénérés, codec unifié)
PREP_DIR = os.path.join("data", "concat_prep")

MAX_TOTAL_CLIPS = 35

# Paramètres d'encodage standardisés pour éviter les problèmes de timestamps / codecs
ENCODE_VIDEO_CODEC = "libx264"
ENCODE_VIDEO_PRESET = "veryfast"
ENCODE_VIDEO_CRF = "18"
ENCODE_AUDIO_CODEC = "aac"
ENCODE_AUDIO_BITRATE = "192k"
ENCODE_AUDIO_RATE = "48000"
ENCODE_AUDIO_CHANNELS = "2"

def run(cmd, **kwargs):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True, **kwargs)

def prepare_file(input_path, output_path):
    """Réencode / remuxe le fichier pour standardiser codecs et timestamps."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-fflags", "+genpts",            # régénère les pts si besoin
        "-avoid_negative_ts", "make_zero",
        "-c:v", ENCODE_VIDEO_CODEC,
        "-preset", ENCODE_VIDEO_PRESET,
        "-crf", ENCODE_VIDEO_CRF,
        "-pix_fmt", "yuv420p",
        "-c:a", ENCODE_AUDIO_CODEC,
        "-b:a", ENCODE_AUDIO_BITRATE,
        "-ar", ENCODE_AUDIO_RATE,
        "-ac", ENCODE_AUDIO_CHANNELS,
        "-movflags", "+faststart",       # meilleur pour la lecture progressive
        output_path
    ]
    run(cmd)

def compile_video():
    print("🎬 Démarrage compilation (préparation + concat stable)...")

    # Vérifications basiques
    if not os.path.exists(INTRO_PATH):
        print(f"❌ Fichier intro manquant : {INTRO_PATH}")
        sys.exit(1)
    if not os.path.exists(OUTRO_PATH):
        print(f"❌ Fichier outro manquant : {OUTRO_PATH}")
        sys.exit(1)
    if not os.path.exists(INPUT_PATHS_JSON):
        print(f"❌ {INPUT_PATHS_JSON} introuvable.")
        sys.exit(1)

    with open(INPUT_PATHS_JSON, "r", encoding="utf-8") as f:
        clips_info = json.load(f)

    if not clips_info:
        print("⚠️ Aucun clip à compiler.")
        sys.exit(0)

    final_clips = [c for c in clips_info if c.get("path") and c.get("duration", 0) > 0]
    final_clips = final_clips[:MAX_TOTAL_CLIPS]

    if not final_clips:
        print("⚠️ Aucun clip valide.")
        sys.exit(0)

    # Préparer dossier temporaire
    if os.path.exists(PREP_DIR):
        shutil.rmtree(PREP_DIR)
    os.makedirs(PREP_DIR, exist_ok=True)

    prep_paths = []

    try:
        # 1) Préparer l'intro et l'outro (on standardise aussi)
        intro_prep = os.path.join(PREP_DIR, "000_intro_prep.mp4")
        outro_prep = os.path.join(PREP_DIR, "999_outro_prep.mp4")
        print("🔧 Préparation de l'intro...")
        prepare_file(INTRO_PATH, intro_prep)
        print("🔧 Préparation de l'outro...")
        prepare_file(OUTRO_PATH, outro_prep)
        prep_paths.append(intro_prep)

        # 2) Préparer chaque clip (réencodage standardisé)
        for idx, clip in enumerate(final_clips, start=1):
            src = clip["path"]
            # normaliser le nom (prefix pour garder l'ordre)
            dst = os.path.join(PREP_DIR, f"{idx:03d}_{os.path.basename(src)}")
            print(f"🔧 Préparation clip {idx}/{len(final_clips)} : {src}")
            prepare_file(src, dst)
            prep_paths.append(dst)

        prep_paths.append(outro_prep)

        # 3) Écrire la liste pour le concat demuxer
        os.makedirs(os.path.dirname(CLIPS_LIST_TXT), exist_ok=True)
        with open(CLIPS_LIST_TXT, "w", encoding="utf-8") as f:
            for p in prep_paths:
                f.write(f"file '{os.path.abspath(p)}'\n")

        # 4) Concaténation finale en copy (les fichiers ont déjà le même codec)
        print("🔗 Concaténation finale (mode fast) ...")
        os.makedirs(os.path.dirname(OUTPUT_VIDEO_PATH), exist_ok=True)
        concat_cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", CLIPS_LIST_TXT,
            "-c", "copy",      # copy parce qu'on a déjà standardisé codecs & metadata
            "-movflags", "+faststart",
            "-y",
            OUTPUT_VIDEO_PATH
        ]
        run(concat_cmd)

        print(f"✅ Compilation terminée : {OUTPUT_VIDEO_PATH}")

    except subprocess.CalledProcessError as e:
        print("❌ Erreur FFmpeg :", e)
        sys.exit(1)
    except Exception as e:
        print("❌ Erreur inattendue :", e)
        sys.exit(1)
    finally:
        # Nettoyage optionnel : on laisse les fichiers préparés si tu veux debug,
        # sinon décommente la ligne suivante pour tout supprimer.
        # shutil.rmtree(PREP_DIR, ignore_errors=True)
        pass

if __name__ == "__main__":
    compile_video()
