block_cipher = None
a = Analysis(['app.py'], binaries=[], datas=[], hiddenimports=[],
             hookspath=[], runtime_hooks=[], excludes=[])
exe = EXE(a.pure, a.zipped_data, a.scripts,
          name='VPS-Rsync-Sync',
          console=False)
