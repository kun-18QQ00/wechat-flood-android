# -*- coding: utf-8 -*-
"""微信刷屏助手 APK 构建脚本 - Google Colab 版"""

# @title ?? 一键构建微信刷屏助手 APK { display-mode: "form" }

# 步骤 1: 安装依赖
print("?? 安装依赖...")
!pip install buildozer cython==3.0.12

# 步骤 2: 安装系统依赖
print("?? 安装系统依赖...")
!sudo apt-get update
!sudo apt-get install -y build-essential git python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo6 cmake libffi-dev libssl-dev automake zip unzip openjdk-17-jdk

# 步骤 3: 克隆项目
print("?? 克隆项目...")
!git clone https://github.com/kun-18QQ00/wechat-flood-android.git
%cd wechat-flood-android

# 步骤 4: 接受 Android SDK 许可证
print("? 接受 Android SDK 许可证...")
!mkdir -p ~/.android
!echo -e "\n24333f8a63b6825ea9c5514f83c2829b004d1fee" > ~/.android/android-sdk-license
!echo -e "\nd56f5187479451eabf01fb78af6dfcb131a6481e" >> ~/.android/android-sdk-license
!echo -e "\n84831b9409646a918e30573bab4c9c91346d8abd" >> ~/.android/android-sdk-license

# 步骤 5: 构建 APK
print("?? 开始构建 APK (大约需要 30-60 分钟)...")
!yes | buildozer android debug

# 步骤 6: 下载 APK
print("? 构建完成！正在准备下载...")
import os
from google.colab import files

apk_files = [f for f in os.listdir('bin') if f.endswith('.apk')]
if apk_files:
    apk_path = os.path.join('bin', apk_files[0])
    print(f"?? 下载 {apk_path}...")
    files.download(apk_path)
else:
    print("? 未找到 APK 文件")
