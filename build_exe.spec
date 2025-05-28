# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['Qt/main.py'],
    pathex=['d:\\pythonproject\\ui2.5'],
    binaries=[],
    datas=[
        ('config/*', 'config'),
        ('*.json', '.'),
        ('utils/*', 'utils'),
        ('cli/*', 'cli'),
        ('pipeline_runner.py', '.'),  # 确保包含pipeline_runner
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui', 
        'PySide6.QtWidgets',
        'cv2',
        'numpy',
        'pathlib',
        'json',
        'subprocess',
        'shutil',
        'pipeline_runner',
        'ultralytics',  # 添加YOLO依赖
        'torch',        # 添加PyTorch依赖
        'osgeo',        # 添加GDAL依赖
        # 添加所有utils模块
        'utils.HSV_Batch2txt',
        'utils.cutting',
        'utils.merge_shp',
        'utils.predect',
        'utils.shp_kuang_cut',
        'utils.tiqu',
        'utils.txt_to_shp',
        'utils.vit_model',
        'utils.qt_tqdm',
        # 添加所有cli模块
        'cli.cutting_cli',
        'cli.hsv_batch_cli',
        'cli.merge_shp_cli',
        'cli.shp_kuang_cut_cli',
        'cli.txt_to_shp_cli',
        'cli.yolo_predict_cli',
        'cli.vit_predict_cli',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],  # 移除a.binaries和a.datas，使用--onedir模式
    exclude_binaries=True,  # 添加此行，启用--onedir模式
    name='病树检测系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为False以隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# 添加COLLECT，用于--onedir模式
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='病树检测系统',
)