[app]
title = 微信刷屏助手
package.name = wechatflood
package.domain = com.tools.wechatflood
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 3.0.0
requirements = python3,kivy,pyjnius,android
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,VIBRATE
android.api = 33
android.minapi = 21
android.ndk = 25c
android.archs = arm64-v8a
android.accept_sdk_license = True
fullscreen = 0
orientation = portrait
android.allow_backup = True
log_level = 2
[buildozer]
warn_on_root = 0
