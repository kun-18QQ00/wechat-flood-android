[app]

# App 基本信息
title = 微信刷屏助手
package.name = wechatflood
package.domain = com.tools.wechatflood
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 3.0.0

# 依赖
requirements = python3,kivy,pyjnius,android

# 安卓配置
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,VIBRATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

# 图标和启动画面（可选，放同目录下）
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png

# 全屏模式
fullscreen = 0

# 横竖屏：portrait=竖屏, landscape=横屏
orientation = portrait

# 允许退出
android.allow_backup = True

# 日志级别
log_level = 2

# 构建模式：debug = 测试版，release = 发布版（需签名）
# buildozer android debug   = 测试版
# buildozer android release = 发布版（需签名）

[buildozer]
warn_on_root = 0