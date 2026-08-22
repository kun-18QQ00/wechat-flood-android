[app]

# App 基本信息
title = 微信刷屏助手
package.name = wechatflood
package.domain = com.tools.wechatflood
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 3.0.0

# 依赖 - 指定Python版本
requirements = python3==3.11.9,kivy,pyjnius,android

# 安卓配置
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,VIBRATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

# 全屏模式
fullscreen = 0

# 横竖屏：portrait=竖屏, landscape=横屏
orientation = portrait

# 允许退出
android.allow_backup = True

# 日志级别
log_level = 2

[buildozer]
warn_on_root = 0