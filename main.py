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
from kivy.uix.switch import Switch
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.utils import get_color_from_hex
from kivy.animation import Animation
from kivy.properties import ListProperty, StringProperty, NumericProperty

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

# iOS风格颜色主题
C_BG_GRADIENT_START = get_color_from_hex('#F2F2F7')  # iOS浅灰背景
C_BG_GRADIENT_END = get_color_from_hex('#E5E5EA')

# iOS系统颜色
C_IOS_BLUE = get_color_from_hex('#007AFF')
C_IOS_GREEN = get_color_from_hex('#34C759')
C_IOS_RED = get_color_from_hex('#FF3B30')
C_IOS_ORANGE = get_color_from_hex('#FF9500')
C_IOS_YELLOW = get_color_from_hex('#FFCC00')
C_IOS_PURPLE = get_color_from_hex('#AF52DE')
C_IOS_PINK = get_color_from_hex('#FF2D55')
C_IOS_TEAL = get_color_from_hex('#5AC8FA')
C_IOS_INDIGO = get_color_from_hex('#5856D6')

# 卡片颜色
C_CARD = (1, 1, 1, 0.95)
C_CARD_GROUPED = (1, 1, 1, 0.9)

# 文字颜色
C_TEXT = (0.1, 0.1, 0.1, 1)
C_TEXT_SECONDARY = (0.4, 0.4, 0.4, 1)
C_TEXT_TERTIARY = (0.6, 0.6, 0.6, 1)
C_TEXT_WHITE = (1, 1, 1, 1)

class IOSCard(BoxLayout):
    """iOS风格卡片"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [16, 14, 16, 14]
        self.spacing = 10
        self.opacity = 0
        self.scale = 0.95
        
        with self.canvas.before:
            # 阴影
            Color(0, 0, 0, 0.05)
            self._shadow = RoundedRectangle(pos=(self.x+1, self.y-1), size=self.size, radius=[12])
            # 背景
            Color(*C_CARD)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
        self.bind(pos=self._update, size=self._update)
        
        # iOS风格入场动画
        Clock.schedule_once(self._animate_in, 0.05)
    
    def _update(self, *a):
        self._shadow.pos = (self.x+1, self.y-1)
        self._shadow.size = self.size
        self._bg.pos = self.pos
        self._bg.size = self.size
    
    def _animate_in(self, dt):
        # iOS风格弹簧动画
        anim = Animation(opacity=1, scale=1, duration=0.4, t='out_back')
        anim.start(self)

class IOSButton(Button):
    """iOS风格按钮"""
    def __init__(self, color=C_IOS_BLUE, **kwargs):
        super().__init__(**kwargs)
        self.color = color
        self.background_color = (0, 0, 0, 0)
        self.color = C_TEXT_WHITE
        self.bold = True
        
        with self.canvas.before:
            Color(*color)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self._update_bg, size=self._update_bg)
        self.bind(on_press=self._on_press)
        self.bind(on_release=self._on_release)
    
    def _update_bg(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size
    
    def _on_press(self, *args):
        # iOS风格按压缩放
        anim = Animation(scale_x=0.96, scale_y=0.96, opacity=0.9, duration=0.1)
        anim.start(self)
    
    def _on_release(self, *args):
        anim = Animation(scale_x=1, scale_y=1, opacity=1, duration=0.2, t='out_back')
        anim.start(self)

class IOSTextButton(Button):
    """iOS风格文字按钮"""
    def __init__(self, color=C_IOS_BLUE, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.color = color
        self.bold = True

class IOSSegmentedControl(BoxLayout):
    """iOS风格分段控件"""
    def __init__(self, options, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = 0
        self.size_hint_y = None
        self.height = 32
        self.callback = callback
        self.buttons = []
        self.selected_index = 0
        
        with self.canvas.before:
            Color(0.9, 0.9, 0.92, 1)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[8])
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        for i, option in enumerate(options):
            btn = IOSTextButton(text=option, font_size=13, font_name=FONT)
            btn.bind(on_press=lambda x, idx=i: self._select(idx))
            self.add_widget(btn)
            self.buttons.append(btn)
        
        self._update_selection()
    
    def _update_bg(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size
    
    def _select(self, index):
        self.selected_index = index
        self._update_selection()
        if self.callback:
            self.callback(index)
    
    def _update_selection(self):
        for i, btn in enumerate(self.buttons):
            if i == self.selected_index:
                btn.color = C_TEXT_WHITE
                with btn.canvas.before:
                    Color(*C_IOS_BLUE)
                    btn._bg = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[6])
            else:
                btn.color = C_TEXT
                with btn.canvas.before:
                    Color(0, 0, 0, 0)
                    btn._bg = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[6])

class IOSListItem(BoxLayout):
    """iOS风格列表项"""
    def __init__(self, text, detail=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = 10
        self.size_hint_y = None
        self.height = 44
        self.padding = [16, 0, 16, 0]
        
        self.add_widget(Label(text=text, font_size=16, font_name=FONT, 
                             color=C_TEXT, size_hint_x=0.6, halign='left'))
        
        if detail:
            self.add_widget(Label(text=detail, font_size=14, font_name=FONT, 
                                 color=C_TEXT_SECONDARY, size_hint_x=0.3, halign='right'))
        
        # 箭头
        self.add_widget(Label(text=">", font_size=16, font_name=FONT, 
                             color=C_TEXT_TERTIARY, size_hint_x=0.1, halign='right'))

class MsgApp(App):
    def build(self):
        Window.clearcolor = C_BG_GRADIENT_START
        
        self.title = "消息助手"
        self.is_running = False
        self.is_paused = False
        self.sent_count = 0
        self.current_idx = 0
        self.history = self._load_history()
        self.auto_send_service = None
        self.start_time = None

        root = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation='vertical', padding=16, spacing=20, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        # 标题
        header = BoxLayout(orientation='vertical', size_hint_y=None, height=50)
        title = Label(text="消息助手", font_size=34, font_name=FONT, 
                      bold=True, color=C_TEXT, size_hint_y=None, height=40, halign='left')
        header.add_widget(title)
        content.add_widget(header)

        # 服务状态卡片
        card_service = IOSCard(size_hint_y=None, height=120)
        card_service.add_widget(Label(text="服务状态", font_size=13, font_name=FONT, 
                                     color=C_TEXT_SECONDARY, size_hint_y=None, height=20, halign='left'))
        
        self.service_status = Label(text="无障碍服务未开启", font_size=17, font_name=FONT, 
                                   color=C_IOS_ORANGE, size_hint_y=None, height=30, halign='left')
        card_service.add_widget(self.service_status)
        
        btn_access = IOSButton(C_IOS_BLUE, text="开启无障碍服务", font_size=17, font_name=FONT, 
                              size_hint_y=None, height=44)
        btn_access.bind(on_press=self._open_accessibility)
        card_service.add_widget(btn_access)
        content.add_widget(card_service)

        # 消息输入卡片
        card_msg = IOSCard(size_hint_y=None, height=280)
        card_msg.add_widget(Label(text="消息内容", font_size=13, font_name=FONT, 
                                 color=C_TEXT_SECONDARY, size_hint_y=None, height=20, halign='left'))
        
        self.msg_input = TextInput(hint_text="输入消息，每行一条", multiline=True, font_size=16, 
                                  font_name=FONT, size_hint_y=None, height=150, padding=[12,10],
                                  background_color=(0.95, 0.95, 0.97, 1), foreground_color=C_TEXT)
        card_msg.add_widget(self.msg_input)
        
        # 字符计数
        self.char_count = Label(text="0 字符", font_size=13, font_name=FONT, 
                               color=C_TEXT_TERTIARY, size_hint_y=None, height=20, halign='right')
        self.msg_input.bind(text=self._update_char_count)
        card_msg.add_widget(self.char_count)
        
        # 预设按钮
        preset_row = GridLayout(cols=4, size_hint_y=None, height=32, spacing=8)
        presets = [
            ("表情", lambda x: self._preset("emoji"), C_IOS_GREEN),
            ("数字", lambda x: self._preset("num"), C_IOS_BLUE),
            ("问候", lambda x: self._preset("greet"), C_IOS_ORANGE),
            ("清空", lambda x: setattr(self.msg_input, 'text', ''), C_IOS_RED)
        ]
        for text, callback, color in presets:
            btn = IOSTextButton(color=color, text=text, font_size=14, font_name=FONT)
            btn.bind(on_press=callback)
            preset_row.add_widget(btn)
        card_msg.add_widget(preset_row)
        content.add_widget(card_msg)

        # 目标应用卡片
        card_app = IOSCard(size_hint_y=None, height=100)
        card_app.add_widget(Label(text="目标应用", font_size=13, font_name=FONT, 
                                 color=C_TEXT_SECONDARY, size_hint_y=None, height=20, halign='left'))
        
        app_row = IOSListItem("应用", detail="微信")
        self.app_sp = Spinner(text='微信', values=('微信','QQ','钉钉','飞书','Telegram','WhatsApp'), 
                             font_size=16, font_name=FONT, size_hint_x=0.7,
                             background_color=(0,0,0,0), color=C_TEXT_SECONDARY)
        app_row.clear_widgets()
        app_row.add_widget(Label(text="应用", font_size=16, font_name=FONT, 
                                color=C_TEXT, size_hint_x=0.3))
        app_row.add_widget(self.app_sp)
        card_app.add_widget(app_row)
        content.add_widget(card_app)

        # 设置卡片
        card_settings = IOSCard(size_hint_y=None, height=200)
        card_settings.add_widget(Label(text="设置", font_size=13, font_name=FONT, 
                                      color=C_TEXT_SECONDARY, size_hint_y=None, height=20, halign='left'))
        
        # 模式选择
        card_settings.add_widget(Label(text="发送模式", font_size=15, font_name=FONT, 
                                      color=C_TEXT, size_hint_y=None, height=25, halign='left'))
        self.mode_control = IOSSegmentedControl(['顺序', '随机', '单条'], callback=self._on_mode_change)
        card_settings.add_widget(self.mode_control)
        
        # 间隔滑块
        card_settings.add_widget(Label(text="发送间隔", font_size=15, font_name=FONT, 
                                      color=C_TEXT, size_hint_y=None, height=25, halign='left'))
        slider_row = BoxLayout(size_hint_y=None, height=30)
        self.speed_sl = Slider(min=0.5, max=5.0, value=1.5, step=0.1, size_hint_x=0.7)
        self.speed_lbl = Label(text="1.5秒", font_size=15, font_name=FONT, 
                              color=C_TEXT_SECONDARY, size_hint_x=0.3)
        self.speed_sl.bind(value=lambda i,v: setattr(self.speed_lbl, 'text', f"{v:.1f}秒"))
        slider_row.add_widget(self.speed_sl)
        slider_row.add_widget(self.speed_lbl)
        card_settings.add_widget(slider_row)
        
        # 批量输入
        batch_row = IOSListItem("发送数量", detail="0")
        self.batch_input = TextInput(text="0", input_filter='int', font_size=16, font_name=FONT, 
                                    size_hint_x=0.5, height=30, padding=[6,4], multiline=False,
                                    background_color=(0,0,0,0), foreground_color=C_TEXT_SECONDARY)
        batch_row.clear_widgets()
        batch_row.add_widget(Label(text="发送数量", font_size=16, font_name=FONT, 
                                  color=C_TEXT, size_hint_x=0.5))
        batch_row.add_widget(self.batch_input)
        batch_row.add_widget(Label(text="(0=无限)", font_size=13, font_name=FONT, 
                                  color=C_TEXT_TERTIARY, size_hint_x=0.2))
        card_settings.add_widget(batch_row)
        content.add_widget(card_settings)

        # 控制卡片
        card_control = IOSCard(size_hint_y=None, height=120)
        card_control.add_widget(Label(text="控制", font_size=13, font_name=FONT, 
                                     color=C_TEXT_SECONDARY, size_hint_y=None, height=20, halign='left'))
        
        btn_row = GridLayout(cols=3, size_hint_y=None, height=50, spacing=12)
        self.btn_start = IOSButton(C_IOS_GREEN, text="开始", font_size=17, font_name=FONT)
        self.btn_pause = IOSButton(C_IOS_ORANGE, text="暂停", font_size=17, font_name=FONT, disabled=True)
        self.btn_stop = IOSButton(C_IOS_RED, text="停止", font_size=17, font_name=FONT, disabled=True)
        self.btn_start.bind(on_press=self._start)
        self.btn_pause.bind(on_press=self._pause)
        self.btn_stop.bind(on_press=self._stop)
        btn_row.add_widget(self.btn_start)
        btn_row.add_widget(self.btn_pause)
        btn_row.add_widget(self.btn_stop)
        card_control.add_widget(btn_row)
        content.add_widget(card_control)

        # 状态卡片
        card_status = IOSCard(size_hint_y=None, height=100)
        card_status.add_widget(Label(text="状态", font_size=13, font_name=FONT, 
                                    color=C_TEXT_SECONDARY, size_hint_y=None, height=20, halign='left'))
        
        status_row = BoxLayout(size_hint_y=None, height=30)
        self.status_lbl = Label(text="就绪", font_size=17, font_name=FONT, color=C_TEXT)
        self.count_lbl = Label(text="0", font_size=28, font_name=FONT, bold=True, color=C_IOS_BLUE)
        status_row.add_widget(self.status_lbl)
        status_row.add_widget(self.count_lbl)
        card_status.add_widget(status_row)
        
        # 统计信息
        self.stats_lbl = Label(text="速度: 0条/秒 | 耗时: 0秒", font_size=13, font_name=FONT, 
                              color=C_TEXT_TERTIARY, size_hint_y=None, height=20)
        card_status.add_widget(self.stats_lbl)
        content.add_widget(card_status)

        # 日志卡片
        card_log = IOSCard(size_hint_y=None, height=200)
        card_log.add_widget(Label(text="日志", font_size=13, font_name=FONT, 
                                 color=C_TEXT_SECONDARY, size_hint_y=None, height=20, halign='left'))
        
        self.log_area = TextInput(readonly=True, background_color=(0.95, 0.95, 0.97, 1), 
                                 foreground_color=C_TEXT, font_size=13, font_name=FONT, 
                                 size_hint_y=None, height=150)
        card_log.add_widget(self.log_area)
        content.add_widget(card_log)

        # 历史记录卡片
        card_history = IOSCard(size_hint_y=None, height=120)
        card_history.add_widget(Label(text="历史记录", font_size=13, font_name=FONT, 
                                     color=C_TEXT_SECONDARY, size_hint_y=None, height=20, halign='left'))
        
        self.history_spinner = Spinner(text='选择历史消息', values=('暂无历史记录',), 
                                      font_size=15, font_name=FONT, size_hint_y=None, height=40,
                                      background_color=(0,0,0,0), color=C_TEXT_SECONDARY)
        self.history_spinner.bind(text=self._load_history_message)
        card_history.add_widget(self.history_spinner)
        
        history_btn_row = GridLayout(cols=2, size_hint_y=None, height=32, spacing=12)
        btn_save = IOSTextButton(C_IOS_BLUE, text="保存当前", font_size=15, font_name=FONT)
        btn_save.bind(on_press=self._save_current_message)
        btn_clear = IOSTextButton(C_IOS_RED, text="清空历史", font_size=15, font_name=FONT)
        btn_clear.bind(on_press=self._clear_history)
        history_btn_row.add_widget(btn_save)
        history_btn_row.add_widget(btn_clear)
        card_history.add_widget(history_btn_row)
        content.add_widget(card_history)

        root.add_widget(content)
        
        # 检查无障碍服务状态
        Clock.schedule_once(lambda dt: self._check_service(), 1)
        
        return root

    def _update_char_count(self, instance, value):
        """更新字符计数"""
        count = len(value)
        self.char_count.text = f"{count} 字符"

    def _on_mode_change(self, index):
        """模式切换回调"""
        modes = ['顺序', '随机', '单条']
        self._log(f"已切换到{modes[index]}模式")

    def _check_service(self):
        """检查无障碍服务状态"""
        if ANDROID:
            try:
                AutoSendService = autoclass('com.wechat.flood.AutoSendService')
                service = AutoSendService.getInstance()
                if service and service.isServiceReady():
                    self.service_status.text = "无障碍服务已开启"
                    self.service_status.color = C_IOS_GREEN
                    self.auto_send_service = service
                else:
                    self.service_status.text = "无障碍服务未开启"
                    self.service_status.color = C_IOS_ORANGE
            except:
                self.service_status.text = "无障碍服务未开启"
                self.service_status.color = C_IOS_ORANGE
        else:
            self.service_status.text = "仅支持Android设备"
            self.service_status.color = C_IOS_ORANGE

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

    def _load_history_message(self, spinner, text):
        """加载历史消息"""
        if text and text != '选择历史消息' and text != '暂无历史记录':
            self.msg_input.text = text

    def _save_current_message(self, *args):
        """保存当前消息到历史"""
        current = self.msg_input.text.strip()
        if current and current not in self.history:
            self.history.insert(0, current)
            self.history = self.history[:20]
            self._save_history()
            self._update_history_spinner()
            self._log("已保存到历史记录")

    def _clear_history(self, *args):
        """清空历史记录"""
        self.history = []
        self._save_history()
        self._update_history_spinner()
        self._log("已清空历史记录")

    def _update_history_spinner(self):
        """更新历史记录下拉框"""
        if self.history:
            self.history_spinner.values = self.history[:10]
        else:
            self.history_spinner.values = ('暂无历史记录',)

    def _preset(self, kind):
        if kind == "emoji":
            self.msg_input.text = "😀\n😂\n🤣\n😍\n🥰\n😎\n🤩\n😘\n😋\n🤔\n👍\n❤️\n🔥\n✨\n🎉"
        elif kind == "num":
            self.msg_input.text = "\n".join(str(i) for i in range(1,21))
        elif kind == "greet":
            self.msg_input.text = "你好\n早上好\n下午好\n晚上好\n在吗\n忙吗\n吃饭了吗\n晚安"
        self._log("已加载预设")

    def _vibrate(self):
        """振动反馈"""
        if ANDROID:
            try:
                Vibrator = autoclass('android.os.Vibrator')
                activity = autoclass('org.kivy.android.PythonActivity').mActivity
                vibrator = activity.getSystemService(activity.VIBRATOR_SERVICE)
                vibrator.vibrate(50)
            except:
                pass

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
        
        if ANDROID and not self.auto_send_service:
            self._log("请先开启无障碍服务")
            return
        
        self.messages = msgs
        self.is_running = True
        self.is_paused = False
        self.sent_count = 0
        self.current_idx = 0
        self.start_time = time.time()
        self.btn_start.disabled = True
        self.btn_pause.disabled = False
        self.btn_stop.disabled = False
        self.status_lbl.text = "运行中..."
        self._vibrate()
        self._log(f"开始 {len(msgs)} 条消息")
        
        self._save_current_message()
        
        if ANDROID and self.auto_send_service:
            package = self._get_app_package()
            batch = int(self.batch_input.text or 0) or 999999
            self.auto_send_service.setBatchMode(batch)
            self._log(f"目标: {self.app_sp.text}")
            threading.Thread(target=self._auto_send_loop, daemon=True).start()
        else:
            threading.Thread(target=self._clipboard_loop, daemon=True).start()

    def _auto_send_loop(self):
        """自动发送循环"""
        mode = ['顺序', '随机', '单条'][self.mode_control.selected_index]
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
                Clock.schedule_once(lambda dt: self._update_stats())
                self._vibrate()
                
                batch = int(self.batch_input.text or 0) or 999999
                if self.sent_count >= batch:
                    break
            except Exception as e:
                Clock.schedule_once(lambda dt, err=str(e): self._log(f"错误: {err}"))
                break
            
            time.sleep(interval)
        
        Clock.schedule_once(lambda dt: self._end())

    def _clipboard_loop(self):
        """剪贴板模式循环"""
        mode = ['顺序', '随机', '单条'][self.mode_control.selected_index]
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
                Clock.schedule_once(lambda dt: self._update_stats())
                self._vibrate()
            except Exception as e:
                Clock.schedule_once(lambda dt, err=str(e): self._log(f"错误: {err}"))
                break
            
            time.sleep(interval)
        
        Clock.schedule_once(lambda dt: self._end())

    def _update_stats(self):
        """更新统计信息"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            speed = self.sent_count / elapsed if elapsed > 0 else 0
            self.stats_lbl.text = f"速度: {speed:.1f}条/秒 | 耗时: {elapsed:.0f}秒"

    def _end(self):
        self.is_running = False
        self.is_paused = False
        self.btn_start.disabled = False
        self.btn_pause.disabled = True
        self.btn_pause.text = "暂停"
        self.btn_stop.disabled = True
        self.status_lbl.text = "已停止"
        self._vibrate()
        self._log(f"完成 共{self.sent_count}条")
        self._update_stats()
        self._save_history()

    def _pause(self, *a):
        if not self.is_running: return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.btn_pause.text = "继续"
            self.status_lbl.text = "已暂停"
            self._vibrate()
            self._log("已暂停")
        else:
            self.btn_pause.text = "暂停"
            self.status_lbl.text = "运行中..."
            self._vibrate()
            self._log("已继续")

    def _stop(self, *a):
        if not self.is_running: return
        self.is_running = False
        self.is_paused = False
        if self.auto_send_service:
            self.auto_send_service.stopSending()
        self._vibrate()
        self._log("正在停止...")

if __name__ == "__main__":
    MsgApp().run()
