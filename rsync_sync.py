import subprocess
import threading

def start_rsync(profile, local_dir, log):
    def run():
        cmd = [
            "rsync",
            "-avz",
            "--delete",
            "--progress",
            "--exclude", "*.tmp",
            "--exclude", "*.part",
            "-e", f'ssh -i {profile["ssh_key"]} -p {profile["port"]}',
            f"{local_dir}/",
            f'{profile["user"]}@{profile["host"]}:{profile["remote_dir"]}/'
        ]

        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in p.stdout:
            log(line.strip())

        log("✅ Sync selesai")

    threading.Thread(target=run, daemon=True).start()
