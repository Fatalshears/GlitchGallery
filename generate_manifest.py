import os
import json
import subprocess
from datetime import datetime

NOTES_DIR = "notes"
PREVIEW_LENGTH = 800


def get_git_date(filepath):
    try:
        result = subprocess.run(
            ["git", "log", "--follow", "--format=%ai", "--", filepath],
            capture_output=True,
            text=True,
        )
        lines = result.stdout.strip().splitlines()
        if lines:
            # Last line = oldest commit = when the file was first added
            return lines[-1][:10]
    except Exception:
        pass
    return datetime.now().strftime("%Y-%m-%d")


def title_from_filename(filename):
    name = filename.removesuffix(".md")
    name = name.replace("-", " ").replace("_", " ")
    return name.title()


def generate_manifest():
    if not os.path.isdir(NOTES_DIR):
        print(f"Directory '{NOTES_DIR}' not found")
        return

    notes = []

    for filename in sorted(os.listdir(NOTES_DIR)):
        if not filename.endswith(".md"):
            continue

        filepath = os.path.join(NOTES_DIR, filename)

        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Skipping {filename}: {e}")
            continue

        notes.append(
            {
                "filename": filename,
                "title": title_from_filename(filename),
                "date": get_git_date(filepath),
                "preview": content[:PREVIEW_LENGTH],
            }
        )

    notes.sort(key=lambda n: n["date"], reverse=True)

    with open("manifest.json", "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)

    print(f"Generated manifest.json with {len(notes)} note(s)")


if __name__ == "__main__":
    generate_manifest()
