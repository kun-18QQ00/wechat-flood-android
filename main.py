# -*- coding: utf-8 -*-
"""
消息助手 v8.0 - 稳定版
自动识别聊天框 + 完全自动发送
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
from kivy.uix.boxlayout import BoxLayout

ANDROID = platform == 'android'

# ── 字体注册 ──
FONT_NAME = 'Roboto'
try:
    font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'chinese.ttf')
    if os.path.exists(font_path):
        LabelBase.register(name='CN', fn_regular=font_path)
        FONT_NAME = 'CN'
except Exception as e:
    Logger.warning(f'字体加载失败: {e}')

# ── 应用包名映射 ──
APP_PACKAGES = {
    '微信': 'com.tencent.mm',
    'QQ': 'com.tencent.mobileqq',
    '钉钉': 'com.alibaba.android.rimet',
    '飞书': 'com.ss.android.lark',
    'Telegram': 'org.telegram.messenger',
    'WhatsApp': 'com.whatsapp',
}


class RootWidget(BoxLayout):
    """根组件"""
    pass


class MessageApp(App):
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
        try:
            Window.clearcolor = (0.949, 0.949, 0.969, 1)
            root = RootWidget()
            # 延迟检查无障碍服务
            Clock.schedule_once(self._check_service, 1)
            return root
        except Exception as e:
            Logger.error(f'构建UI失败: {e}')
            # 返回一个简单的布局作为后备
            return BoxLayout()

    def on_start(self):
        self._log("应用已启动")
        if ANDROID:
            self._log("请先开启无障碍服务")
        else:
            self._log("当前为非Android环境，使用剪贴板模式")

    # ══════════════════════════════════════
    # 无障碍服务管理
    # ══════════════════════════════════════

    def _check_service(self, *args):
        if not ANDROID:
            self.service_status = '仅支持Android'
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
                self._log("请开启无障碍服务")
        except Exception as e:
            self.service_status = '未开启'
            Logger.warning(f'无障碍检查失败: {e}')

    def open_accessibility_settings(self):
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
        except Exception as e:
            self._log(f"打开设置失败: {e}")

    def _get_service(self):
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
    # UI 操作回调
    # ══════════════════════════════════════

    def load_preset(self, preset_type):
        try:
            presets = {
                'emoji': "😀\n😂\n🤣\n😍\n🥰\n😎",
                'greeting': "你好\n早上好\n中午好\n晚上好",
                'numbers': "1\n2\n3\n4\n5\n6\n7\n8\n9\n10",
            }
            text = presets.get(preset_type, '')
            if text:
                self.root.ids.msg_input.text = text
                self._log(f"已加载预设: {preset_type}")
        except Exception as e:
            self._log(f"加载预设失败: {e}")

    def _update_char_count(self):
        try:
            text = self.root.ids.msg_input.text
            self.root.ids.char_count.text = f'{len(text)} 字符'
        except Exception:
            pass

    def select_app(self, app_name):
        self.selected_app = app_name
        self._log(f"已选择: {app_name}")

    def select_mode(self, mode):
        self.selected_mode = mode
        self._log(f"模式: {mode}")

    def start_sending(self):
        if self.is_running:
            return

        try:
            raw_text = self.root.ids.msg_input.text.strip()
        except Exception:
            raw_text = ''

        if not raw_text:
            self._log("请输入消息内容")
            return

        self.messages = [m.strip() for m in raw_text.split('\n') if m.strip()]
        if not self.messages:
            self._log("消息内容为空")
            return

        # 读取设置
        try:
            speed_text = self.root.ids.speed_input.text
            self.interval = max(0.1, float(speed_text))
        except Exception:
            self.interval = 1.0

        try:
            batch_text = self.root.ids.batch_input.text
            self.batch = int(batch_text) if batch_text else 0
        except Exception:
            self.batch = 0

        # 初始化状态
        self.is_running = True
        self.is_paused = False
        self.sent_count = 0
        self.current_index = 0
        self.start_time = time.time()
        self.status_text = '运行中...'

        self._log(f"开始发送 {len(self.messages)} 条消息")

        # 启动发送线程
        self._send_thread = threading.Thread(target=self._send_loop, daemon=True)
        self._send_thread.start()

    def pause_sending(self):
        if not self.is_running:
            return
        self.is_paused = not self.is_paused
        self.status_text = '已暂停' if self.is_paused else '运行中...'
        self._log("已暂停" if self.is_paused else "已继续")

    def stop_sending(self):
        self.is_running = False
        self.is_paused = False
        self.status_text = '已停止'
        self._log("已停止")

        service = self._get_service()
        if service:
            try:
                service.stopSending()
            except Exception:
                pass

    def _send_loop(self):
        pkg = APP_PACKAGES.get(self.selected_app, 'com.tencent.mm')

        while self.is_running:
            if self.is_paused:
                time.sleep(0.1)
                continue

            if self.batch > 0 and self.sent_count >= self.batch:
                Clock.schedule_once(lambda dt: self._log("已达到批量限制"), 0)
                break

            # 选择消息
            if self.selected_mode == '随机':
                msg = random.choice(self.messages)
            elif self.selected_mode == '单条':
                msg = self.messages[0]
            else:
                msg = self.messages[self.current_index % len(self.messages)]
                self.current_index += 1

            # 发送
            try:
                service = self._get_service()
                if service:
                    success = service.sendMessage(msg, pkg, 1, 300)
                    if success:
                        self.sent_count += 1
                        Clock.schedule_once(lambda dt, m=msg: self._on_sent(m, True), 0)
                    else:
                        self._do_clipboard(msg)
                else:
                    self._do_clipboard(msg)
            except Exception as e:
                Logger.error(f'发送失败: {e}')
                try:
                    self._do_clipboard(msg)
                except Exception:
                    break

            time.sleep(self.interval)

        Clock.schedule_once(lambda dt: self._on_complete(), 0)

    def _do_clipboard(self, msg):
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(msg)
        self.sent_count += 1
        Clock.schedule_once(lambda dt, m=msg: self._on_sent(m, False), 0)

    def _on_sent(self, msg, auto):
        self.count_text = str(self.sent_count)
        self._update_stats()
        prefix = "自动发送" if auto else "已复制"
        short = msg[:10] + '...' if len(msg) > 10 else msg
        self._log(f"#{self.sent_count} {prefix}: {short}")

    def _on_complete(self):
        self.is_running = False
        self.is_paused = False
        self.status_text = '完成'
        self._update_stats()
        elapsed = time.time() - self.start_time if self.start_time else 0
        self._log(f"完成: 共 {self.sent_count} 条, 耗时 {elapsed:.1f} 秒")

    def _update_stats(self):
        if self.start_time:
            elapsed = time.time() - self.start_time
            speed = self.sent_count / elapsed if elapsed > 0 else 0
            self.stats_text = f'速度: {speed:.1f} 条/秒 | 耗时: {elapsed:.0f} 秒'

    def _log(self, msg):
        ts = datetime.now().strftime('%H:%M:%S')
        line = f'[{ts}] {msg}'
        Logger.info(line)
        try:
            self.root.ids.log_area.text += line + '\n'
            self.root.ids.log_area.cursor = (0, len(self.root.ids.log_area.text))
        except Exception:
            pass

    def on_pause(self):
        return True

    def on_resume(self):
        Clock.schedule_once(self._check_service, 1)


if __name__ == '__main__':
    MessageApp().run()
