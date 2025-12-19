import sys, os, subprocess, json, base64, threading
from pathlib import Path
os.environ["QT_MAC_WANTS_LAYER"] = "1"
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QComboBox
from PySide6.QtGui import QTextCursor
from PySide6.QtCore import QObject, Signal



# -----------------------------
# Log Handler Signal (thread-safe)
# -----------------------------
class LogHandler(QObject):
    new_log = Signal(str)  # untuk mengirim string log dari thread ke GUI

# -----------------------------
# GUI App
# -----------------------------
class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KangAi - Sync")
        self.resize(700, 500)

        self.layout = QVBoxLayout(self)

        # Config
        self.config_file = None
        self.profiles = []
        self.profile = None

        # Log Signal
        self.log_handler = LogHandler()
        self.log_handler.new_log.connect(self.append_log)

        # GUI Components
        self.profile_box = QComboBox()
        self.profile_box.currentIndexChanged.connect(self.profile_changed)

        self.load_json_btn = QPushButton("Load JSON Config")
        self.load_json_btn.clicked.connect(self.load_json_file)

        self.local_dir = QLineEdit()
        browse_btn = QPushButton("Browse Local Folder")
        browse_btn.clicked.connect(self.pick_folder)

        test_btn = QPushButton("Test SSH")
        test_btn.clicked.connect(self.test_ssh)
        sync_btn = QPushButton("Start Sync")
        sync_btn.clicked.connect(self.sync)

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        # Layout
        self.layout.addWidget(self.load_json_btn)
        self.layout.addWidget(QLabel("Select VPS Profile"))
        self.layout.addWidget(self.profile_box)
        self.layout.addWidget(QLabel("Local Folder"))
        self.layout.addWidget(self.local_dir)
        self.layout.addWidget(browse_btn)
        self.layout.addWidget(test_btn)
        self.layout.addWidget(sync_btn)
        self.layout.addWidget(QLabel("Log"))
        self.layout.addWidget(self.log)

    # -----------------------------
    # Thread-safe append log
    # -----------------------------
    def append_log(self, text):
        self.log.append(text)
        self.log.moveCursor(QTextCursor.End)
        self.log.ensureCursorVisible()

    # -----------------------------
    # Load JSON
    # -----------------------------
    def load_json_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select JSON Config", "", "JSON Files (*.json)")
        if not file_path:
            return
        self.config_file = Path(file_path)
        try:
            data = json.loads(self.config_file.read_text())
            profiles = data.get("profiles", [])
            if not isinstance(profiles, list) or len(profiles) == 0:
                self.log_handler.new_log.emit("❌ JSON invalid: 'profiles' must be a non-empty list")
                return
            self.profiles = profiles
            self.profile_box.clear()
            for p in self.profiles:
                self.profile_box.addItem(p.get("name", "Unnamed"))
            self.profile = self.profiles[0]
            self.profile_box.setCurrentIndex(0)
            self.log_handler.new_log.emit(f"✅ Loaded {len(self.profiles)} profiles from {self.config_file}")
            if "local_dir" in self.profile:
                self.local_dir.setText(self.profile["local_dir"])
        except Exception as e:
            self.log_handler.new_log.emit(f"❌ Failed to load JSON: {e}")

    # -----------------------------
    # Profile change
    # -----------------------------
    def profile_changed(self, index):
        if index < 0 or index >= len(self.profiles):
            return
        self.profile = self.profiles[index]
        self.log_handler.new_log.emit(f"🔄 Selected profile: {self.profile.get('name','Unnamed')}")
        if "local_dir" in self.profile:
            self.local_dir.setText(self.profile["local_dir"])

    # -----------------------------
    # Pick local folder
    # -----------------------------
    def pick_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Select Local Folder")
        if d:
            self.local_dir.setText(d)
            self.log_handler.new_log.emit(f"📁 Local folder selected: {d}")
            if self.profile:
                self.profile["local_dir"] = d

    # -----------------------------
    # Get SSH key (Base64 or file), bersihkan karakter asing
    # -----------------------------
    def get_ssh_key(self, profile):
        tmp_path = Path("/tmp/temp_ssh_key")

        if "ssh_key_content" in profile and profile["ssh_key_content"]:
            try:
                tmp_path = Path("/tmp/temp_ssh_key")
                tmp_path.write_bytes(base64.b64decode(profile["ssh_key_content"]))
                tmp_path.chmod(0o600)
                return str(tmp_path)
            except Exception as e:
                self.log_handler.new_log.emit(f"❌ Failed to write SSH key: {e}")
                return ""

        elif "ssh_key_path" in profile:
            key_bytes = Path(profile["ssh_key_path"]).read_bytes()
            key_bytes = key_bytes.rstrip(b"\x00\r\n% ")
            tmp_path.write_bytes(key_bytes)
            tmp_path.chmod(0o600)
            return str(tmp_path)
        else:
            self.log_handler.new_log.emit("❌ No SSH key found in profile")
            return ""

    # -----------------------------
    # Test SSH
    # -----------------------------
    def test_ssh(self):
        if not self.profile:
            self.log_handler.new_log.emit("❌ No profile selected")
            return

        def run():
            self.log_handler.new_log.emit(f"🔄 Testing SSH to {self.profile.get('name','Unnamed')} ...")
            key_path = self.get_ssh_key(self.profile)
            cmd = [
                "ssh",
                "-i", key_path,
                "-p", str(self.profile.get("port",22)),
                f"{self.profile['user']}@{self.profile['host']}",
                "echo OK"
            ]
            try:
                subprocess.check_output(cmd, stderr=subprocess.STDOUT)
                self.log_handler.new_log.emit("✅ SSH OK")
            except subprocess.CalledProcessError:
                self.log_handler.new_log.emit("❌ SSH FAILED")
            except Exception as e:
                self.log_handler.new_log.emit(f"❌ SSH error: {e}")

        threading.Thread(target=run, daemon=True).start()

    # -----------------------------
    # Start Rsync (read-only remote)
    # -----------------------------
    def sync(self):
        if not self.profile:
            self.log_handler.new_log.emit("❌ No profile selected")
            return
        local_dir = self.local_dir.text()
        if not local_dir:
            self.log_handler.new_log.emit("❌ Please select local folder first")
            return
        key_path = self.get_ssh_key(self.profile)

        cmd = [
            "rsync",
            "-avz",
            "--progress",
            "--ignore-existing",
            "-e", f"ssh -i {key_path} -p {self.profile.get('port',22)}",
            f"{local_dir}/",
            f"{self.profile['user']}@{self.profile['host']}:{self.profile['remote_dir']}/"
        ]

        def run():
            self.log_handler.new_log.emit(f"🚀 Starting rsync to {self.profile.get('name','Unnamed')}")
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in p.stdout:
                self.log_handler.new_log.emit(line.strip())
            self.log_handler.new_log.emit("✅ Sync selesai")

        threading.Thread(target=run, daemon=True).start()

# -----------------------------
# Run App
# -----------------------------
def run_app():
    app = QApplication(sys.argv)
    w = App()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_app()
