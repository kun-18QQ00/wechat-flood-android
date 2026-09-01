# -*- coding: utf-8 -*-
import os
import json
import threading
import time
import random
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle

# Android imports
try:
    from jnius import autoclass, cast
    from android.runnable import run_on_ui_thread
    ANDROID = True
except:
    ANDROID = False

# 注册中文字体
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'chinese.ttf')
if os.path.exists(FONT_PATH):
    try:
        LabelBase.register(name='CN', fn_regular=FONT_PATH)
        FONT = 'CN'
    except Exception as e:
        print(f"字体加载失败: {e}")
        FONT = 'Roboto'
else:
    FONT = 'Roboto'

# 颜色主题
C_PRIMARY = (0.07, 0.75, 0.38, 1)
C_PRIMARY_DARK = (0.05, 0.6, 0.3, 1)
C_DANGER = (0.91, 0.30, 0.24, 1)
C_WARNING = (0.95, 0.61, 0.07, 1)
C_INFO = (0.20, 0.60, 0.86, 1)
C_BG = (0.96, 0.97, 0.98, 1)
C_CARD = (1, 1, 1, 1)
C_TEXT = (0.17, 0.24, 0.31, 1)
C_TEXT_SUB = (0.50, 0.55, 0.55, 1)

class CardBox(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [16, 12, 16, 12]
        self.spacing = 8
        with self.canvas.before:
            Color(*C_CARD)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
        self.bind(pos=self._update, size=self._update)
    def _update(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size

class MsgApp(App):
    def build(self):
        Window.clearcolor = C_BG
        self.title = "消息助手"
        self.is_running = False
        self.is_paused = False
        self.sent_count = 0
        self.current_idx = 0
        self.history = self._load_history()
        self.auto_send_service = None

        root = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation='vertical', padding=16, spacing=12, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        # 标题
        title = Label(text="[b]消息助手[/b]", markup=True, font_size=22, font_name=FONT, color=C_PRIMARY, size_hint_y=None, height=40)
        content.add_widget(title)

        # 无障碍服务状态
        self.service_status = Label(text="[!] 无障碍服务未开启", font_size=12, font_name=FONT, color=C_WARNING, size_hint_y=None, height=30)
        content.add_widget(self.service_status)
        
        # 开启无障碍服务按钮
        btn_accessibility = Button(text="[开启] 无障碍服务", font_size=14, font_name=FONT, 
                                   background_color=C_INFO, color=(1,1,1,1), size_hint_y=None, height=40)
        btn_accessibility.bind(on_press=self._open_accessibility)
        content.add_widget(btn_accessibility)

        # 消息输入卡片
        card1 = CardBox(size_hint_y=None, height=220)
        card1.add_widget(Label(text="消息内容", font_size=14, font_name=FONT, color=C_TEXT, size_hint_y=None, height=24, halign='left', text_size=(None,None)))
        self.msg_input = TextInput(hint_text="输入消息，每行一条", multiline=True, font_size=14, font_name=FONT, size_hint_y=None, height=130, padding=[10,8])
        card1.add_widget(self.msg_input)
        btn_row = GridLayout(cols=3, size_hint_y=None, height=36, spacing=6)
        for text, callback in [("表情", lambda x: self._preset("emoji")), ("数字", lambda x: self._preset("num")), ("清空", lambda x: setattr(self.msg_input, 'text', ''))]:
            b = Button(text=text, font_size=13, font_name=FONT, background_color=C_INFO, color=(1,1,1,1))
            b.bind(on_press=callback)
            btn_row.add_widget(b)
        card1.add_widget(btn_row)
        content.add_widget(card1)

        # 目标应用卡片
        card_target = CardBox(size_hint_y=None, height=100)
        card_target.add_widget(Label(text="目标应用", font_size=14, font_name=FONT, color=C_TEXT, size_hint_y=None, height=24, halign='left'))
        row_target = BoxLayout(size_hint_y=None, height=36)
        row_target.add_widget(Label(text="应用", font_size=13, font_name=FONT, color=C_TEXT_SUB, size_hint_x=0.3))
        self.app_sp = Spinner(text='微信', values=('微信','QQ','钉钉','飞书','Telegram','WhatsApp'), font_size=13, font_name=FONT, size_hint_x=0.7)
        row_target.add_widget(self.app_sp)
        card_target.add_widget(row_target)
        content.add_widget(card_target)

        # 设置卡片
        card2 = CardBox(size_hint_y=None, height=200)
        card2.add_widget(Label(text="设置", font_size=14, font_name=FONT, color=C_TEXT, size_hint_y=None, height=24, halign='left'))
        # 模式
        row1 = BoxLayout(size_hint_y=None, height=36)
        row1.add_widget(Label(text="模式", font_size=13, font_name=FONT, color=C_TEXT_SUB, size_hint_x=0.3))
        self.mode_sp = Spinner(text='顺序', values=('顺序','随机','单条'), font_size=13, font_name=FONT, size_hint_x=0.7)
        row1.add_widget(self.mode_sp)
        card2.add_widget(row1)
        # 间隔
        row2 = BoxLayout(size_hint_y=None, height=36)
        row2.add_widget(Label(text="间隔", font_size=13, font_name=FONT, color=C_TEXT_SUB, size_hint_x=0.3))
        self.speed_sl = Slider(min=0.5, max=5.0, value=1.5, step=0.1, size_hint_x=0.5)
        self.speed_lbl = Label(text="1.5s", font_size=13, font_name=FONT, color=C_TEXT, size_hint_x=0.2)
        self.speed_sl.bind(value=lambda i,v: setattr(self.speed_lbl, 'text', f"{v:.1f}s"))
        row2.add_widget(self.speed_sl)
        row2.add_widget(self.speed_lbl)
        card2.add_widget(row2)
        # 批量
        row3 = BoxLayout(size_hint_y=None, height=36)
        row3.add_widget(Label(text="批量(0=无限)", font_size=13, font_name=FONT, color=C_TEXT_SUB, size_hint_x=0.4))
        self.batch_input = TextInput(text="0", input_filter='int', font_size=13, font_name=FONT, size_hint_x=0.6, height=30, padding=[6,4], multiline=False)
        row3.add_widget(self.batch_input)
        card2.add_widget(row3)
        content.add_widget(card2)

        # 控制卡片
        card3 = CardBox(size_hint_y=None, height=70)
        card3.add_widget(Label(text="控制", font_size=14, font_name=FONT, color=C_TEXT, size_hint_y=None, height=24, halign='left'))
        btn_row2 = GridLayout(cols=3, size_hint_y=None, height=40, spacing=8)
        self.btn_start = Button(text="开始", font_size=14, font_name=FONT, background_color=C_PRIMARY, color=(1,1,1,1))
        self.btn_pause = Button(text="暂停", font_size=14, font_name=FONT, background_color=C_WARNING, color=(1,1,1,1), disabled=True)
        self.btn_stop = Button(text="停止", font_size=14, font_name=FONT, background_color=C_DANGER, color=(1,1,1,1), disabled=True)
        self.btn_start.bind(on_press=self._start)
        self.btn_pause.bind(on_press=self._pause)
        self.btn_stop.bind(on_press=self._stop)
        btn_row2.add_widget(self.btn_start)
        btn_row2.add_widget(self.btn_pause)
        btn_row2.add_widget(self.btn_stop)
        card3.add_widget(btn_row2)
        content.add_widget(card3)

        # 状态卡片
        card4 = CardBox(size_hint_y=None, height=60)
        card4.add_widget(Label(text="状态", font_size=14, font_name=FONT, color=C_TEXT, size_hint_y=None, height=20))
        status_row = BoxLayout()
        self.status_lbl = Label(text="就绪", font_size=13, font_name=FONT, color=C_TEXT_SUB)
        self.count_lbl = Label(text="0", font_size=18, font_name=FONT, bold=True, color=C_PRIMARY)
        status_row.add_widget(self.status_lbl)
        status_row.add_widget(self.count_lbl)
        card4.add_widget(status_row)
        content.add_widget(card4)

        # 日志
        card5 = CardBox(size_hint_y=None, height=180)
        card5.add_widget(Label(text="日志", font_size=14, font_name=FONT, color=C_TEXT, size_hint_y=None, height=24, halign='left'))
        self.log_area = TextInput(readonly=True, background_color=(0.12,0.12,0.18,1), foreground_color=(0.65,0.89,0.63,1), font_size=11, font_name=FONT, size_hint_y=None, height=120)
        card5.add_widget(self.log_area)
        content.add_widget(card5)

        root.add_widget(content)
        
        # 检查无障碍服务状态
        Clock.schedule_once(lambda dt: self._check_service(), 1)
        
        return root

    def _check_service(self):
        """检查无障碍服务状态"""
        if ANDROID:
            try:
                AutoSendService = autoclass('com.wechat.flood.AutoSendService')
                service = AutoSendService.getInstance()
                if service and service.isServiceReady():
                    self.service_status.text = "[OK] 无障碍服务已开启"
                    self.service_status.color = C_PRIMARY
                    self.auto_send_service = service
                else:
                    self.service_status.text = "[!] 无障碍服务未开启"
                    self.service_status.color = C_WARNING
            except:
                self.service_status.text = "[!] 无障碍服务未开启"
                self.service_status.color = C_WARNING
        else:
            self.service_status.text = "[!] 仅支持Android设备"
            self.service_status.color = C_WARNING

    def _open_accessibility(self, *args):
        """打开无障碍设置"""
        if ANDROID:
            try:
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                Settings = autoclass('android.provider.Settings')
                intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
                PythonActivity.mActivity.startActivity(intent)
                self._log("请开启「消息助手」无障碍服务")
            except Exception as e:
                self._log(f"打开设置失败: {e}")
        else:
            self._log("仅支持Android设备")

    def _get_app_package(self):
        """获取应用包名"""
        app_map = {
            '微信': 'com.tencent.mm',
            'QQ': 'com.tencent.mobileqq',
            '钉钉': 'com.alibaba.android.rimet',
            '飞书': 'com.ss.android.lark',
            'Telegram': 'org.telegram.messenger',
            'WhatsApp': 'com.whatsapp'
        }
        return app_map.get(self.app_sp.text, 'com.tencent.mm')

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_area.text += f"[{ts}] {msg}\n"

    def _load_history(self):
        try:
            p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'history.json')
            if os.path.exists(p):
                return json.load(open(p, 'r', encoding='utf-8'))
        except: pass
        return []

    def _save_history(self):
        try:
            p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'history.json')
            json.dump(self.history[:100], open(p, 'w', encoding='utf-8'), ensure_ascii=False)
        except: pass

    def _preset(self, kind):
        if kind == "emoji":
            self.msg_input.text = "hello\nhi\nhey\nok\nnice\ngood\nyes\nno\nthanks\nsorry"
        elif kind == "num":
            self.msg_input.text = "\n".join(str(i) for i in range(1,21))
        self._log("已加载预设")

    def _start(self, *a):
        if self.is_running: return
        raw = self.msg_input.text.strip()
        if not raw:
            self.status_lbl.text = "请输入消息"
            return
        msgs = [m.strip() for m in raw.split("\n") if m.strip()]
        if not msgs:
            self.status_lbl.text = "消息为空"
            return
        
        # 检查无障碍服务
        if ANDROID and not self.auto_send_service:
            self._log("请先开启无障碍服务")
            return
        
        self.messages = msgs
        self.is_running = True
        self.is_paused = False
        self.sent_count = 0
        self.current_idx = 0
        self.btn_start.disabled = True
        self.btn_pause.disabled = False
        self.btn_stop.disabled = False
        self.status_lbl.text = "运行中..."
        self._log(f"开始 {len(msgs)} 条消息")
        
        # 启动自动发送
        if ANDROID and self.auto_send_service:
            package = self._get_app_package()
            batch = int(self.batch_input.text or 0) or 999999
            self.auto_send_service.setBatchMode(batch)
            self._log(f"目标: {self.app_sp.text}")
            threading.Thread(target=self._auto_send_loop, daemon=True).start()
        else:
            # 非Android环境使用剪贴板模式
            threading.Thread(target=self._clipboard_loop, daemon=True).start()

    def _auto_send_loop(self):
        """自动发送循环"""
        mode = self.mode_sp.text
        interval = self.speed_sl.value
        package = self._get_app_package()
        
        while self.is_running:
            if self.is_paused:
                time.sleep(0.1)
                continue
            
            if mode == "随机":
                msg = random.choice(self.messages)
            elif mode == "单条":
                msg = self.messages[0]
            else:
                msg = self.messages[self.current_idx % len(self.messages)]
                self.current_idx += 1
            
            try:
                self.auto_send_service.sendMessage(msg, package, 1, 300)
                self.sent_count += 1
                d = msg[:12] + "..." if len(msg) > 12 else msg
                Clock.schedule_once(lambda dt, m=d: self._log(f"#{self.sent_count} {m}"))
                Clock.schedule_once(lambda dt: setattr(self.count_lbl, 'text', str(self.sent_count)))
                
                # 检查批量限制
                batch = int(self.batch_input.text or 0) or 999999
                if self.sent_count >= batch:
                    break
            except Exception as e:
                Clock.schedule_once(lambda dt, err=str(e): self._log(f"错误: {err}"))
                break
            
            time.sleep(interval)
        
        Clock.schedule_once(lambda dt: self._end())

    def _clipboard_loop(self):
        """剪贴板模式循环（非Android环境）"""
        mode = self.mode_sp.text
        interval = self.speed_sl.value
        batch = int(self.batch_input.text or 0) or 999999
        
        while self.is_running and self.sent_count < batch:
            if self.is_paused:
                time.sleep(0.1)
                continue
            
            if mode == "随机":
                msg = random.choice(self.messages)
            elif mode == "单条":
                msg = self.messages[0]
            else:
                msg = self.messages[self.current_idx % len(self.messages)]
                self.current_idx += 1
            
            try:
                from kivy.core.clipboard import Clipboard
                Clipboard.copy(msg)
                self.sent_count += 1
                d = msg[:12] + "..." if len(msg) > 12 else msg
                Clock.schedule_once(lambda dt, m=d: self._log(f"#{self.sent_count} {m}"))
                Clock.schedule_once(lambda dt: setattr(self.count_lbl, 'text', str(self.sent_count)))
            except Exception as e:
                Clock.schedule_once(lambda dt, err=str(e): self._log(f"错误: {err}"))
                break
            
            time.sleep(interval)
        
        Clock.schedule_once(lambda dt: self._end())

    def _end(self):
        self.is_running = False
        self.is_paused = False
        self.btn_start.disabled = False
        self.btn_pause.disabled = True
        self.btn_pause.text = "暂停"
        self.btn_stop.disabled = True
        self.status_lbl.text = "已停止"
        self._log(f"完成 共{self.sent_count}条")
        self._save_history()

    def _pause(self, *a):
        if not self.is_running: return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.btn_pause.text = "继续"
            self.status_lbl.text = "已暂停"
            self._log("已暂停")
        else:
            self.btn_pause.text = "暂停"
            self.status_lbl.text = "运行中..."
            self._log("已继续")

    def _stop(self, *a):
        if not self.is_running: return
        self.is_running = False
        self.is_paused = False
        if self.auto_send_service:
            self.auto_send_service.stopSending()
        self._log("正在停止...")

if __name__ == "__main__":
    MsgApp().run()
