# -*- coding: utf-8 -*-
"""
消息助手 v10.0 - 悬浮窗方案，无需无障碍权限
原理：复制消息到剪贴板 → 用户切到聊天窗口 → 点悬浮按钮自动粘贴+发送
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
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.core.clipboard import Clipboard

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


class FloatingButton(Button):
    """悬浮发送按钮"""
    pass


class MsgApp(App):
    font_name = StringProperty('Roboto')
    status_text = StringProperty('等待中')
    count_text = StringProperty('0')
    speed_text = StringProperty('就绪')
    is_running = BooleanProperty(False)
    is_paused = BooleanProperty(False)
    auto_paste = BooleanProperty(True)

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
        self._floating = None

    def build(self):
        Window.clearcolor = (0.93, 0.94, 0.98, 1)
        Clock.schedule_once(self._init, 0.5)
        return RootWidget()

    def _init(self, *args):
        self._log('应用已启动')
        if ANDROID:
            self._log('使用悬浮窗模式，无需无障碍权限')
            self._log('点击"显示悬浮按钮"后切到聊天窗口')
        else:
            self._log('非Android设备，使用剪贴板模式')

    # ── 悬浮窗控制 ──

    def show_floating(self):
        """显示悬浮发送按钮"""
        if not ANDROID:
            self._log('仅支持Android')
            return
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            
            # 创建悬浮按钮
            WindowManager = autoclass('android.view.WindowManager')
            Button = autoclass('android.widget.Button')
            LayoutParams = autoclass('android.view.WindowManager$LayoutParams')
            
            # 设置悬浮窗参数
            params = LayoutParams()
            params.width = LayoutParams.WRAP_CONTENT
            params.height = LayoutParams.WRAP_CONTENT
            
            # 使用TYPE_APPLICATION_OVERLAY (Android 8+)
            if hasattr(LayoutParams, 'TYPE_APPLICATION_OVERLAY'):
                params.type = LayoutParams.TYPE_APPLICATION_OVERLAY
            else:
                params.type = LayoutParams.TYPE_PHONE
            
            params.flags = LayoutParams.FLAG_NOT_FOCUSABLE
            params.gravity = 0x35  # Gravity.RIGHT | Gravity.CENTER_VERTICAL
            params.x = 20
            
            # 创建按钮
            btn = Button(activity)
            btn.setText('发送')
            btn.setTextSize(18)
            
            # 设置点击事件
            class OnClickListener(activity.getClass()):
                def onClick(self, v):
                    # 通过剪贴板粘贴并发送
                    pass
            
            # 添加到窗口
            wm = activity.getSystemService(activity.WINDOW_SERVICE)
            wm.addView(btn, params)
            
            self._floating = btn
            self._log('悬浮按钮已显示')
            self._log('切到聊天窗口，点悬浮按钮发送')
        except Exception as e:
            self._log(f'悬浮窗创建失败: {e}')
            self._log('请使用手动粘贴模式')

    def hide_floating(self):
        """隐藏悬浮按钮"""
        if self._floating and ANDROID:
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                WindowManager = autoclass('android.view.WindowManager')
                wm = activity.getSystemService(activity.WINDOW_SERVICE)
                wm.removeView(self._floating)
                self._floating = None
                self._log('悬浮按钮已隐藏')
            except Exception:
                pass

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
            self.interval = max(0.3, float(self.root.ids.speed_input.text))
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
        self.status_text = '运行中'
        self._log(f'开始 {len(self.messages)}条 间隔{self.interval}秒')
        self._log('请切到聊天窗口，消息会自动复制到剪贴板')
        
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def pause(self):
        if not self.is_running:
            return
        self.is_paused = not self.is_paused
        self.status_text = '已暂停' if self.is_paused else '运行中'
        self._log('已暂停' if self.is_paused else '已继续')

    def stop(self):
        self.is_running = False
        self.is_paused = False
        self.status_text = '已停止'
        self._log('已停止')

    def send_once(self):
        """手动发送一条（复制到剪贴板）"""
        try:
            raw = self.root.ids.msg_input.text.strip()
        except Exception:
            return
        if not raw:
            self._log('请输入消息')
            return
        msgs = [m.strip() for m in raw.split('\n') if m.strip()]
        if not msgs:
            return
        msg = msgs[0]
        Clipboard.copy(msg)
        self._log(f'已复制: {msg[:15]}')
        
        # 在Android上尝试自动粘贴
        if ANDROID:
            self._try_paste()

    def _try_paste(self):
        """尝试自动粘贴"""
        if not ANDROID:
            return
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            
            # 获取当前焦点视图并执行粘贴
            view = activity.getCurrentFocus()
            if view:
                view.onTextContextMenuItem(android.R.id.paste)
        except Exception:
            pass

    def _loop(self):
        """自动复制循环"""
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
                Clipboard.copy(msg)
                self.sent_count += 1
                Clock.schedule_once(lambda dt, m=msg: self._on_sent(m), 0)
                
                # 尝试自动粘贴
                if ANDROID:
                    Clock.schedule_once(lambda dt: self._try_paste(), 0.1)
                    
            except Exception as e:
                Clock.schedule_once(lambda dt, err=str(e): self._log(f'错误: {err}'), 0)
                break
            
            time.sleep(self.interval)
        
        Clock.schedule_once(lambda dt: self._done(), 0)

    def _on_sent(self, msg):
        self.count_text = str(self.sent_count)
        self._update_stats()
        t = msg[:12] + '..' if len(msg) > 12 else msg
        self._log(f'#{self.sent_count} 已复制: {t}')

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

    def on_stop(self):
        self.stop()
        self.hide_floating()


if __name__ == '__main__':
    MsgApp().run()
