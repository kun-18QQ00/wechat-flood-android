\"\"\"
微信刷屏助手 Android 版 v3.0
基于 Kivy 框架，支持安卓打包为 APK
新增功能：自动打开微信、消息历史、深色模式、振动反馈
\"\"\"

import os
import json
import time
import random
import threading
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform
from kivy.storage.jsonstore import JsonStore

# 安卓平台适配
if platform == 'android':
    from android.runnable import run_on_ui_thread
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    ClipData = autoclass('android.content.ClipData')
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    PythonService = autoclass('org.kivy.android.PythonService')
    
    @run_on_ui_thread
    def android_copy(text):
        \"\"\"安卓复制到剪贴板\"\"\"
        activity = PythonActivity.mActivity
        clipboard = activity.getSystemService(Context.CLIPBOARD_SERVICE)
        clip = ClipData.newPlainText(\"msg\", text)
        clipboard.setPrimaryClip(clip)
    
    def android_toast(msg):
        \"\"\"安卓 Toast 提示\"\"\"
        try:
            Toast = autoclass('android.widget.Toast')
            activity = PythonActivity.mActivity
            
            @run_on_ui_thread
            def show():
                Toast.makeText(activity, msg, Toast.LENGTH_SHORT).show()
            show()
        except Exception:
            pass
    
    def android_vibrate(ms=100):
        \"\"\"安卓振动\"\"\"
        try:
            activity = PythonActivity.mActivity
            vibrator = activity.getSystemService(Context.VIBRATOR_SERVICE)
            vibrator.vibrate(ms)
        except Exception:
            pass
    
    def open_wechat():
        \"\"\"打开微信应用\"\"\"
        try:
            activity = PythonActivity.mActivity
            intent = activity.getPackageManager().getLaunchIntentForPackage(\"com.tencent.mm\")
            if intent:
                activity.startActivity(intent)
                return True
            return False
        except Exception:
            return False
    
    def share_to_wechat(text):
        \"\"\"通过分享功能发送到微信\"\"\"
        try:
            activity = PythonActivity.mActivity
            intent = Intent(Intent.ACTION_SEND)
            intent.setType(\"text/plain\")
            intent.putExtra(Intent.EXTRA_TEXT, text)
            chooser = Intent.createChooser(intent, \"分享到\")
            activity.startActivity(chooser)
        except Exception as e:
            android_toast(f\"分享失败: {str(e)}\")
else:
    def android_copy(text):
        \"\"\"桌面端复制（备用）\"\"\"
        try:
            import pyperclip
            pyperclip.copy(text)
        except Exception:
            pass
    
    def android_toast(msg):
        print(f\"[Toast] {msg}\")
    
    def android_vibrate(ms=100):
        print(f\"[Vibrate] {ms}ms\")
    
    def open_wechat():
        print(\"[Open WeChat]\")
        return False
    
    def share_to_wechat(text):
        print(f\"[Share] {text}\")


# 主题颜色
LIGHT_THEME = {
    \"bg\":         (0.96, 0.97, 0.98, 1),
    \"card\":       (1, 1, 1, 1),
    \"accent\":     (0.18, 0.80, 0.44, 1),
    \"accent_dk\":  (0.15, 0.68, 0.38, 1),
    \"warning\":    (0.95, 0.61, 0.07, 1),
    \"danger\":     (0.91, 0.30, 0.24, 1),
    \"info\":       (0.20, 0.60, 0.86, 1),
    \"text\":       (0.17, 0.24, 0.31, 1),
    \"text_sub\":   (0.50, 0.55, 0.55, 1),
    \"log_bg\":     (0.12, 0.12, 0.18, 1),
    \"log_text\":   (0.65, 0.89, 0.63, 1),
    \"white\":      (1, 1, 1, 1),
    \"input_bg\":   (0.98, 0.98, 0.98, 1),
    \"border\":     (0.90, 0.90, 0.90, 1),
}

DARK_THEME = {
    \"bg\":         (0.11, 0.11, 0.14, 1),
    \"card\":       (0.16, 0.16, 0.20, 1),
    \"accent\":     (0.30, 0.85, 0.50, 1),
    \"accent_dk\":  (0.25, 0.75, 0.45, 1),
    \"warning\":    (0.95, 0.65, 0.20, 1),
    \"danger\":     (0.90, 0.35, 0.30, 1),
    \"info\":       (0.30, 0.65, 0.90, 1),
    \"text\":       (0.95, 0.95, 0.97, 1),
    \"text_sub\":   (0.65, 0.65, 0.70, 1),
    \"log_bg\":     (0.08, 0.08, 0.12, 1),
    \"log_text\":   (0.65, 0.89, 0.63, 1),
    \"white\":      (0.20, 0.20, 0.24, 1),
    \"input_bg\":   (0.18, 0.18, 0.22, 1),
    \"border\":     (0.25, 0.25, 0.30, 1),
}

PRESETS_FILE = \"message_presets.json\"
HISTORY_FILE = \"message_history.json\"


class CardBox(BoxLayout):
    \"\"\"卡片容器组件\"\"\"
    def __init__(self, title=\"\", theme=None, **kwargs):
        super().__init__(orientation='vertical', padding=[12, 10, 12, 10],
                         spacing=6, size_hint_y=None, **kwargs)
        self.theme = theme or LIGHT_THEME
        self.bind(minimum_height=self.setter('height'))
        self.canvas.before.clear()
        with self.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(*self.theme[\"card\"])
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        if title:
            lbl = Label(text=title, font_size='16sp', bold=True,
                        color=self.theme[\"text\"], size_hint_y=None, height='30dp',
                        halign='left', valign='middle')
            lbl.bind(size=lbl.setter('text_size'))
            self.add_widget(lbl)
    
    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size


class WeChatFloodApp(App):
    def build(self):
        # 加载设置
        self.store = JsonStore(os.path.join(self.user_data_dir, 'settings.json'))
        self.dark_mode = self.store.get('dark_mode')['value'] if self.store.exists('dark_mode') else False
        self.theme = DARK_THEME if self.dark_mode else LIGHT_THEME
        
        Window.clearcolor = self.theme[\"bg\"]
        self.title = \"微信刷屏助手 v3.0\"
        
        # 状态变量
        self.is_running = False
        self.is_paused = False
        self.sent_count = 0
        self.last_sent = \"\"
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.send_thread = None
        self._timer_remaining = 0
        
        # 加载历史消息
        self.history = []
        self._load_history()
        
        # 构建UI
        root = BoxLayout(orientation='vertical', padding=8, spacing=8)
        
        # 顶部标题栏
        header = BoxLayout(size_hint_y=None, height='50dp', spacing=8)
        title_label = Label(text=\"[b]微信刷屏助手[/b]\", markup=True,
                           font_size='20sp', color=self.theme[\"text\"])
        header.add_widget(title_label)
        
        # 深色模式切换
        dark_switch = Switch(active=self.dark_mode, size_hint_x=None, width='60dp')
        dark_switch.bind(active=self._toggle_dark_mode)
        dark_label = Label(text=\"🌙\", font_size='18sp', size_hint_x=None, width='30dp\")
        header.add_widget(dark_label)
        header.add_widget(dark_switch)
        root.add_widget(header)
        
        # 主内容区
        main_scroll = ScrollView()
        main_content = BoxLayout(orientation='vertical', spacing=10, 
                                size_hint_y=None, padding=[0, 0, 0, 10])
        main_content.bind(minimum_height=main_content.setter('height'))
        
        # 消息输入卡片
        msg_card = CardBox(title=\"📝 消息内容\", theme=self.theme)
        
        # 消息输入
        self.msg_input = TextInput(
            hint_text=\"输入消息，每行一条...\",
            multiline=True,
            size_hint_y=None,
            height='120dp',
            background_color=self.theme[\"input_bg\"],
            foreground_color=self.theme[\"text\"],
            cursor_color=self.theme[\"accent\"],
            font_size='14sp'
        )
        msg_card.add_widget(self.msg_input)
        
        # 预设和历史按钮
        btn_row = BoxLayout(size_hint_y=None, height='40dp', spacing=8)
        
        preset_btn = Button(text=\"📦 预设消息\", background_color=self.theme[\"info\"],
                           font_size='13sp')
        preset_btn.bind(on_press=self._show_presets)
        btn_row.add_widget(preset_btn)
        
        history_btn = Button(text=\"📚 历史记录\", background_color=self.theme[\"info\"],
                            font_size='13sp')
        history_btn.bind(on_press=self._show_history)
        btn_row.add_widget(history_btn)
        
        clear_btn = Button(text=\"🗑️ 清空\", background_color=self.theme[\"danger\"],
                          font_size='13sp')
        clear_btn.bind(on_press=lambda x: self.msg_input.setter('text')(self.msg_input, ''))
        btn_row.add_widget(clear_btn)
        
        msg_card.add_widget(btn_row)
        main_content.add_widget(msg_card)
        
        # 设置卡片
        settings_card = CardBox(title=\"⚙️ 发送设置\", theme=self.theme)
        
        # 发送模式
        mode_row = BoxLayout(size_hint_y=None, height='40dp', spacing=8)
        mode_row.add_widget(Label(text=\"模式:\", color=self.theme[\"text\"], 
                                 size_hint_x=None, width='50dp'))
        self.mode_spinner = Spinner(
            text='顺序',
            values=('顺序', '随机', '单条'),
            size_hint_x=None,
            width='100dp',
            background_color=self.theme[\"accent\"]
        )
        mode_row.add_widget(self.mode_spinner)
        
        # 去重开关
        dedup_label = Label(text=\"去重:\", color=self.theme[\"text\"],
                           size_hint_x=None, width='50dp\")
        self.dedup_switch = Switch(active=True, size_hint_x=None, width='60dp\")
        mode_row.add_widget(dedup_label)
        mode_row.add_widget(self.dedup_switch)
        settings_card.add_widget(mode_row)
        
        # 速度控制
        speed_row = BoxLayout(size_hint_y=None, height='50dp', spacing=8)
        speed_row.add_widget(Label(text=\"间隔:\", color=self.theme[\"text\"],
                                  size_hint_x=None, width='50dp\"))
        self.speed_slider = Slider(min=0.1, max=5.0, value=1.0, step=0.1)
        self.speed_label = Label(text=\"1.0s\", color=self.theme[\"text\"],
                                size_hint_x=None, width='50dp\")
        self.speed_slider.bind(value=lambda x, v: setattr(self.speed_label, 'text', f\"{v:.1f}s\"))
        speed_row.add_widget(self.speed_slider)
        speed_row.add_widget(self.speed_label)
        settings_card.add_widget(speed_row)
        
        # 批量和定时
        limit_row = BoxLayout(size_hint_y=None, height='40dp', spacing=8)
        limit_row.add_widget(Label(text=\"批量:\", color=self.theme[\"text\"],
                                  size_hint_x=None, width='50dp\"))
        self.batch_input = TextInput(text=\"0\", input_filter='int',
                                    size_hint_x=None, width='80dp',
                                    background_color=self.theme[\"input_bg\"],
                                    foreground_color=self.theme[\"text\"])
        limit_row.add_widget(self.batch_input)
        limit_row.add_widget(Label(text=\"定时:\", color=self.theme[\"text\"],
                                  size_hint_x=None, width='50dp\"))
        self.timer_input = TextInput(text=\"0\", input_filter='int',
                                    size_hint_x=None, width='80dp',
                                    hint_text=\"秒\",
                                    background_color=self.theme[\"input_bg\"],
                                    foreground_color=self.theme[\"text\"])
        limit_row.add_widget(self.timer_input)
        settings_card.add_widget(limit_row)
        
        # 自动打开微信
        wechat_row = BoxLayout(size_hint_y=None, height='40dp', spacing=8)
        wechat_row.add_widget(Label(text=\"自动打开微信:\", color=self.theme[\"text\"]))
        self.auto_wechat = Switch(active=False, size_hint_x=None, width='60dp\")
        wechat_row.add_widget(self.auto_wechat)
        settings_card.add_widget(wechat_row)
        
        main_content.add_widget(settings_card)
        
        # 控制按钮
        control_card = CardBox(theme=self.theme)
        
        btn_grid = GridLayout(cols=3, size_hint_y=None, height='50dp', spacing=8)
        
        self.start_btn = Button(text=\"▶ 开始\", background_color=self.theme[\"accent\"],
                               font_size='16sp', bold=True)
        self.start_btn.bind(on_press=self.start_sending)
        
        self.pause_btn = Button(text=\"⏸ 暂停\", background_color=self.theme[\"warning\"],
                               font_size='16sp', disabled=True)
        self.pause_btn.bind(on_press=self.toggle_pause)
        
        self.stop_btn = Button(text=\"⏹ 停止\", background_color=self.theme[\"danger\"],
                              font_size='16sp', disabled=True)
        self.stop_btn.bind(on_press=self.stop_sending)
        
        btn_grid.add_widget(self.start_btn)
        btn_grid.add_widget(self.pause_btn)
        btn_grid.add_widget(self.stop_btn)
        control_card.add_widget(btn_grid)
        
        # 状态栏
        status_row = BoxLayout(size_hint_y=None, height='30dp')
        self.status_label = Label(text=\"⏸ 就绪\", color=self.theme[\"text_sub\"],
                                 font_size='13sp')
        self.count_label = Label(text=\"已发送: 0\", color=self.theme[\"text_sub\"],
                                font_size='13sp\")
        self.timer_label = Label(text=\"\", color=self.theme[\"warning\"],
                                font_size='13sp\")
        status_row.add_widget(self.status_label)
        status_row.add_widget(self.count_label)
        status_row.add_widget(self.timer_label)
        control_card.add_widget(status_row)
        
        main_content.add_widget(control_card)
        
        # 日志卡片
        log_card = CardBox(title=\"📋 运行日志\", theme=self.theme)
        
        self.log_area = TextInput(
            readonly=True,
            background_color=self.theme[\"log_bg\"],
            foreground_color=self.theme[\"log_text\"],
            font_size='12sp',
            size_hint_y=None,
            height='150dp'
        )
        log_card.add_widget(self.log_area)
        
        clear_log_btn = Button(text=\"清空日志\", size_hint_y=None, height='35dp',
                              background_color=self.theme[\"danger\"], font_size='13sp\")
        clear_log_btn.bind(on_press=lambda x: setattr(self.log_area, 'text', ''))
        log_card.add_widget(clear_log_btn)
        
        main_content.add_widget(log_card)
        
        main_scroll.add_widget(main_content)
        root.add_widget(main_scroll)
        
        # 使用说明弹窗（首次启动）
        if not self.store.exists('shown_help'):
            Clock.schedule_once(lambda dt: self._show_help(), 1)
            self.store.put('shown_help', value=True)
        
        self._log(\"🚀 应用已启动\")
        return root
    
    def _toggle_dark_mode(self, instance, value):
        \"\"\"切换深色模式\"\"\"
        self.dark_mode = value
        self.store.put('dark_mode', value=value)
        self.theme = DARK_THEME if value else LIGHT_THEME
        android_toast(\"重启应用以生效\")
    
    def _load_history(self):
        \"\"\"加载历史消息\"\"\"
        try:
            history_path = os.path.join(self.user_data_dir, HISTORY_FILE)
            if os.path.exists(history_path):
                with open(history_path, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
        except Exception:
            self.history = []
    
    def _save_history(self, messages):
        \"\"\"保存历史消息\"\"\"
        try:
            # 添加到历史，去重并限制数量
            for msg in messages:
                if msg not in self.history:
                    self.history.insert(0, msg)
            self.history = self.history[:100]  # 保留最近100条
            
            history_path = os.path.join(self.user_data_dir, HISTORY_FILE)
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log(f\"⚠️ 保存历史失败: {e}\")
    
    def _show_help(self):
        \"\"\"显示使用说明\"\"\"
        help_text = \"\"\"[b]微信刷屏助手 v3.0 使用说明[/b]

[size=14sp]基本操作：
1. 在消息框输入内容，每行一条
2. 点击「开始」自动复制并发送
3. 使用「暂停/恢复」控制发送

高级功能：
• [b]顺序模式[/b]：按顺序循环发送
• [b]随机模式[/b]：随机选择消息
• [b]单条模式[/b]：只发第一条
• [b]去重[/b]：避免连续重复
• [b]批量[/b]：设置发送总数限制
• [b]定时[/b]：自动停止时间

安卓特别提示：
• 需要手动切换到微信粘贴
• 可开启「自动打开微信」
• 支持通过系统分享发送

快捷操作：
• 使用预设消息快速开始
• 查看历史记录复用消息\"\"\"
        
        popup = Popup(title=\"使用说明\", content=Label(text=help_text, markup=True,
                                                      text_size=(None, None),
                                                      halign='left', valign='top'),
                     size_hint=(0.9, 0.8))
        popup.open()
    
    def _show_presets(self, *args):
        \"\"\"显示预设消息\"\"\"
        presets = {
            \"测试消息\": [\"测试消息1\", \"测试消息2\", \"测试消息3\"],
            \"表情刷屏\": [\"😀\", \"😂\", \"🤣\", \"😍\", \"🥰\"],
            \"数字递增\": [str(i) for i in range(1, 21)],
            \"节日祝福\": [\"新年快乐！🎆\", \"恭喜发财！🧧\", \"万事如意！✨\"],
        }
        
        content = BoxLayout(orientation='vertical', spacing=8, padding=8)
        
        for name, msgs in presets.items():
            btn = Button(text=f\"📦 {name} ({len(msgs)}条)\",
                        size_hint_y=None, height='45dp',
                        background_color=self.theme[\"info\"])
            btn.bind(on_press=lambda x, m=msgs: self._apply_preset(m))
            content.add_widget(btn)
        
        popup = Popup(title=\"预设消息\", content=content,
                     size_hint=(0.8, 0.6))
        popup.open()
    
    def _apply_preset(self, messages):
        \"\"\"应用预设消息\"\"\"
        self.msg_input.text = '\\n'.join(messages)
        android_toast(f\"已加载 {len(messages)} 条预设消息\")
    
    def _show_history(self, *args):
        \"\"\"显示历史记录\"\"\"
        if not self.history:
            android_toast(\"暂无历史记录\")
            return
        
        content = BoxLayout(orientation='vertical', spacing=4, padding=8)
        scroll = ScrollView()
        msg_list = BoxLayout(orientation='vertical', spacing=4,
                            size_hint_y=None)
        msg_list.bind(minimum_height=msg_list.setter('height'))
        
        for i, msg in enumerate(self.history[:50]):
            btn = Button(text=msg[:30] + (\"...\" if len(msg) > 30 else \"\"),
                        size_hint_y=None, height='40dp',
                        background_color=self.theme[\"card\"],
                        color=self.theme[\"text\"],
                        halign='left')
            btn.bind(on_press=lambda x, m=msg: self._use_history(m))
            msg_list.add_widget(btn)
        
        scroll.add_widget(msg_list)
        content.add_widget(scroll)
        
        popup = Popup(title=f\"历史记录 (共{len(self.history)}条)\", content=content,
                     size_hint=(0.9, 0.7))
        popup.open()
    
    def _use_history(self, msg):
        \"\"\"使用历史消息\"\"\"
        current = self.msg_input.text.strip()
        if current:
            self.msg_input.text = current + '\\n' + msg
        else:
            self.msg_input.text = msg
    
    def _log(self, text):
        \"\"\"添加日志\"\"\"
        timestamp = datetime.now().strftime(\"%H:%M:%S\")
        self.log_area.text += f\"[{timestamp}] {text}\\n\"
        # 滚动到底部
        self.log_area.cursor = (0, len(self.log_area.text))
    
    def start_sending(self, *args):
        \"\"\"开始发送\"\"\"
        if self.is_running:
            return
        
        # 获取消息列表
        raw = self.msg_input.text.strip()
        if not raw:
            android_toast(\"请输入消息内容\")
            return
        
        messages = [line.strip() for line in raw.split('\\n') if line.strip()]
        if not messages:
            android_toast(\"消息内容不能为空\")
            return
        
        # 保存到历史
        self._save_history(messages)
        
        # 重置状态
        self.is_running = True
        self.is_paused = False
        self.sent_count = 0
        self.last_sent = \"\"
        self.stop_event.clear()
        self.pause_event.set()
        
        self.start_btn.disabled = True
        self.pause_btn.disabled = False
        self.stop_btn.disabled = False
        self.status_label.text = \"🟢 运行中..\"
        self.timer_label.text = \"\"
        
        # 自动打开微信
        if self.auto_wechat.active:
            if open_wechat():
                self._log(\"✅ 已自动打开微信\")
                time.sleep(1)  # 等待微信启动
            else:
                self._log(\"⚠️ 无法自动打开微信\")
        
        self._log(f\"🚀 开始 · {len(messages)} 条 · 间隔 {self.speed_slider.value:.1f}s\")
        android_vibrate(200)
        
        # 启动发送线程
        self.send_thread = threading.Thread(target=self._send_loop,
                                             args=(messages,), daemon=True)
        self.send_thread.start()
        
        # 定时器
        try:
            timer_sec = int(self.timer_input.text)
        except ValueError:
            timer_sec = 0
        if timer_sec > 0:
            self._timer_remaining = timer_sec
            Clock.schedule_once(self._timer_tick, 1)
    
    def _timer_tick(self, dt):
        if not self.is_running:
            self.timer_label.text = \"\"
            return
        if self._timer_remaining > 0:
            m, s = divmod(self._timer_remaining, 60)
            self.timer_label.text = f\"⏱ 剩余: {m:02d}:{s:02d}\"
            self._timer_remaining -= 1
            Clock.schedule_once(self._timer_tick, 1)
        else:
            self.timer_label.text = \"\"
            self._log(\"⏱ 定时到达\")
            self.stop_sending()
    
    def _send_loop(self, messages):
        mode = self.mode_spinner.text
        idx = 0
        try:
            batch_limit = int(self.batch_input.text)
        except ValueError:
            batch_limit = 0
        
        while not self.stop_event.is_set():
            self.pause_event.wait()
            if self.stop_event.is_set():
                break
            
            # 选择消息
            if mode == \"随机\":
                msg = random.choice(messages)
                if self.dedup_switch.active and len(messages) > 1:
                    tries = 0
                    while msg == self.last_sent and tries < 10:
                        msg = random.choice(messages)
                        tries += 1
            elif mode == \"单条\":
                msg = messages[0]
            else:
                msg = messages[idx % len(messages)]
                idx += 1
            
            self.last_sent = msg
            
            try:
                # 复制到剪贴板
                android_copy(msg)
                time.sleep(0.05)
                
                self.sent_count += 1
                display = msg if len(msg) <= 15 else msg[:15] + \"...\"
                Clock.schedule_once(lambda dt, c=self.sent_count, m=display:
                                    self._on_sent(c, m), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt, err=str(e):
                                    self._log(f\"❌ 出错: {err}\"), 0)
                break
            
            # 批量检查
            if batch_limit > 0 and self.sent_count >= batch_limit:
                Clock.schedule_once(lambda dt: self._log(f\"🎯 达到 {batch_limit} 条上限\"), 0)
                Clock.schedule_once(lambda dt: self.stop_sending(), 0)
                break
            
            # 间隔
            self.stop_event.wait(self.speed_slider.value)
        
        Clock.schedule_once(lambda dt: self._on_send_end(), 0)
    
    def _on_sent(self, count, msg):
        self.count_label.text = f\"已发送: {count} 条\"
        self._log(f\"📤 #{count} {msg}\")
    
    def _on_send_end(self):
        self.is_running = False
        self.is_paused = False
        self.start_btn.disabled = False
        self.pause_btn.disabled = True
        self.pause_btn.text = \"⏸ 暂停\"
        self.stop_btn.disabled = True
        self.status_label.text = \"⏸ 已停止\"
        self.count_label.text = f\"共发送 {self.sent_count} 条消息\"
        self._log(f\"✅ 结束，共 {self.sent_count} 条\")
        android_toast(f\"刷屏结束，共 {self.sent_count} 条\")
        android_vibrate(500)
    
    def toggle_pause(self, *args):
        if not self.is_running:
            return
        if self.is_paused:
            self.is_paused = False
            self.pause_event.set()
            self.pause_btn.text = \"⏸ 暂停\"
            self.status_label.text = \"🟢 运行中..\"
            self._log(\"▶ 已恢复\")
        else:
            self.is_paused = True
            self.pause_event.clear()
            self.pause_btn.text = \"▶ 恢复\"
            self.status_label.text = \"🟡 已暂停\"
            self._log(\"⏸ 已暂停\")
    
    def stop_sending(self, *args):
        if not self.is_running:
            return
        self.stop_event.set()
        self.pause_event.set()
        self.timer_label.text = \"\"
        self._log(\"⏹ 正在停止...\")
        android_vibrate(100)


if __name__ == '__main__':
    WeChatFloodApp().run()
