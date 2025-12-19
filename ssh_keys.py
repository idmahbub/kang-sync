from pathlib import Path
import subprocess

SSH_DIR = Path.home() / ".ssh"

def list_keys():
    SSH_DIR.mkdir(exist_ok=True)
    return [str(p) for p in SSH_DIR.iterdir() if p.is_file() and not p.suffix]

def generate_key(name="id_vps_rsync"):
    path = SSH_DIR / name
    subprocess.run([
        "ssh-keygen",
        "-t", "rsa",
        "-b", "4096",
        "-f", str(path),
        "-N", ""
    ])
    return str(path)

def test_ssh(profile):
    cmd = [
        "ssh",
        "-i", profile["ssh_key"],
        "-p", str(profile["port"]),
        f'{profile["user"]}@{profile["host"]}',
        "echo OK"
    ]
    return subprocess.call(cmd) == 0
