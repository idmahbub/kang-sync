import sys
from PySide6.QtWidgets import *
from profiles import load_profiles, add_profile, delete_profile
from ssh_keys import list_keys, generate_key, test_ssh
from rsync_sync import start_rsync

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VPS Rsync Sync Manager")
        self.resize(600, 700)

        layout = QVBoxLayout(self)

        self.profile_box = QComboBox()
        self.refresh_profiles()

        self.local_dir = QLineEdit()
        self.log = QTextEdit()
        self.log.setReadOnly(True)

        layout.addWidget(QLabel("Profile VPS"))
        layout.addWidget(self.profile_box)
        layout.addWidget(self.btn("Add Profile", self.add_profile))
        layout.addWidget(self.btn("Delete Profile", self.del_profile))

        layout.addWidget(QLabel("Local Folder"))
        layout.addWidget(self.local_dir)
        layout.addWidget(self.btn("Browse", self.pick_folder))

        layout.addWidget(self.btn("Generate SSH Key", self.gen_key))
        layout.addWidget(self.btn("Test SSH", self.test_ssh))
        layout.addWidget(self.btn("Start Sync", self.sync))

        layout.addWidget(QLabel("Log"))
        layout.addWidget(self.log)

    def btn(self, text, fn):
        b = QPushButton(text)
        b.clicked.connect(fn)
        return b

    def refresh_profiles(self):
        self.profile_box.clear()
        self.profiles = load_profiles()
        for p in self.profiles:
            self.profile_box.addItem(p["name"])

    def add_profile(self):
        name, ok = QInputDialog.getText(self, "Profile Name", "Name:")
        if not ok:
            return

        keys = list_keys()
        if not keys:
            QMessageBox.warning(self, "No SSH Key", "Generate SSH key first")
            return

        profile = {
            "name": name,
            "host": QInputDialog.getText(self, "Host", "IP / Domain:")[0],
            "user": QInputDialog.getText(self, "User", "SSH User:")[0],
            "port": 22,
            "remote_dir": QInputDialog.getText(self, "Remote Dir", "/opt/vps-agent/videos")[0],
            "ssh_key": keys[0]
        }

        add_profile(profile)
        self.refresh_profiles()

    def del_profile(self):
        delete_profile(self.profile_box.currentText())
        self.refresh_profiles()

    def pick_folder(self):
        d = QFileDialog.getExistingDirectory(self)
        if d:
            self.local_dir.setText(d)

    def get_profile(self):
        return self.profiles[self.profile_box.currentIndex()]

    def gen_key(self):
        k = generate_key()
        self.log.append(f"🔑 SSH key generated: {k}")

    def test_ssh(self):
        ok = test_ssh(self.get_profile())
        self.log.append("✅ SSH OK" if ok else "❌ SSH FAILED")

    def sync(self):
        start_rsync(self.get_profile(), self.local_dir.text(), self.log.append)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = App()
    w.show()
    sys.exit(app.exec())
