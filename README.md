# 微信刷屏助手 Android 版 v2.0

## 功能特性

- 📝 自定义消息内容，支持多行
- ⚡ 可调节发送速度（0.1秒 ~ 5秒）
- 🔄 三种模式：顺序循环 / 随机发送 / 单条重复
- ⏱ 定时停止 + 批量停止
- 💾 消息预设保存/加载
- 📥 从文件导入消息
- 📋 实时发送日志
- 🔁 防重复模式

## 打包 APK 方法

### 方法一：GitHub Actions 自动构建（推荐，最简单）

1. 在 GitHub 上创建一个新仓库（如 `wechat-flood-android`）
2. 把整个 `wechat_flood_android` 文件夹的内容上传到仓库
3. 推送到 `main` 分支后，GitHub Actions 会自动开始构建
4. 构建完成后，进入仓库 → Actions → 点击最新的构建 → 下载 `wechat-flood-apk` 文件
5. 解压得到 `.apk` 文件，传到手机安装即可

```bash
# 如果你有 git，可以直接：
cd wechat_flood_android
git init
git add .
git commit -m "init"
git remote add origin https://github.com/你的用户名/wechat-flood-android.git
git push -u origin main
```

### 方法二：本地构建（需要 Linux 环境）

```bash
# 1. 安装依赖（Ubuntu/Debian）
sudo apt-get update
sudo apt-get install -y build-essential git python3-pip autoconf libtool pkg-config \
  zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# 2. 安装 buildozer
pip install buildozer cython

# 3. 进入项目目录
cd wechat_flood_android

# 4. 构建 debug 版 APK
buildozer android debug

# 5. APK 文件在 bin/ 目录下
```

### 方法三：WSL (Windows 子系统)

```bash
# 1. 安装 WSL（管理员 PowerShell）
wsl --install -d Ubuntu

# 2. 重启电脑后，进入 Ubuntu 终端，按方法二操作
```

## 使用说明

1. 安装 APK 到安卓手机
2. 打开应用，输入刷屏消息内容
3. 调整发送速度、模式等参数
4. 点击「开始刷屏」
5. 应用会自动复制消息到剪贴板
6. 切换到微信聊天窗口，长按输入框 → 粘贴 → 发送

> ⚠️ **注意**：安卓系统限制，无法自动在微信中粘贴发送。
> 应用会自动将消息复制到剪贴板并弹出提示，你需要手动粘贴到微信。
> 使用「随机发送」模式 + 快速间隔效果最佳。

## 文件结构

```
wechat_flood_android/
├── main.py                    # 主程序
├── buildozer.spec             # 打包配置
├── README.md                  # 说明文档
└── .github/
    └── workflows/
        └── build-apk.yml      # GitHub Actions 自动构建
```
