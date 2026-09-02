# -*- coding: utf-8 -*-
"""
消息助手 v5.0 - iOS风格
完全重写，解决闪退、布局、字体等问题
"""
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
from kivy.uix.slider import Slider
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.utils import platform
from kivy.metrics import dp, sp

# Android相关
ANDROID = platform == 'android'

# 注册中文字体
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'chinese.ttf')
if os.path.exists(FONT_PATH):
    try:
        LabelBase.register(name='CN', fn_regular=FONT_PATH)
        FONT_NAME = 'CN'
    except:
        FONT_NAME = 'Roboto'
else:
    FONT_NAME = 'Roboto'

# ============ 颜色定义 ============
class Colors:
    # iOS系统颜色
    BLUE = (0, 0.478, 1, 1)
    GREEN = (0.204, 0.788, 0.349, 1)
    RED = (1, 0.231, 0.188, 1)
    ORANGE = (1, 0.584, 0, 1)
    PURPLE = (0.686, 0.322, 0.871, 1)
    PINK = (1, 0.176, 0.333, 1)
    TEAL = (0.353, 0.784, 0.98, 1)
    YELLOW = (1, 0.8, 0, 1)
    
    # 灰度
    BG = (0.949, 0.949, 0.969, 1)  # #F2F2F7
    CARD = (1, 1, 1, 1)
    SEPARATOR = (0.863, 0.863, 0.882, 1)
    
    # 文字
    TEXT_PRIMARY = (0.11, 0.11, 0.118, 1)
    TEXT_SECONDARY = (0.427, 0.427, 0.447, 1)
    TEXT_TERTIARY = (0.627, 0.627, 0.647, 1)
    TEXT_WHITE = (1, 1, 1, 1)
    
    # 状态
    SUCCESS = GREEN
    WARNING = ORANGE
    DANGER = RED
    INFO = BLUE

# ============ 基础组件 ============

class IOSCard(BoxLayout):
    """iOS风格卡片"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [dp(16), dp(14), dp(16), dp(14)]
        self.spacing = dp(10)
        self.size_hint_y = None
        self.bind(minimum_height=self.setter('height'))
        
        with self.canvas.before:
            Color(*Colors.CARD)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=self._update_rect, size=self._update_rect)
    
    def _update_rect(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size

class SectionTitle(Label):
    """分组标题"""
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.font_size = sp(13)
        self.font_name = FONT_NAME
        self.color = Colors.TEXT_SECONDARY
        self.size_hint_y = None
        self.height = dp(20)
        self.halign = 'left'
        self.valign = 'middle'
        self.text_size = (None, None)
        self.bind(size=self._update_text_size)
    
    def _update_text_size(self, *args):
        self.text_size = (self.width - dp(32), None)

class IOSButton(Button):
    """iOS风格按钮"""
    def __init__(self, color=Colors.BLUE, **kwargs):
        super().__init__(**kwargs)
        self.font_size = sp(17)
        self.font_name = FONT_NAME
        self.bold = True
        self.background_color = (0, 0, 0, 0)
        self.color = Colors.TEXT_WHITE
        self.size_hint_y = None
        self.height = dp(50)
        
        with self.canvas.before:
            Color(*color)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=self._update_rect, size=self._update_rect)
    
    def _update_rect(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size

class IOSListItem(BoxLayout):
    """iOS风格列表项"""
    def __init__(self, title, value='', **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(44)
        self.padding = [dp(16), 0, dp(16), 0]
        
        self.title_label = Label(
            text=title,
            font_size=sp(17),
            font_name=FONT_NAME,
            color=Colors.TEXT_PRIMARY,
            size_hint_x=0.5,
            halign='left',
            valign='middle'
        )
        self.title_label.bind(size=self.title_label.setter('text_size'))
        self.add_widget(self.title_label)
        
        self.value_label = Label(
            text=value,
            font_size=sp(17),
            font_name=FONT_NAME,
            color=Colors.TEXT_SECONDARY,
            size_hint_x=0.5,
            halign='right',
            valign='middle'
        )
        self.value_label.bind(size=self.value_label.setter('text_size'))
        self.add_widget(self.value_label)

# ============ 主应用 ============

class MessageApp(App):
    def build(self):
        # 设置窗口背景
        Window.clearcolor = Colors.BG
        
        self.title = "消息助手"
        self.is_running = False
        self.is_paused = False
        self.sent_count = 0
        self.current_index = 0
        self.start_time = None
        self.history = self._load_history()
        
        # 主滚动视图
        scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            bar_color=Colors.TEXT_TERTIARY,
            bar_width=dp(4)
        )
        
        # 主布局
        main = BoxLayout(
            orientation='vertical',
            padding=[dp(16), dp(20), dp(16), dp(20)],
            spacing=dp(20),
            size_hint_y=None
        )
        main.bind(minimum_height=main.setter('height'))
        
        # ===== 标题 =====
        title_box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(60),
            spacing=dp(4)
        )
        title_box.add_widget(Label(
            text="消息助手",
            font_size=sp(34),
            font_name=FONT_NAME,
            bold=True,
            color=Colors.TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(40),
            halign='left'
        ))
        title_box.add_widget(Label(
            text="iOS 风格自动发送工具",
            font_size=sp(15),
            font_name=FONT_NAME,
            color=Colors.TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(20),
            halign='left'
        ))
        # 修正左对齐
        for child in title_box.children:
            child.bind(size=child.setter('text_size'))
        main.add_widget(title_box)
        
        # ===== 消息输入卡片 =====
        card1 = IOSCard()
        card1.add_widget(SectionTitle("消息内容"))
        
        self.msg_input = TextInput(
            hint_text="输入消息，每行一条\n支持emoji表情 😀",
            multiline=True,
            font_size=sp(17),
            font_name=FONT_NAME,
            size_hint_y=None,
            height=dp(150),
            padding=[dp(12), dp(10)],
            background_color=(0.95, 0.95, 0.97, 1),
            foreground_color=Colors.TEXT_PRIMARY,
            cursor_color=Colors.BLUE
        )
        card1.add_widget(self.msg_input)
        
        # 字符计数
        self.char_count = Label(
            text="0 字符",
            font_size=sp(13),
            font_name=FONT_NAME,
            color=Colors.TEXT_TERTIARY,
            size_hint_y=None,
            height=dp(20),
            halign='right'
        )
        self.char_count.bind(size=self.char_count.setter('text_size'))
        self.msg_input.bind(text=self._update_char_count)
        card1.add_widget(self.char_count)
        
        # 预设按钮
        preset_grid = GridLayout(
            cols=3,
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10)
        )
        for text, color, callback in [
            ("表情", Colors.GREEN, lambda x: self._load_preset("emoji")),
            ("数字", Colors.BLUE, lambda x: self._load_preset("num")),
            ("问候", Colors.ORANGE, lambda x: self._load_preset("greet"))
        ]:
            btn = Button(
                text=text,
                font_size=sp(15),
                font_name=FONT_NAME,
                background_color=color,
                color=Colors.TEXT_WHITE,
                size_hint_y=None,
                height=dp(40)
            )
            btn.bind(on_press=callback)
            preset_grid.add_widget(btn)
        card1.add_widget(preset_grid)
        main.add_widget(card1)
        
        # ===== 目标应用卡片 =====
        card2 = IOSCard()
        card2.add_widget(SectionTitle("目标应用"))
        
        self.app_buttons = {}
        app_grid = GridLayout(cols=3, size_hint_y=None, height=dp(120), spacing=dp(10))
        apps = [
            ("微信", Colors.GREEN),
            ("QQ", Colors.BLUE),
            ("钉钉", Colors.TEAL),
            ("飞书", Colors.PURPLE),
            ("Telegram", Colors.BLUE),
            ("WhatsApp", Colors.GREEN)
        ]
        for name, color in apps:
            btn = Button(
                text=name,
                font_size=sp(15),
                font_name=FONT_NAME,
                background_color=color,
                color=Colors.TEXT_WHITE,
                size_hint_y=None,
                height=dp(50)
            )
            btn.bind(on_press=lambda x, n=name: self._select_app(n))
            app_grid.add_widget(btn)
            self.app_buttons[name] = btn
        card2.add_widget(app_grid)
        
        self.selected_app_label = Label(
            text="当前: 微信",
            font_size=sp(15),
            font_name=FONT_NAME,
            color=Colors.BLUE,
            size_hint_y=None,
            height=dp(25)
        )
        card2.add_widget(self.selected_app_label)
        self.selected_app = "微信"
        main.add_widget(card2)
        
        # ===== 设置卡片 =====
        card3 = IOSCard()
        card3.add_widget(SectionTitle("发送设置"))
        
        # 模式选择
        mode_box = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        mode_box.add_widget(Label(
            text="模式",
            font_size=sp(17),
            font_name=FONT_NAME,
            color=Colors.TEXT_PRIMARY,
            size_hint_x=0.3,
            halign='left'
        ))
        self.mode_buttons = {}
        mode_grid = GridLayout(cols=3, size_hint_x=0.7, spacing=dp(8))
        for mode in ["顺序", "随机", "单条"]:
            btn = Button(
                text=mode,
                font_size=sp(14),
                font_name=FONT_NAME,
                background_color=Colors.BLUE if mode == "顺序" else Colors.TEXT_TERTIARY,
                color=Colors.TEXT_WHITE,
                size_hint_y=None,
                height=dp(36)
            )
            btn.bind(on_press=lambda x, m=mode: self._select_mode(m))
            mode_grid.add_widget(btn)
            self.mode_buttons[mode] = btn
        mode_box.add_widget(mode_grid)
        card3.add_widget(mode_box)
        self.selected_mode = "顺序"
        
        # 间隔设置
        interval_box = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
        interval_box.add_widget(Label(
            text="间隔",
            font_size=sp(17),
            font_name=FONT_NAME,
            color=Colors.TEXT_PRIMARY,
            size_hint_x=0.2,
            halign='left'
        ))
        
        slider_box = BoxLayout(orientation='vertical', size_hint_x=0.8)
        self.speed_slider = Slider(
            min=0.5,
            max=5.0,
            value=1.0,
            step=0.1,
            size_hint_y=None,
            height=dp(30),
            cursor_size=(dp(20), dp(20)),
            background_width=dp(4)
        )
        self.speed_slider.bind(value=self._update_speed)
        slider_box.add_widget(self.speed_slider)
        
        self.speed_label = Label(
            text="1.0 秒",
            font_size=sp(15),
            font_name=FONT_NAME,
            color=Colors.TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(25)
        )
        slider_box.add_widget(self.speed_label)
        interval_box.add_widget(slider_box)
        card3.add_widget(interval_box)
        
        # 批量设置
        batch_box = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        batch_box.add_widget(Label(
            text="数量",
            font_size=sp(17),
            font_name=FONT_NAME,
            color=Colors.TEXT_PRIMARY,
            size_hint_x=0.3,
            halign='left'
        ))
        self.batch_input = TextInput(
            text="0",
            font_size=sp(17),
            font_name=FONT_NAME,
            size_hint_x=0.7,
            size_hint_y=None,
            height=dp(40),
            padding=[dp(10), dp(8)],
            background_color=(0.95, 0.95, 0.97, 1),
            foreground_color=Colors.TEXT_PRIMARY,
            input_filter='int',
            multiline=False
        )
        batch_box.add_widget(self.batch_input)
        batch_box.add_widget(Label(
            text="(0=无限)",
            font_size=sp(13),
            font_name=FONT_NAME,
            color=Colors.TEXT_TERTIARY,
            size_hint_x=0.3
        ))
        card3.add_widget(batch_box)
        main.add_widget(card3)
        
        # ===== 控制卡片 =====
        card4 = IOSCard()
        card4.add_widget(SectionTitle("控制"))
        
        btn_grid = GridLayout(cols=3, size_hint_y=None, height=dp(55), spacing=dp(12))
        
        self.btn_start = Button(
            text="▶ 开始",
            font_size=sp(18),
            font_name=FONT_NAME,
            bold=True,
            background_color=Colors.GREEN,
            color=Colors.TEXT_WHITE,
            size_hint_y=None,
            height=dp(55)
        )
        self.btn_start.bind(on_press=self._start)
        btn_grid.add_widget(self.btn_start)
        
        self.btn_pause = Button(
            text="⏸ 暂停",
            font_size=sp(18),
            font_name=FONT_NAME,
            bold=True,
            background_color=Colors.ORANGE,
            color=Colors.TEXT_WHITE,
            size_hint_y=None,
            height=dp(55),
            disabled=True
        )
        self.btn_pause.bind(on_press=self._pause)
        btn_grid.add_widget(self.btn_pause)
        
        self.btn_stop = Button(
            text="⏹ 停止",
            font_size=sp(18),
            font_name=FONT_NAME,
            bold=True,
            background_color=Colors.RED,
            color=Colors.TEXT_WHITE,
            size_hint_y=None,
            height=dp(55),
            disabled=True
        )
        self.btn_stop.bind(on_press=self._stop)
        btn_grid.add_widget(self.btn_stop)
        
        card4.add_widget(btn_grid)
        main.add_widget(card4)
        
        # ===== 状态卡片 =====
        card5 = IOSCard()
        card5.add_widget(SectionTitle("状态"))
        
        status_box = BoxLayout(size_hint_y=None, height=dp(50))
        self.status_label = Label(
            text="就绪",
            font_size=sp(17),
            font_name=FONT_NAME,
            color=Colors.TEXT_PRIMARY,
            halign='left'
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        status_box.add_widget(self.status_label)
        
        self.count_label = Label(
            text="0",
            font_size=sp(32),
            font_name=FONT_NAME,
            bold=True,
            color=Colors.BLUE,
            halign='right'
        )
        self.count_label.bind(size=self.count_label.setter('text_size'))
        status_box.add_widget(self.count_label)
        card5.add_widget(status_box)
        
        self.stats_label = Label(
            text="速度: 0 条/秒 | 耗时: 0 秒",
            font_size=sp(13),
            font_name=FONT_NAME,
            color=Colors.TEXT_TERTIARY,
            size_hint_y=None,
            height=dp(20),
            halign='left'
        )
        self.stats_label.bind(size=self.stats_label.setter('text_size'))
        card5.add_widget(self.stats_label)
        main.add_widget(card5)
        
        # ===== 日志卡片 =====
        card6 = IOSCard()
        card6.add_widget(SectionTitle("日志"))
        
        self.log_area = TextInput(
            readonly=True,
            font_size=sp(14),
            font_name=FONT_NAME,
            size_hint_y=None,
            height=dp(150),
            padding=[dp(10), dp(8)],
            background_color=(0.95, 0.95, 0.97, 1),
            foreground_color=Colors.TEXT_PRIMARY,
            cursor_color=(0, 0, 0, 0)
        )
        card6.add_widget(self.log_area)
        main.add_widget(card6)
        
        # ===== 历史记录卡片 =====
        card7 = IOSCard()
        card7.add_widget(SectionTitle("历史记录"))
        
        history_grid = GridLayout(cols=2, size_hint_y=None, height=dp(44), spacing=dp(10))
        
        btn_save = Button(
            text="保存当前",
            font_size=sp(15),
            font_name=FONT_NAME,
            background_color=Colors.BLUE,
            color=Colors.TEXT_WHITE,
            size_hint_y=None,
            height=dp(44)
        )
        btn_save.bind(on_press=self._save_to_history)
        history_grid.add_widget(btn_save)
        
        btn_load = Button(
            text="加载历史",
            font_size=sp(15),
            font_name=FONT_NAME,
            background_color=Colors.PURPLE,
            color=Colors.TEXT_WHITE,
            size_hint_y=None,
            height=dp(44)
        )
        btn_load.bind(on_press=self._show_history)
        history_grid.add_widget(btn_load)
        
        card7.add_widget(history_grid)
        main.add_widget(card7)
        
        # 添加到滚动视图
        scroll.add_widget(main)
        
        # 初始化日志
        self._log("应用已启动")
        self._log("请先输入消息，然后点击开始")
        
        return scroll
    
    def _update_char_count(self, instance, value):
        self.char_count.text = f"{len(value)} 字符"
    
    def _update_speed(self, instance, value):
        self.speed_label.text = f"{value:.1f} 秒"
    
    def _select_app(self, app_name):
        self.selected_app = app_name
        self.selected_app_label.text = f"当前: {app_name}"
        for name, btn in self.app_buttons.items():
            btn.background_color = Colors.BLUE if name == app_name else Colors.TEXT_TERTIARY
        self._log(f"已选择: {app_name}")
    
    def _select_mode(self, mode):
        self.selected_mode = mode
        for name, btn in self.mode_buttons.items():
            btn.background_color = Colors.BLUE if name == mode else Colors.TEXT_TERTIARY
        self._log(f"模式: {mode}")
    
    def _load_preset(self, preset_type):
        presets = {
            "emoji": "😀\n😂\n🤣\n😍\n🥰\n😎\n🤩\n😘\n😋\n🤔\n👍\n❤️\n🔥\n✨\n🎉",
            "num": "\n".join(str(i) for i in range(1, 21)),
            "greet": "你好\n早上好\n下午好\n晚上好\n在吗\n忙吗\n吃饭了吗\n晚安"
        }
        self.msg_input.text = presets.get(preset_type, "")
        self._log(f"已加载预设: {preset_type}")
    
    def _log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.text += f"[{timestamp}] {message}\n"
    
    def _load_history(self):
        try:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'history.json')
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def _save_history(self):
        try:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'history.json')
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.history[:50], f, ensure_ascii=False)
        except:
            pass
    
    def _save_to_history(self, *args):
        text = self.msg_input.text.strip()
        if text and text not in self.history:
            self.history.insert(0, text)
            self._save_history()
            self._log("已保存到历史")
        else:
            self._log("消息为空或已存在")
    
    def _show_history(self, *args):
        if not self.history:
            self._log("暂无历史记录")
            return
        
        # 简单实现：加载最近一条
        self.msg_input.text = self.history[0]
        self._log(f"已加载历史记录 (共{len(self.history)}条)")
    
    def _vibrate(self):
        if ANDROID:
            try:
                from jnius import autoclass
                activity = autoclass('org.kivy.android.PythonActivity').mActivity
                vibrator = activity.getSystemService(activity.VIBRATOR_SERVICE)
                vibrator.vibrate(50)
            except:
                pass
    
    def _get_app_package(self):
        packages = {
            '微信': 'com.tencent.mm',
            'QQ': 'com.tencent.mobileqq',
            '钉钉': 'com.alibaba.android.rimet',
            '飞书': 'com.ss.android.lark',
            'Telegram': 'org.telegram.messenger',
            'WhatsApp': 'com.whatsapp'
        }
        return packages.get(self.selected_app, 'com.tencent.mm')
    
    def _start(self, *args):
        if self.is_running:
            return
        
        text = self.msg_input.text.strip()
        if not text:
            self._log("请输入消息内容")
            return
        
        messages = [m.strip() for m in text.split('\n') if m.strip()]
        if not messages:
            self._log("消息内容为空")
            return
        
        self.messages = messages
        self.is_running = True
        self.is_paused = False
        self.sent_count = 0
        self.current_index = 0
        self.start_time = time.time()
        
        self.btn_start.disabled = True
        self.btn_pause.disabled = False
        self.btn_stop.disabled = False
        self.status_label.text = "运行中..."
        self.status_label.color = Colors.GREEN
        
        self._vibrate()
        self._log(f"开始发送 {len(messages)} 条消息")
        self._log(f"目标: {self.selected_app} | 模式: {self.selected_mode}")
        
        # 在新线程中运行
        thread = threading.Thread(target=self._send_loop, daemon=True)
        thread.start()
    
    def _send_loop(self):
        interval = self.speed_slider.value
        batch = int(self.batch_input.text or '0') or 999999
        
        while self.is_running and self.sent_count < batch:
            if self.is_paused:
                time.sleep(0.1)
                continue
            
            # 选择消息
            if self.selected_mode == "随机":
                msg = random.choice(self.messages)
            elif self.selected_mode == "单条":
                msg = self.messages[0]
            else:  # 顺序
                msg = self.messages[self.current_index % len(self.messages)]
                self.current_index += 1
            
            try:
                # 复制到剪贴板
                from kivy.core.clipboard import Clipboard
                Clipboard.copy(msg)
                
                self.sent_count += 1
                
                # 更新UI（必须在主线程）
                display_msg = msg[:15] + "..." if len(msg) > 15 else msg
                Clock.schedule_once(lambda dt, m=display_msg: self._on_sent(m), 0)
                
                self._vibrate()
                
            except Exception as e:
                Clock.schedule_once(lambda dt, err=str(e): self._log(f"错误: {err}"), 0)
                break
            
            time.sleep(interval)
        
        Clock.schedule_once(lambda dt: self._on_complete(), 0)
    
    def _on_sent(self, message):
        self._log(f"#{self.sent_count} 已复制: {message}")
        self.count_label.text = str(self.sent_count)
        self._update_stats()
    
    def _on_complete(self):
        self.is_running = False
        self.is_paused = False
        self.btn_start.disabled = False
        self.btn_pause.disabled = True
        self.btn_stop.disabled = True
        self.btn_pause.text = "⏸ 暂停"
        self.status_label.text = "已停止"
        self.status_label.color = Colors.TEXT_PRIMARY
        self._log(f"完成! 共发送 {self.sent_count} 条")
        self._update_stats()
    
    def _update_stats(self):
        if self.start_time:
            elapsed = time.time() - self.start_time
            speed = self.sent_count / elapsed if elapsed > 0 else 0
            self.stats_label.text = f"速度: {speed:.1f} 条/秒 | 耗时: {elapsed:.0f} 秒"
    
    def _pause(self, *args):
        if not self.is_running:
            return
        
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.btn_pause.text = "▶ 继续"
            self.status_label.text = "已暂停"
            self.status_label.color = Colors.ORANGE
            self._log("已暂停")
        else:
            self.btn_pause.text = "⏸ 暂停"
            self.status_label.text = "运行中..."
            self.status_label.color = Colors.GREEN
            self._log("已继续")
        
        self._vibrate()
    
    def _stop(self, *args):
        if not self.is_running:
            return
        
        self.is_running = False
        self.is_paused = False
        self._vibrate()
        self._log("正在停止...")


if __name__ == '__main__':
    MessageApp().run()
