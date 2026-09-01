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
from kivy.properties import ListProperty, StringProperty

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

# 柔光玻璃彩色主题
C_BG_GRADIENT_START = get_color_from_hex('#667eea')
C_BG_GRADIENT_END = get_color_from_hex('#764ba2')

# 卡片颜色（半透明）
C_CARD_1 = (1, 1, 1, 0.85)
C_CARD_2 = (0.95, 0.95, 1, 0.8)
C_CARD_3 = (0.9, 1, 0.95, 0.8)
C_CARD_4 = (1, 0.95, 0.9, 0.8)
C_CARD_5 = (0.95, 0.9, 1, 0.8)  # 新增：粉色卡片

# 按钮颜色
C_PRIMARY = get_color_from_hex('#4facfe')
C_PRIMARY_GRADIENT = get_color_from_hex('#00f2fe')
C_SUCCESS = get_color_from_hex('#43e97b')
C_SUCCESS_GRADIENT = get_color_from_hex('#38f9d7')
C_WARNING = get_color_from_hex('#fa709a')
C_WARNING_GRADIENT = get_color_from_hex('#fee140')
C_DANGER = get_color_from_hex('#ff6b6b')
C_DANGER_GRADIENT = get_color_from_hex('#ffa500')
C_INFO = get_color_from_hex('#a18cd1')
C_INFO_GRADIENT = get_color_from_hex('#fbc2eb')

# 文字颜色
C_TEXT = (0.2, 0.2, 0.3, 1)
C_TEXT_SUB = (0.4, 0.4, 0.5, 1)
C_TEXT_WHITE = (1, 1, 1, 1)

class AnimatedCard(BoxLayout):
    """带动画的柔光玻璃卡片"""
    def __init__(self, card_color=C_CARD_1, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [16, 12, 16, 12]
        self.spacing = 8
        self.card_color = card_color
        self.opacity = 0  # 初始透明
        
        with self.canvas.before:
            Color(0, 0, 0, 0.1)
            self._shadow = RoundedRectangle(pos=(self.x+2, self.y-2), size=self.size, radius=[16])
            Color(*card_color)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[16])
        self.bind(pos=self._update, size=self._update)
        
        # 入场动画
        Clock.schedule_once(self._animate_in, 0.1)
    
    def _update(self, *a):
        self._shadow.pos = (self.x+2, self.y-2)
        self._shadow.size = self.size
        self._bg.pos = self.pos
        self._bg.size = self.size
    
    def _animate_in(self, dt):
        anim = Animation(opacity=1, duration=0.3)
        anim.start(self)

class PulsingButton(Button):
    """带脉冲效果的按钮"""
    def __init__(self, color_start, color_end, **kwargs):
        super().__init__(**kwargs)
        self.color_start = color_start
        self.color_end = color_end
        self.background_color = (0, 0, 0, 0)
        self.color = C_TEXT_WHITE
        
        with self.canvas.before:
            Color(*color_start)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
        self.bind(pos=self._update_bg, size=self._update_bg)
        self.bind(on_press=self._on_press)
        self.bind(on_release=self._on_release)
    
    def _update_bg(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size
    
    def _on_press(self, *args):
        anim = Animation(size_hint_x=0.95, size_hint_y=0.95, duration=0.1)
        anim.start(self)
    
    def _on_release(self, *args):
        anim = Animation(size_hint_x=1, size_hint_y=1, duration=0.1)
        anim.start(self)

class StatusIndicator(BoxLayout):
    """状态指示器（带动画）"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = 8
        self.size_hint_y = None
        self.height = 30
        
        self.indicator = Label(text="●", font_size=16, color=C_WARNING, size_hint_x=0.1)
        self.add_widget(self.indicator)
        
        self.status_text = Label(text="就绪", font_size=13, font_name=FONT, 
                                color=C_TEXT_SUB, size_hint_x=0.9)
        self.add_widget(self.status_text)
        
        # 脉冲动画
        self._pulse_animation()
    
    def _pulse_animation(self):
        anim = Animation(color=(1, 0.8, 0, 1), duration=0.5) + \
               Animation(color=C_WARNING, duration=0.5)
        anim.repeat = True
        anim.start(self.indicator)
    
    def set_status(self, text, color=C_WARNING):
        self.status_text.text = text
        self.indicator.color = color
        if color == C_SUCCESS:
            anim = Animation(color=(0.2, 1, 0.5, 1), duration=0.5) + \
                   Animation(color=C_SUCCESS, duration=0.5)
            anim.repeat = True
            anim.start(self.indicator)
        elif color == C_DANGER:
            anim = Animation(color=(1, 0.3, 0.3, 1), duration=0.5) + \
                   Animation(color=C_DANGER, duration=0.5)
            anim.repeat = True
            anim.start(self.indicator)

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
        content = BoxLayout(orientation='vertical', padding=16, spacing=12, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        # 标题区域
        title_box = BoxLayout(orientation='vertical', size_hint_y=None, height=60)
        title = Label(text="[b]消息助手[/b]", markup=True, font_size=26, font_name=FONT, 
                      color=C_TEXT_WHITE, size_hint_y=None, height=35)
        subtitle = Label(text="智能自动发送工具", font_size=12, font_name=FONT, 
                        color=(1, 1, 1, 0.7), size_hint_y=None, height=20)
        title_box.add_widget(title)
        title_box.add_widget(subtitle)
        content.add_widget(title_box)

        # 无障碍服务状态卡片
        card_service = AnimatedCard(card_color=C_CARD_4, size_hint_y=None, height=100)
        card_service.add_widget(Label(text="[服务状态]", font_size=14, font_name=FONT, 
                                     color=C_WARNING, size_hint_y=None, height=22))
        self.service_indicator = StatusIndicator()
        card_service.add_widget(self.service_indicator)
        btn_accessibility = PulsingButton(C_INFO, C_INFO_GRADIENT, text="[开启] 无障碍服务", 
                                         font_size=14, font_name=FONT, size_hint_y=None, height=40)
        btn_accessibility.bind(on_press=self._open_accessibility)
        card_service.add_widget(btn_accessibility)
        content.add_widget(card_service)

        # 消息输入卡片
        card1 = AnimatedCard(card_color=C_CARD_1, size_hint_y=None, height=250)
        card1.add_widget(Label(text="[消息内容]", font_size=15, font_name=FONT, 
                              color=C_PRIMARY, size_hint_y=None, height=26))
        
        # 消息输入区域
        input_box = BoxLayout(orientation='vertical', size_hint_y=None, height=160)
        self.msg_input = TextInput(hint_text="输入消息，每行一条\n支持emoji表情 😀", 
                                  multiline=True, font_size=14, font_name=FONT, 
                                  size_hint_y=None, height=130, padding=[10,8],
                                  background_color=(1, 1, 1, 0.6), foreground_color=C_TEXT)
        input_box.add_widget(self.msg_input)
        
        # 字符计数
        self.char_count = Label(text="0 字符", font_size=11, font_name=FONT, 
                               color=C_TEXT_SUB, size_hint_y=None, height=20)
        self.msg_input.bind(text=self._update_char_count)
        input_box.add_widget(self.char_count)
        card1.add_widget(input_box)
        
        # 预设按钮
        btn_row = GridLayout(cols=4, size_hint_y=None, height=36, spacing=6)
        presets = [
            ("表情", lambda x: self._preset("emoji"), C_SUCCESS),
            ("数字", lambda x: self._preset("num"), C_INFO),
            ("问候", lambda x: self._preset("greet"), C_WARNING),
            ("清空", lambda x: setattr(self.msg_input, 'text', ''), C_DANGER)
        ]
        for text, callback, color in presets:
            b = PulsingButton(color, (color[0]*0.8, color[1]*0.8, color[2]*0.8, 1), 
                             text=text, font_size=12, font_name=FONT)
            b.bind(on_press=callback)
            btn_row.add_widget(b)
        card1.add_widget(btn_row)
        content.add_widget(card1)

        # 目标应用卡片
        card_target = AnimatedCard(card_color=C_CARD_3, size_hint_y=None, height=100)
        card_target.add_widget(Label(text="[目标应用]", font_size=15, font_name=FONT, 
                                    color=C_SUCCESS, size_hint_y=None, height=26))
        row_target = BoxLayout(size_hint_y=None, height=36)
        row_target.add_widget(Label(text="应用", font_size=13, font_name=FONT, 
                                   color=C_TEXT_SUB, size_hint_x=0.3))
        self.app_sp = Spinner(text='微信', values=('微信','QQ','钉钉','飞书','Telegram','WhatsApp'), 
                             font_size=13, font_name=FONT, size_hint_x=0.7,
                             background_color=C_SUCCESS, color=C_TEXT_WHITE)
        row_target.add_widget(self.app_sp)
        card_target.add_widget(row_target)
        content.add_widget(card_target)

        # 设置卡片
        card2 = AnimatedCard(card_color=C_CARD_2, size_hint_y=None, height=220)
        card2.add_widget(Label(text="[设置]", font_size=15, font_name=FONT, 
                              color=C_INFO, size_hint_y=None, height=26))
        
        # 模式
        row1 = BoxLayout(size_hint_y=None, height=36)
        row1.add_widget(Label(text="模式", font_size=13, font_name=FONT, 
                             color=C_TEXT_SUB, size_hint_x=0.3))
        self.mode_sp = Spinner(text='顺序', values=('顺序','随机','单条'), 
                              font_size=13, font_name=FONT, size_hint_x=0.7,
                              background_color=C_INFO, color=C_TEXT_WHITE)
        row1.add_widget(self.mode_sp)
        card2.add_widget(row1)
        
        # 间隔
        row2 = BoxLayout(size_hint_y=None, height=36)
        row2.add_widget(Label(text="间隔", font_size=13, font_name=FONT, 
                             color=C_TEXT_SUB, size_hint_x=0.3))
        self.speed_sl = Slider(min=0.5, max=5.0, value=1.5, step=0.1, size_hint_x=0.5)
        self.speed_lbl = Label(text="1.5s", font_size=13, font_name=FONT, 
                              color=C_TEXT, size_hint_x=0.2)
        self.speed_sl.bind(value=lambda i,v: setattr(self.speed_lbl, 'text', f"{v:.1f}s"))
        row2.add_widget(self.speed_sl)
        row2.add_widget(self.speed_lbl)
        card2.add_widget(row2)
        
        # 批量
        row3 = BoxLayout(size_hint_y=None, height=36)
        row3.add_widget(Label(text="批量(0=无限)", font_size=13, font_name=FONT, 
                             color=C_TEXT_SUB, size_hint_x=0.4))
        self.batch_input = TextInput(text="0", input_filter='int', font_size=13, font_name=FONT, 
                                    size_hint_x=0.6, height=30, padding=[6,4], multiline=False,
                                    background_color=(1, 1, 1, 0.6), foreground_color=C_TEXT)
        row3.add_widget(self.batch_input)
        card2.add_widget(row3)
        
        # 振动反馈开关
        row4 = BoxLayout(size_hint_y=None, height=36)
        row4.add_widget(Label(text="振动反馈", font_size=13, font_name=FONT, 
                             color=C_TEXT_SUB, size_hint_x=0.5))
        self.vibrate_switch = Switch(active=True, size_hint_x=0.5)
        row4.add_widget(self.vibrate_switch)
        card2.add_widget(row4)
        
        content.add_widget(card2)

        # 控制卡片
        card3 = AnimatedCard(card_color=C_CARD_4, size_hint_y=None, height=80)
        card3.add_widget(Label(text="[控制]", font_size=15, font_name=FONT, 
                              color=C_DANGER, size_hint_y=None, height=26))
        btn_row2 = GridLayout(cols=3, size_hint_y=None, height=45, spacing=8)
        self.btn_start = PulsingButton(C_SUCCESS, C_SUCCESS_GRADIENT, text="[开始]", 
                                      font_size=15, font_name=FONT)
        self.btn_pause = PulsingButton(C_WARNING, C_WARNING_GRADIENT, text="[暂停]", 
                                      font_size=15, font_name=FONT, disabled=True)
        self.btn_stop = PulsingButton(C_DANGER, C_DANGER_GRADIENT, text="[停止]", 
                                     font_size=15, font_name=FONT, disabled=True)
        self.btn_start.bind(on_press=self._start)
        self.btn_pause.bind(on_press=self._pause)
        self.btn_stop.bind(on_press=self._stop)
        btn_row2.add_widget(self.btn_start)
        btn_row2.add_widget(self.btn_pause)
        btn_row2.add_widget(self.btn_stop)
        card3.add_widget(btn_row2)
        content.add_widget(card3)

        # 状态卡片
        card4 = AnimatedCard(card_color=C_CARD_5, size_hint_y=None, height=80)
        card4.add_widget(Label(text="[状态]", font_size=15, font_name=FONT, 
                              color=C_PRIMARY, size_hint_y=None, height=20))
        status_row = BoxLayout()
        self.status_lbl = Label(text="就绪", font_size=13, font_name=FONT, color=C_TEXT_SUB)
        self.count_lbl = Label(text="0", font_size=22, font_name=FONT, bold=True, color=C_PRIMARY)
        status_row.add_widget(self.status_lbl)
        status_row.add_widget(self.count_lbl)
        card4.add_widget(status_row)
        
        # 统计信息
        stats_row = BoxLayout(size_hint_y=None, height=20)
        self.stats_lbl = Label(text="速度: 0条/秒 | 耗时: 0秒", font_size=11, font_name=FONT, 
                              color=C_TEXT_SUB)
        stats_row.add_widget(self.stats_lbl)
        card4.add_widget(stats_row)
        content.add_widget(card4)

        # 日志卡片
        card5 = AnimatedCard(card_color=(0.1, 0.1, 0.2, 0.9), size_hint_y=None, height=200)
        card5.add_widget(Label(text="[日志]", font_size=15, font_name=FONT, 
                              color=C_PRIMARY_GRADIENT, size_hint_y=None, height=26))
        self.log_area = TextInput(readonly=True, background_color=(0.05, 0.05, 0.1, 0.8), 
                                 foreground_color=C_SUCCESS_GRADIENT, font_size=11, font_name=FONT, 
                                 size_hint_y=None, height=140)
        card5.add_widget(self.log_area)
        content.add_widget(card5)

        # 历史记录卡片
        card6 = AnimatedCard(card_color=C_CARD_1, size_hint_y=None, height=120)
        card6.add_widget(Label(text="[历史记录]", font_size=15, font_name=FONT, 
                              color=C_INFO, size_hint_y=None, height=26))
        
        # 历史消息列表
        history_box = BoxLayout(orientation='vertical', size_hint_y=None, height=70)
        self.history_spinner = Spinner(text='选择历史消息', values=('暂无历史记录',), 
                                      font_size=12, font_name=FONT, size_hint_y=None, height=35,
                                      background_color=C_INFO, color=C_TEXT_WHITE)
        self.history_spinner.bind(text=self._load_history_message)
        history_box.add_widget(self.history_spinner)
        
        history_btn_row = GridLayout(cols=2, size_hint_y=None, height=30, spacing=6)
        btn_save = PulsingButton(C_SUCCESS, C_SUCCESS_GRADIENT, text="保存当前", 
                                font_size=12, font_name=FONT)
        btn_save.bind(on_press=self._save_current_message)
        btn_clear_history = PulsingButton(C_DANGER, C_DANGER_GRADIENT, text="清空历史", 
                                         font_size=12, font_name=FONT)
        btn_clear_history.bind(on_press=self._clear_history)
        history_btn_row.add_widget(btn_save)
        history_btn_row.add_widget(btn_clear_history)
        history_box.add_widget(history_btn_row)
        card6.add_widget(history_box)
        content.add_widget(card6)

        root.add_widget(content)
        
        # 检查无障碍服务状态
        Clock.schedule_once(lambda dt: self._check_service(), 1)
        
        return root

    def _update_char_count(self, instance, value):
        """更新字符计数"""
        count = len(value)
        self.char_count.text = f"{count} 字符"

    def _check_service(self):
        """检查无障碍服务状态"""
        if ANDROID:
            try:
                AutoSendService = autoclass('com.wechat.flood.AutoSendService')
                service = AutoSendService.getInstance()
                if service and service.isServiceReady():
                    self.service_indicator.set_status("无障碍服务已开启", C_SUCCESS)
                    self.auto_send_service = service
                else:
                    self.service_indicator.set_status("无障碍服务未开启", C_WARNING)
            except:
                self.service_indicator.set_status("无障碍服务未开启", C_WARNING)
        else:
            self.service_indicator.set_status("仅支持Android设备", C_WARNING)

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
            self.history = self.history[:20]  # 只保留20条
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
        if ANDROID and self.vibrate_switch.active:
            try:
                Vibrator = autoclass('android.os.Vibrator')
                activity = autoclass('org.kivy.android.PythonActivity').mActivity
                vibrator = activity.getSystemService(activity.VIBRATOR_SERVICE)
                vibrator.vibrate(50)  # 50毫秒
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
        
        # 检查无障碍服务
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
        
        # 自动保存到历史
        self._save_current_message()
        
        # 启动自动发送
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
                Clock.schedule_once(lambda dt: self._update_stats())
                self._vibrate()
                
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
        """剪贴板模式循环"""
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
        self.btn_pause.text = "[暂停]"
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
            self.btn_pause.text = "[继续]"
            self.status_lbl.text = "已暂停"
            self._vibrate()
            self._log("已暂停")
        else:
            self.btn_pause.text = "[暂停]"
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
