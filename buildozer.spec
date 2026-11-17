[app]
title = Assistant Pro
package.name = assistantpro
package.domain = org.shikharsharan
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,atlas,ttf,otf
source.exclude_dirs = .git,.venv,.buildozer,build,dist,logs,tests,build_assets,__pycache__,.vscode
version = 0.1.0
requirements = python3,kivy==2.3.1,python-dotenv,charset-normalizer==3.4.4,cryptography
p4a.branch = develop
orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/26.png
presplash.filename = %(source.dir)s/26.png

android.api = 35
android.minapi = 24
android.archs = arm64-v8a
android.allow_backup = False
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
