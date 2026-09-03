# -*- coding: utf-8 -*-
"""
消息助手 v7.0
自动识别聊天框 + 完全自动发送
原生Kv UI + Java无障碍服务 + pyjnius桥接
"""
import os
import threading
import time
import random
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.utils import platform
from kivy.logger import Logger
from kivy.properties import StringProperty, BooleanProperty

ANDROID = platform == 'android'

# ── 字体 ──
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'chinese.ttf')
if os.path.exists(FONT_PATH):
    try:
        LabelBase.register(name='CN', fn_regular=FONT_PATH)
        FONT_NAME = 'CN'
    except Exception:
        FONT_NAME = 'Roboto'
else:
    FONT_NAME = 'Roboto'

# ── 应用包名映射 ──
APP_PACKAGES = {
    '微信': 'com.tencent.mm',
    'QQ': 'com.tencent.mobileqq',
    '钉钉': 'com.alibaba.android.rimet',
    '飞书': 'com.ss.android.lark',
    'Telegram': 'org.telegram.messenger',
    'WhatsApp': 'com.whatsapp',
}


class MessageApp(App):
    """消息助手主应用"""

    font_name = StringProperty('Roboto')
    status_text = StringProperty('就绪')
    count_text = StringProperty('0')
    stats_text = StringProperty('速度: 0 条/秒 | 耗时: 0 秒')
    service_status = StringProperty('检查中...')
    is_running = BooleanProperty(False)
    is_paused = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = FONT_NAME
        self.messages = []
        self.sent_count = 0
        self.current_index = 0
        self.start_time = None
        self.selected_app = '微信'
        self.selected_mode = '顺序'
        self.interval = 1.0
        self.batch = 0
        self._send_thread = None
        self._accessibility_service = None

    def build(self):
        Window.clearcolor = (0.949, 0.949, 0.969, 1)
        # Kv文件自动加载 (同目录下 message.kv)
        # 延迟检查无障碍服务状态
        Clock.schedule_once(self._check_service, 2)
        # 返回None让Kv文件接管UI
        return None

    def on_start(self):
        """应用启动后调用"""
        self._log("应用已启动")
        self._log("请先开启无障碍服务")

    # ══════════════════════════════════════
    # 无障碍服务管理
    # ══════════════════════════════════════

    def _check_service(self, *args):
        """检查无障碍服务是否已启用"""
        if not ANDROID:
            self.service_status = '仅支持Android设备'
            return

        try:
            from jnius import autoclass
            AutoSendService = autoclass('com.msg.sender.MessageAccessibilityService')
            service = AutoSendService.getInstance()
            if service is not None:
                self.service_status = '已连接'
                self._accessibility_service = service
                self._log("无障碍服务已连接")
            else:
                self.service_status = '未开启'
                self._log("请在系统设置中开启无障碍服务")
        except Exception as e:
            self.service_status = '未开启'
            Logger.warning(f"无障碍服务检查失败: {e}")

    def open_accessibility_settings(self):
        """打开无障碍设置页面"""
        if not ANDROID:
            self._log("仅支持Android设备")
            return
        try:
            from jnius import autoclass
            Intent = autoclass('android.content.Intent')
            Settings = autoclass('android.provider.Settings')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
            PythonActivity.mActivity.startActivity(intent)
            self._log("已打开无障碍设置")
            self._log("请找到「消息助手」并开启")
        except Exception as e:
            self._log(f"打开设置失败: {e}")

    def _get_service(self):
        """获取无障碍服务实例"""
        if not ANDROID:
            return None
        if self._accessibility_service is not None:
            return self._accessibility_service
        try:
            from jnius import autoclass
            AutoSendService = autoclass('com.msg.sender.MessageAccessibilityService')
            service = AutoSendService.getInstance()
            if service is not None:
                self._accessibility_service = service
            return service
        except Exception:
            return None

    # ══════════════════════════════════════
    # UI 操作回调 (由 message.kv 调用)
    # ══════════════════════════════════════

    def load_preset(self, preset_type):
        """加载预设消息"""
        presets = {
            'emoji': "😀\n😂\n🤣\n😍\n🥰\n😎\n🤩\n😘\n😋\n🤔",
            'number': "1\n2\n3\n4\n5\n6\n7\n8\n9\n10",
            'greet': "你好\n早上好\n中午好\n晚上好\n在吗\n忙吗",
        }
        text = presets.get(preset_type, '')
        try:
            self.root.ids.msg_input.text = text
            self._update_char_count()
            self._log(f"已加载{preset_type}预设")
        except Exception:
            pass

    def select_app(self, app_name):
        """选择目标应用"""
        self.selected_app = app_name
        self._log(f"目标应用: {app_name}")

    def select_mode(self, mode):
        """选择发送模式"""
        self.selected_mode = mode
        self._log(f"发送模式: {mode}")

    def update_speed(self, value):
        """更新发送间隔"""
        self.interval = float(value)

    def _update_char_count(self):
        """更新字符计数"""
        try:
            text = self.root.ids.msg_input.text
            count = len(text.strip())
            self.root.ids.char_count.text = f'{count} 字符'
        except Exception:
            pass

    # ══════════════════════════════════════
    # 发送控制
    # ══════════════════════════════════════

    def start_sending(self):
        """开始发送"""
        if self.is_running:
            return

        # 获取消息
        try:
            raw_text = self.root.ids.msg_input.text.strip()
        except Exception:
            raw_text = ''

        if not raw_text:
            self.status_text = '请输入消息'
            self._log("错误: 请先输入消息内容")
            return

        self.messages = [m.strip() for m in raw_text.split('\n') if m.strip()]
        if not self.messages:
            self.status_text = '消息为空'
            self._log("错误: 消息内容为空")
            return

        # 读取批量设置
        try:
            batch_text = self.root.ids.batch_input.text.strip()
            self.batch = int(batch_text) if batch_text else 0
        except (ValueError, AttributeError):
            self.batch = 0

        # 读取间隔设置
        try:
            self.interval = float(self.root.ids.speed_slider.value)
        except (ValueError, AttributeError):
            self.interval = 1.0

        # 检查无障碍服务
        service = self._get_service()
        if service is None:
            self._log("⚠ 无障碍服务未开启")
            self._log("尝试使用剪贴板模式")
        else:
            self._log("✓ 无障碍服务已连接")

        # 初始化状态
        self.is_running = True
        self.is_paused = False
        self.sent_count = 0
        self.current_index = 0
        self.start_time = time.time()
        self.status_text = '运行中...'

        self._log(f"开始发送 {len(self.messages)} 条消息")
        self._log(f"目标: {self.selected_app} | 模式: {self.selected_mode} | 间隔: {self.interval}秒")

        # 启动发送线程
        self._send_thread = threading.Thread(target=self._send_loop, daemon=True)
        self._send_thread.start()

    def pause_sending(self):
        """暂停/继续"""
        if not self.is_running:
            return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.status_text = '已暂停'
            self._log("已暂停")
        else:
            self.status_text = '运行中...'
            self._log("已继续")

    def stop_sending(self):
        """停止发送"""
        self.is_running = False
        self.is_paused = False
        self.status_text = '已停止'
        self._log("已停止发送")

        # 通知无障碍服务停止
        service = self._get_service()
        if service is not None:
            try:
                service.stopSending()
            except Exception:
                pass

    def _send_loop(self):
        """发送循环（在后台线程运行）"""
        pkg = APP_PACKAGES.get(self.selected_app, 'com.tencent.mm')

        while self.is_running:
            if self.is_paused:
                time.sleep(0.1)
                continue

            # 检查批量限制
            if self.batch > 0 and self.sent_count >= self.batch:
                Clock.schedule_once(lambda dt: self._log("已达到批量限制"), 0)
                break

            # 每次循环重新获取服务实例（用户可能中途开启了无障碍）
            service = self._get_service()

            # 选择消息
            if self.selected_mode == '随机':
                msg = random.choice(self.messages)
            elif self.selected_mode == '单条':
                msg = self.messages[0]
            else:  # 顺序
                msg = self.messages[self.current_index % len(self.messages)]
                self.current_index += 1

            # 发送消息
            try:
                if service is not None:
                    # 使用无障碍服务自动发送
                    success = service.sendMessage(msg, pkg, 1, 300)
                    if success:
                        self.sent_count += 1
                        Clock.schedule_once(lambda dt, m=msg: self._on_sent(m), 0)
                    else:
                        # 回退到剪贴板
                        self._copy_to_clipboard(msg)
                        self.sent_count += 1
                        Clock.schedule_once(lambda dt, m=msg: self._on_sent_clipboard(m), 0)
                else:
                    # 无障碍不可用，用剪贴板
                    self._copy_to_clipboard(msg)
                    self.sent_count += 1
                    Clock.schedule_once(lambda dt, m=msg: self._on_sent_clipboard(m), 0)

            except Exception as e:
                Logger.error(f"发送失败: {e}")
                Clock.schedule_once(lambda dt, err=str(e): self._log(f"错误: {err}"), 0)
                # 尝试剪贴板回退
                try:
                    self._copy_to_clipboard(msg)
                    self.sent_count += 1
                    Clock.schedule_once(lambda dt, m=msg: self._on_sent_clipboard(m), 0)
                except Exception:
                    break

            # 等待间隔
            time.sleep(self.interval)

        # 完成
        Clock.schedule_once(lambda dt: self._on_complete(), 0)

    def _copy_to_clipboard(self, msg):
        """复制到剪贴板"""
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(msg)

    def _on_sent(self, msg):
        """通过无障碍服务发送后的回调"""
        self.count_text = str(self.sent_count)
        self._update_stats()
        short = msg[:15] + '...' if len(msg) > 15 else msg
        self._log(f"#{self.sent_count} 自动发送: {short}")
        self._vibrate()

    def _on_sent_clipboard(self, msg):
        """通过剪贴板发送后的回调"""
        self.count_text = str(self.sent_count)
        self._update_stats()
        short = msg[:15] + '...' if len(msg) > 15 else msg
        self._log(f"#{self.sent_count} 已复制: {short} (请手动粘贴)")
        self._vibrate()

    def _on_complete(self):
        """发送完成"""
        self.is_running = False
        self.is_paused = False
        self.status_text = '完成'
        self._update_stats()
        elapsed = time.time() - self.start_time if self.start_time else 0
        self._log(f"发送完成: 共 {self.sent_count} 条, 耗时 {elapsed:.1f} 秒")

    def _update_stats(self):
        """更新统计信息"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            speed = self.sent_count / elapsed if elapsed > 0 else 0
            self.stats_text = f'速度: {speed:.1f} 条/秒 | 耗时: {elapsed:.0f} 秒'

    def _vibrate(self):
        """振动反馈"""
        if not ANDROID:
            return
        try:
            from jnius import autoclass
            activity = autoclass('org.kivy.android.PythonActivity').mActivity
            vibrator = activity.getSystemService(activity.VIBRATOR_SERVICE)
            vibrator.vibrate(50)
        except Exception:
            pass

    def _log(self, msg):
        """写入日志"""
        ts = datetime.now().strftime('%H:%M:%S')
        line = f'[{ts}] {msg}'
        Logger.info(line)
        try:
            log_area = self.root.ids.log_area
            log_area.text += line + '\n'
            # 自动滚动到底部
            log_area.cursor = (0, len(log_area.text))
        except Exception:
            pass

    def on_pause(self):
        return True

    def on_resume(self):
        # 恢复时重新检查无障碍服务
        Clock.schedule_once(self._check_service, 1)


if __name__ == '__main__':
    MessageApp().run()
