[app]
title = 消息助手
package.name = msgsender
package.domain = org.msg
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf,otf,xml,html,css,js
source.include_patterns = fonts/*,res/xml/*,assets/**
version = 9.1.0
requirements = python3,kivy,pyjnius,android
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,BIND_ACCESSIBILITY_SERVICE,VIBRATE,FOREGROUND_SERVICE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
orientation = portrait
fullscreen = 0
android.allow_backup = True
android.manifest.custom_enabled = true

# 编译Java源码（无障碍服务）
android.add_src = src

# 图标
icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/presplash.png

# 日志级别
log_level = 2

[buildozer]
warn_on_root = 0



