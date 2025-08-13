import subprocess
import os
import json
import sys

# --- Chemins des fichiers ---
INPUT_PATHS_JSON = os.path.join("data", "downloaded_clip_paths.json")
OUTPUT_VIDEO_PATH = os.path.join("output", "compiled_video.mp4")
CLIPS_LIST_TXT = os.path.join("data", "clips_list.txt")

# --- Chemins intro / outro ---
ASSETS_DIR = os.path.join("assets")
INTRO_PATH = os.path.join(ASSETS_DIR, "intro.mp4")
OUTRO_PATH = os.path.join(ASSETS_DIR, "outro.mp4")

MAX_TOTAL_CLIPS = 35

def compile_video():
    print("🎬 Démarrage compilation...")

    # Vérification des fichiers intro/outro
    if not os.path.exists(INTRO_PATH):
        print(f"❌ Fichier intro manquant : {INTRO_PATH}")
        sys.exit(1)
    if not os.path.exists(OUTRO_PATH):
        print(f"❌ Fichier outro manquant : {OUTRO_PATH}")
        sys.exit(1)

    # Vérification clips JSON
    if not os.path.exists(INPUT_PATHS_JSON):
        print(f"❌ {INPUT_PATHS_JSON} introuvable.")
        sys.exit(1)

    with open(INPUT_PATHS_JSON, "r", encoding="utf-8") as f:
        clips_info = json.load(f)

    if not clips_info:
        print("⚠️ Aucun clip à compiler.")
        sys.exit(0)

    # Filtrer clips valides
    final_clips = [c for c in clips_info if c.get("path") and c.get("duration", 0) > 0]
    final_clips = final_clips[:MAX_TOTAL_CLIPS]

    if not final_clips:
        print("⚠️ Aucun clip valide.")
        sys.exit(0)

    # Création du fichier de concat
    with open(CLIPS_LIST_TXT, "w") as f:
        # Intro
        f.write(f"file '{os.path.abspath(INTRO_PATH)}'\n")
        # Clips
        for c in final_clips:
            f.write(f"file '{os.path.abspath(c['path'])}'\n")
        # Outro
        f.write(f"file '{os.path.abspath(OUTRO_PATH)}'\n")

    # Commande FFmpeg
    final_cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", CLIPS_LIST_TXT,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-y", OUTPUT_VIDEO_PATH
    ]
    subprocess.run(final_cmd, check=True)
    print(f"✅ Compilation terminée : {OUTPUT_VIDEO_PATH}")

if __name__ == "__main__":
    compile_video()
