# -*- coding: utf-8 -*-
"""
消息助手 v9.3 - 修复无障碍 + 优化UI
"""
import os
import threading
import time
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.utils import platform
from kivy.logger import Logger
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

ANDROID = platform == 'android'

Builder.load_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'message.kv'))

FONT_NAME = 'Roboto'
try:
    fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'chinese.ttf')
    if os.path.exists(fp):
        LabelBase.register(name='CN', fn_regular=fp)
        FONT_NAME = 'CN'
except Exception:
    pass


class RootWidget(BoxLayout):
    pass


class MsgApp(App):
    font_name = StringProperty('Roboto')
    status_text = StringProperty('等待中')
    count_text = StringProperty('0')
    speed_text = StringProperty('1.0秒/条')
    service_ok = BooleanProperty(False)
    is_running = BooleanProperty(False)
    is_paused = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = FONT_NAME
        self.messages = []
        self.sent_count = 0
        self.current_index = 0
        self.start_time = None
        self.interval = 1.0
        self.batch = 0
        self._thread = None
        self._service = None

    def build(self):
        Window.clearcolor = (0.93, 0.94, 0.98, 1)
        Clock.schedule_once(self._init, 1)
        return RootWidget()

    def _init(self, *args):
        self._log('应用已启动')
        self._check_service()

    # ── 无障碍服务 ──

    def _check_service(self):
        if not ANDROID:
            self._log('非Android设备，使用剪贴板模式')
            return
        try:
            from jnius import autoclass
            svc = autoclass('com.msg.sender.MessageAccessibilityService')
            inst = svc.getInstance()
            if inst:
                self._service = inst
                self.service_ok = True
                self._log('无障碍服务已连接')
            else:
                self.service_ok = False
                self._log('请点击按钮开启无障碍')
        except Exception as e:
            self.service_ok = False
            self._log(f'检查失败: {e}')

    def open_settings(self):
        if not ANDROID:
            self._log('仅支持Android')
            return
        try:
            from jnius import autoclass
            ctx = autoclass('org.kivy.android.PythonActivity').mActivity
            Intent = autoclass('android.content.Intent')
            Settings = autoclass('android.provider.Settings')
            
            # 直接打开无障碍设置
            try:
                intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                ctx.startActivity(intent)
                self._log('已打开无障碍设置')
            except Exception:
                # 备用：打开系统设置
                try:
                    ctx.startActivity(Intent(Settings.ACTION_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                    self._log('已打开系统设置')
                except Exception:
                    self._log('打开设置失败')
            
            self._log('找到[消息助手]并开启')
            self._log('如果找不到，请重启APP后重试')
        except Exception as e:
            self._log(f'失败: {e}')

    def _get_svc(self):
        if not ANDROID:
            return None
        if self._service:
            return self._service
        try:
            from jnius import autoclass
            svc = autoclass('com.msg.sender.MessageAccessibilityService')
            inst = svc.getInstance()
            if inst:
                self._service = inst
                self.service_ok = True
            return inst
        except Exception:
            return None

    # ── 发送控制 ──

    def start(self):
        if self.is_running:
            return
        try:
            raw = self.root.ids.msg_input.text.strip()
        except Exception:
            raw = ''
        if not raw:
            self._log('请输入消息')
            return
        self.messages = [m.strip() for m in raw.split('\n') if m.strip()]
        if not self.messages:
            self._log('消息为空')
            return
        try:
            self.interval = max(0.1, float(self.root.ids.speed_input.text))
        except Exception:
            self.interval = 1.0
        try:
            self.batch = int(self.root.ids.batch_input.text or '0')
        except Exception:
            self.batch = 0

        self.is_running = True
        self.is_paused = False
        self.sent_count = 0
        self.current_index = 0
        self.start_time = time.time()
        self.status_text = '发送中'
        self._log(f'开始 {len(self.messages)} 条 间隔{self.interval}秒')
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def pause(self):
        if not self.is_running:
            return
        self.is_paused = not self.is_paused
        self.status_text = '已暂停' if self.is_paused else '发送中'

    def stop(self):
        self.is_running = False
        self.is_paused = False
        self.status_text = '已停止'
        self._log('已停止')
        svc = self._get_svc()
        if svc:
            try:
                svc.stopSending()
            except Exception:
                pass

    def _loop(self):
        while self.is_running:
            if self.is_paused:
                time.sleep(0.1)
                continue
            if self.batch > 0 and self.sent_count >= self.batch:
                Clock.schedule_once(lambda dt: self._log('达到批量限制'), 0)
                break
            msg = self.messages[self.current_index % len(self.messages)]
            self.current_index += 1
            try:
                svc = self._get_svc()
                if svc:
                    ok = svc.sendMessage(msg, None, 1, 300)
                    if ok:
                        self.sent_count += 1
                        Clock.schedule_once(lambda dt, m=msg: self._on_sent(m, True), 0)
                    else:
                        self._copy(msg)
                else:
                    self._copy(msg)
            except Exception:
                try:
                    self._copy(msg)
                except Exception:
                    break
            time.sleep(self.interval)
        Clock.schedule_once(lambda dt: self._done(), 0)

    def _copy(self, msg):
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(msg)
        self.sent_count += 1
        Clock.schedule_once(lambda dt, m=msg: self._on_sent(m, False), 0)

    def _on_sent(self, msg, auto):
        self.count_text = str(self.sent_count)
        self._update_stats()
        t = msg[:8] + '..' if len(msg) > 8 else msg
        tag = '自动' if auto else '复制'
        self._log(f'#{self.sent_count} {tag}: {t}')

    def _done(self):
        self.is_running = False
        self.is_paused = False
        self.status_text = '完成'
        self._update_stats()
        e = time.time() - self.start_time if self.start_time else 0
        self._log(f'完成 {self.sent_count}条 {e:.0f}秒')

    def _update_stats(self):
        if self.start_time:
            e = time.time() - self.start_time
            s = self.sent_count / e if e > 0 else 0
            self.speed_text = f'{s:.1f}条/秒 | {e:.0f}秒'

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
        Clock.schedule_once(lambda dt: self._check_service(), 1)


if __name__ == '__main__':
    MsgApp().run()
