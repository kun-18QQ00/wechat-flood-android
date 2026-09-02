# 消息助手 v6.0 - 多语言混合架构

## 项目概述

消息助手是一款iOS风格的Android自动发送工具，采用多种编程语言混合开发，实现最佳用户体验。

## 技术架构

### 编程语言

| 语言 | 用途 | 文件 |
|------|------|------|
| **Python** | 主程序逻辑、业务处理 | `main.py` |
| **Kv** | UI布局、动画定义 | `message.kv` |
| **Java** | Android原生功能、无障碍服务 | `src/com/msg/sender/*.java` |
| **HTML5** | WebView界面结构 | `assets/web/index.html` |
| **CSS3** | 样式、动画、响应式设计 | `assets/web/style.css` |
| **JavaScript** | 交互逻辑、实时更新 | `assets/web/app.js` |
| **XML** | Android配置、资源 | `res/xml/*.xml` |

### 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Android 应用                          │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Python     │  │   WebView    │  │    Java      │  │
│  │   (主逻辑)   │  │  (HTML/CSS)  │  │  (无障碍)    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                  │          │
│         └────────┬────────┴──────────────────┘          │
│                  │                                       │
│           ┌──────▼──────┐                               │
│           │   Kv语言    │                               │
│           │  (UI布局)   │                               │
│           └─────────────┘                               │
└─────────────────────────────────────────────────────────┘
```

## 功能特性

### 核心功能

- 🚀 **自动发送** - 通过无障碍服务实现真正的自动发送
- 📱 **多应用支持** - 微信、QQ、钉钉、飞书、Telegram、WhatsApp
- 🎨 **iOS风格** - 现代化的iOS设计语言
- ✨ **丝滑动画** - CSS3 + Kv语言驱动的流畅动画
- 📊 **实时统计** - 发送速度、耗时、进度显示

### 技术亮点

1. **WebView混合开发** - HTML/CSS/JS提供现代化UI
2. **无障碍服务** - Java实现Android原生自动发送
3. **Kv语言** - 声明式UI，丝滑动画
4. **Python桥接** - 统一的业务逻辑处理
5. **响应式设计** - 适配各种屏幕尺寸

## 文件结构

```
wechat_flood_android/
├── main.py                      # Python主程序
├── message.kv                   # Kv语言UI定义
├── buildozer.spec               # Buildozer配置
├── AndroidManifest.xml          # Android清单
├── src/
│   └── com/msg/sender/
│       └── MessageAccessibilityService.java  # Java无障碍服务
├── assets/
│   ├── web/
│   │   ├── index.html           # WebView HTML
│   │   ├── style.css            # CSS样式
│   │   └── app.js               # JavaScript逻辑
│   ├── icon.svg                 # 应用图标
│   └── presplash.png            # 启动画面
├── res/
│   ├── xml/
│   │   ├── accessibility_service_config.xml
│   │   ├── network_security_config.xml
│   │   └── file_paths.xml
│   └── values/
│       └── strings.xml
└── fonts/
    └── chinese.ttf              # 中文字体
```

## 开发指南

### 环境要求

- Python 3.9+
- Buildozer
- Android SDK 33
- Java JDK 17

### 构建命令

```bash
# 调试版本
buildozer android debug

# 发布版本
buildozer android release
```

### 开发调试

```bash
# 本地运行（测试UI）
python main.py

# Android调试
buildozer android debug deploy run logcat
```

## 更新日志

### v6.0.0 (2026-09-02)

- ✨ 新增WebView混合架构
- ✨ 新增Java无障碍服务
- ✨ 新增CSS3动画效果
- ✨ 新增响应式设计
- 🎨 全新iOS风格界面
- 🔧 优化性能和稳定性

## 许可证

MIT License

## 作者

消息助手团队
