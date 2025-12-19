import json
from pathlib import Path

CONFIG_FILE = Path("config.json")

def load_profiles():
    if not CONFIG_FILE.exists():
        return []
    return json.loads(CONFIG_FILE.read_text())

def save_profiles(profiles):
    CONFIG_FILE.write_text(json.dumps(profiles, indent=2))

def add_profile(profile):
    profiles = load_profiles()
    profiles.append(profile)
    save_profiles(profiles)

def delete_profile(name):
    profiles = load_profiles()
    profiles = [p for p in profiles if p["name"] != name]
    save_profiles(profiles)
