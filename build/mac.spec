app = BUNDLE(
    EXE(
        Analysis(['app.py']),
        name='VPS-Rsync-Sync',
        console=False
    ),
    bundle_identifier='com.vps.rsync.sync'
)
