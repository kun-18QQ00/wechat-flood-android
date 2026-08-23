[app]
title = MsgHelper
package.name = msgsender
package.domain = org.msg
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0
requirements = python3,kivy
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
orientation = portrait
fullscreen = 0
android.allow_backup = True
log_level = 2

[buildozer]
warn_on_root = 0
