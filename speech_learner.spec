# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('backend', 'backend'), ('.env.example', '.')]
binaries = []
hiddenimports = ['flask', 'flask_cors', 'dashscope', 'python-dotenv', 'requests', 'werkzeug', 'jinja2', 'markupsafe', 'itsdangerous', 'click', 'backend.app', 'backend.config', 'backend.services.tts_service', 'backend.services.llm_service']
tmp_ret = collect_all('dashscope')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('flask')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('flask_cors')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# 排除不需要的 Qt 绑定和其他大型库
excludes = [
    'PyQt5', 'PyQt6', 'PySide2', 'PySide6',  # Qt 绑定
    'matplotlib', 'plotly', 'seaborn',        # 绘图库
    'pandas', 'numpy',                        # 数据分析（dashscope 可能依赖）
    'torch', 'tensorflow', 'jax',             # 深度学习框架
    'scipy', 'sklearn',                       # 科学计算
    'sqlalchemy',                             # ORM
    'tables', 'h5py',                         # 数据存储
    'lxml', 'bs4',                            # XML/HTML 解析
    'PIL', 'Pillow',                          # 图像处理
    'openpyxl', 'xlrd',                       # Excel 处理
    'zmq', 'tornado',                         # 网络库
    'nacl',                                   # 加密库（保留 nacl，移除 cryptography）
    'botocore', 'boto3',                      # AWS
    'fsspec', 's3fs',                         # 文件系统
    'pyarrow',                                # 列式存储
    'Cython',                                 # 编译器
    'IPython', 'ipykernel',                   # Jupyter
    'jupyter', 'notebook',
    'qtpy', 'QtPy',                           # Qt 抽象层
    'pydantic',                               # 数据验证（dashscope 可能依赖）
]

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='speech_learner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='NONE',
)
