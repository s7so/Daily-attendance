# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

added_files = [
    ('src', 'src'),  # نسخ مجلد src بالكامل
]

a = Analysis(
    ['main.py'],
    pathex=['.'],  # إضافة المسار الحالي
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'src.ui.main_window',
        'src.database.departments_db',
        'src.database.employees_db',
        'src.devices.fingertec',
        'pandas',
        'openpyxl',
        'sqlite3'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MyApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # تغيير إلى True مؤقتاً لرؤية الأخطاء
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
) 