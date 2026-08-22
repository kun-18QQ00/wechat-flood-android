"""
微信刷屏助手 Android 版 v2.0
基于 Kivy 框架，支持安卓打包为 APK
"""

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

# 安卓平台适配
if platform == 'android':
    from android.runnable import run_on_ui_thread
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    ClipData = autoclass('android.content.ClipData')
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')

    @run_on_ui_thread
    def android_copy(text):
        """安卓复制到剪贴板"""
        activity = PythonActivity.mActivity
        clipboard = activity.getSystemService(Context.CLIPBOARD_SERVICE)
        clip = ClipData.newPlainText("msg", text)
        clipboard.setPrimaryClip(clip)

    def android_toast(msg):
        """安卓 Toast 提示"""
        try:
            from jnius import autoclass
            Toast = autoclass('android.widget.Toast')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity

            @run_on_ui_thread
            def show():
                Toast.makeText(activity, msg, Toast.LENGTH_SHORT).show()
            show()
        except Exception:
            pass

    def android_share_to_wechat(text):
        """通过分享功能发送到微信"""
        try:
            activity = PythonActivity.mActivity
            intent = Intent(Intent.ACTION_SEND)
            intent.setType("text/plain")
            intent.putExtra(Intent.EXTRA_TEXT, text)
            activity.startActivity(intent)
        except Exception:
            pass
else:
    def android_copy(text):
        """桌面端复制（备用）"""
        try:
            import pyperclip
            pyperclip.copy(text)
        except Exception:
            pass

    def android_toast(msg):
        print(f"[Toast] {msg}")

    def android_share_to_wechat(text):
        print(f"[Share] {text}")


# ═══════════════════════════════════════════
#  颜色主题
# ═══════════════════════════════════════════
THEME = {
    "bg":         (0.96, 0.97, 0.98, 1),
    "card":       (1, 1, 1, 1),
    "accent":     (0.18, 0.80, 0.44, 1),
    "accent_dk":  (0.15, 0.68, 0.38, 1),
    "warning":    (0.95, 0.61, 0.07, 1),
    "danger":     (0.91, 0.30, 0.24, 1),
    "info":       (0.20, 0.60, 0.86, 1),
    "text":       (0.17, 0.24, 0.31, 1),
    "text_sub":   (0.50, 0.55, 0.55, 1),
    "log_bg":     (0.12, 0.12, 0.18, 1),
    "log_text":   (0.65, 0.89, 0.63, 1),
    "white":      (1, 1, 1, 1),
    "input_bg":   (0.98, 0.98, 0.98, 1),
}

PRESETS_FILE = "message_presets.json"


class CardBox(BoxLayout):
    """卡片容器组件"""
    def __init__(self, title="", **kwargs):
        super().__init__(orientation='vertical', padding=[12, 10, 12, 10],
                         spacing=6, size_hint_y=None, **kwargs)
        self.bind(minimum_height=self.setter('height'))
        self.canvas.before.clear()
        with self.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(*THEME["card"])
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self._update_bg, size=self._update_bg)

        if title:
            lbl = Label(text=title, font_size='16sp', bold=True,
                        color=THEME["text"], size_hint_y=None, height='30dp',
                        halign='left', valign='middle')
            lbl.bind(size=lbl.setter('text_size'))
            self.add_widget(lbl)

    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size


class WeChatFloodApp(App):
    def build(self):
        Window.clearcolor = THEME["bg"]
        self.title = "微信刷屏助手 v2.0"

        # 状态变量
        self.is_running = False
        self.is_paused = False
        self.sent_count = 0
        self.last_sent = ""
        self.send_thread = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.presets = self._load_presets()

        # 主滚动布局
        root = BoxLayout(orientation='vertical')
        scroll = ScrollView(size_hint=(1, 1))
        self.main = BoxLayout(orientation='vertical', padding=10, spacing=8,
                              size_hint_y=None)
        self.main.bind(minimum_height=self.main.setter('height'))

        # 构建 UI
        self._build_header()
        self._build_status()
        self._build_content_tab()
        self._build_speed()
        self._build_mode()
        self._build_timer()
        self._build_buttons()
        self._build_log()

        scroll.add_widget(self.main)
        root.add_widget(scroll)
        return root

    # ───────────────────────────────────
    #  UI 构建
    # ───────────────────────────────────
    def _build_header(self):
        card = CardBox()
        title = Label(text="[b]💬 微信刷屏助手 v2.0[/b]", markup=True,
                      font_size='20sp', color=THEME["white"],
                      size_hint_y=None, height='45dp')
        with card.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(*THEME["accent"])
            self._header_bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[10])
        card.bind(pos=self._update_header_bg, size=self._update_header_bg)
        card.add_widget(title)
        self.main.add_widget(card)

    def _update_header_bg(self, *args):
        self._header_bg.pos = self.main.children[-1].pos
        self._header_bg.size = self.main.children[-1].size

    def _build_status(self):
        card = CardBox(title="📊 运行状态")
        self.status_label = Label(text="⏸ 就绪 - 等待开始", font_size='16sp',
                                   bold=True, color=THEME["text"],
                                   size_hint_y=None, height='30dp',
                                   halign='left', valign='middle')
        self.status_label.bind(size=self.status_label.setter('text_size'))
        self.count_label = Label(text="已发送：0 条", font_size='14sp',
                                  color=THEME["info"], size_hint_y=None, height='25dp',
                                  halign='left', valign='middle')
        self.count_label.bind(size=self.count_label.setter('text_size'))
        self.timer_label = Label(text="", font_size='13sp',
                                  color=THEME["warning"], size_hint_y=None, height='25dp',
                                  halign='left', valign='middle')
        self.timer_label.bind(size=self.timer_label.setter('text_size'))

        card.add_widget(self.status_label)
        card.add_widget(self.count_label)
        card.add_widget(self.timer_label)
        self.main.add_widget(card)

    def _build_content_tab(self):
        card = CardBox(title="📝 刷屏内容")

        # 预设管理
        preset_row = BoxLayout(size_hint_y=None, height='40dp', spacing=5)
        self.preset_spinner = Spinner(text='选择预设', values=list(self.presets.keys()),
                                       size_hint_x=0.5, font_size='13sp')
        btn_load = Button(text='加载', size_hint_x=0.17, font_size='13sp',
                          background_color=THEME["info"])
        btn_load.bind(on_press=self._load_preset)
        btn_save = Button(text='保存', size_hint_x=0.17, font_size='13sp',
                          background_color=THEME["accent"])
        btn_save.bind(on_press=self._save_preset)
        btn_del = Button(text='删除', size_hint_x=0.16, font_size='13sp',
                          background_color=THEME["danger"])
        btn_del.bind(on_press=self._delete_preset)
        preset_row.add_widget(self.preset_spinner)
        preset_row.add_widget(btn_load)
        preset_row.add_widget(btn_save)
        preset_row.add_widget(btn_del)
        card.add_widget(preset_row)

        # 消息输入
        self.content_input = TextInput(
            text="你好呀！\n哈哈哈\n测试刷屏",
            font_size='15sp', size_hint_y=None, height='150dp',
            multiline=True, hint_text='每行一条消息...',
            background_color=THEME["input_bg"],
            foreground_color=THEME["text"]
        )
        card.add_widget(self.content_input)

        # 字符统计
        self.char_label = Label(text="共 3 行", font_size='12sp',
                                 color=THEME["text_sub"], size_hint_y=None, height='25dp',
                                 halign='left', valign='middle')
        self.char_label.bind(size=self.char_label.setter('text_size'))
        self.content_input.bind(text=self._update_char_count)
        card.add_widget(self.char_label)

        # 导入按钮
        btn_import = Button(text='📥 从文件导入消息', size_hint_y=None, height='38dp',
                             font_size='14sp', background_color=THEME["info"])
        btn_import.bind(on_press=self._import_file)
        card.add_widget(btn_import)

        self.main.add_widget(card)

    def _build_speed(self):
        card = CardBox(title="⚡ 发送速度")

        row = BoxLayout(size_hint_y=None, height='45dp', spacing=8)
        row.add_widget(Label(text="间隔", font_size='14sp', color=THEME["text_sub"],
                              size_hint_x=0.15))
        self.speed_slider = Slider(min=0.1, max=5.0, value=0.5, step=0.1,
                                    size_hint_x=0.55)
        self.speed_slider.bind(value=self._on_speed_change)
        row.add_widget(self.speed_slider)
        self.speed_label = Label(text="0.5 秒", font_size='15sp', bold=True,
                                  color=THEME["accent"], size_hint_x=0.3)
        row.add_widget(self.speed_label)
        card.add_widget(row)

        # 预设按钮
        presets_row = GridLayout(cols=5, size_hint_y=None, height='36dp', spacing=4)
        for label, val in [("极快", 0.1), ("快速", 0.3), ("中等", 0.5), ("慢速", 1.0), ("很慢", 2.0)]:
            btn = Button(text=label, font_size='12sp',
                         background_color=THEME["accent"])
            btn.bind(on_press=lambda inst, v=val: setattr(self.speed_slider, 'value', v))
            presets_row.add_widget(btn)
        card.add_widget(presets_row)
        self.main.add_widget(card)

    def _build_mode(self):
        card = CardBox(title="🔄 发送模式")

        self.mode = 'sequential'
        mode_row = BoxLayout(size_hint_y=None, height='40dp', spacing=5)
        self.mode_buttons = {}
        for text, val in [("顺序循环", "sequential"), ("随机发送", "random"), ("单条重复", "single")]:
            btn = Button(text=text, font_size='13sp',
                         background_color=THEME["accent_dk"] if val == 'sequential' else THEME["text_sub"])
            btn.bind(on_press=lambda inst, v=val: self._set_mode(v))
            self.mode_buttons[val] = btn
            mode_row.add_widget(btn)
        card.add_widget(mode_row)

        # 防重复开关
        opt_row = BoxLayout(size_hint_y=None, height='36dp', spacing=10)
        opt_row.add_widget(Label(text="防重复", font_size='14sp', color=THEME["text_sub"]))
        self.dedup_switch = Switch(active=False, size_hint_x=0.3)
        opt_row.add_widget(self.dedup_switch)
        opt_row.add_widget(Label(text="窗口置顶", font_size='14sp', color=THEME["text_sub"]))
        self.topmost_switch = Switch(active=True, size_hint_x=0.3)
        opt_row.add_widget(self.topmost_switch)
        card.add_widget(opt_row)
        self.main.add_widget(card)

    def _set_mode(self, mode):
        self.mode = mode
        for k, btn in self.mode_buttons.items():
            btn.background_color = THEME["accent_dk"] if k == mode else THEME["text_sub"]

    def _build_timer(self):
        card = CardBox(title="⏱ 停止条件")

        row1 = BoxLayout(size_hint_y=None, height='36dp', spacing=5)
        row1.add_widget(Label(text="定时(秒，0=不限)", font_size='13sp',
                               color=THEME["text_sub"], size_hint_x=0.6))
        self.timer_input = TextInput(text="0", font_size='15sp', input_filter='int',
                                      size_hint_x=0.4, multiline=False,
                                      background_color=THEME["input_bg"])
        row1.add_widget(self.timer_input)
        card.add_widget(row1)

        row2 = BoxLayout(size_hint_y=None, height='36dp', spacing=5)
        row2.add_widget(Label(text="批量(条，0=不限)", font_size='13sp',
                               color=THEME["text_sub"], size_hint_x=0.6))
        self.batch_input = TextInput(text="0", font_size='15sp', input_filter='int',
                                      size_hint_x=0.4, multiline=False,
                                      background_color=THEME["input_bg"])
        row2.add_widget(self.batch_input)
        card.add_widget(row2)

        # 倒计时设置
        cd_row = BoxLayout(size_hint_y=None, height='36dp', spacing=5)
        cd_row.add_widget(Label(text="启动倒计时", font_size='13sp',
                                 color=THEME["text_sub"], size_hint_x=0.4))
        self.cd_spinner = Spinner(text='3秒', values=['0秒', '3秒', '5秒', '10秒'],
                                   size_hint_x=0.6, font_size='13sp')
        cd_row.add_widget(self.cd_spinner)
        card.add_widget(cd_row)

        self.main.add_widget(card)

    def _build_buttons(self):
        row = BoxLayout(size_hint_y=None, height='50dp', spacing=6)

        self.start_btn = Button(text='▶ 开始刷屏', font_size='16sp', bold=True,
                                 background_color=THEME["accent"])
        self.start_btn.bind(on_press=self.start_sending)

        self.pause_btn = Button(text='⏸ 暂停', font_size='15sp',
                                 background_color=THEME["warning"], disabled=True)
        self.pause_btn.bind(on_press=self.toggle_pause)

        self.stop_btn = Button(text='⏹ 停止', font_size='15sp',
                                background_color=THEME["danger"], disabled=True)
        self.stop_btn.bind(on_press=self.stop_sending)

        row.add_widget(self.start_btn)
        row.add_widget(self.pause_btn)
        row.add_widget(self.stop_btn)
        self.main.add_widget(row)

    def _build_log(self):
        card = CardBox(title="📋 发送日志")

        # 操作按钮
        btn_row = BoxLayout(size_hint_y=None, height='32dp', spacing=5)
        btn_clear = Button(text='清空', font_size='12sp', size_hint_x=0.5,
                            background_color=THEME["text_sub"])
        btn_clear.bind(on_press=self._clear_log)
        btn_export = Button(text='导出', font_size='12sp', size_hint_x=0.5,
                             background_color=THEME["info"])
        btn_export.bind(on_press=self._export_log)
        btn_row.add_widget(btn_clear)
        btn_row.add_widget(btn_export)
        card.add_widget(btn_row)

        self.log_input = TextInput(text="", font_size='12sp', readonly=True,
                                    size_hint_y=None, height='150dp',
                                    background_color=THEME["log_bg"],
                                    foreground_color=THEME["log_text"])
        card.add_widget(self.log_input)
        self.main.add_widget(card)

    # ───────────────────────────────────
    #  辅助方法
    # ───────────────────────────────────
    def _on_speed_change(self, instance, value):
        self.speed_label.text = f"{value:.1f} 秒"

    def _update_char_count(self, instance, text):
        lines = [l for l in text.strip().split('\n') if l.strip()]
        self.char_label.text = f"共 {len(lines)} 行 · {len(text.strip())} 字符"

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_input.text += f"[{ts}] {msg}\n"
        # 自动滚动到底部
        self.log_input.cursor = (0, len(self.log_input.text))

    def _clear_log(self, *args):
        self.log_input.text = ""

    def _export_log(self, *args):
        if not self.log_input.text.strip():
            android_toast("日志为空")
            return
        try:
            filename = f"刷屏日志_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join(os.path.expanduser("~"), filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self.log_input.text)
            android_toast(f"已保存到 {filepath}")
        except Exception as e:
            android_toast(f"导出失败: {e}")

    # ───────────────────────────────────
    #  预设管理
    # ───────────────────────────────────
    def _load_presets(self):
        try:
            if os.path.exists(PRESETS_FILE):
                with open(PRESETS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_presets_file(self):
        try:
            with open(PRESETS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.presets, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _refresh_presets(self):
        self.preset_spinner.values = list(self.presets.keys())

    def _save_preset(self, *args):
        content = self.content_input.text.strip()
        if not content:
            android_toast("内容为空")
            return
        # 弹窗输入名称
        popup_content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        name_input = TextInput(hint_text='输入预设名称', font_size='15sp',
                                size_hint_y=None, height='45dp', multiline=False)
        popup_content.add_widget(name_input)

        btn_row = BoxLayout(size_hint_y=None, height='40dp', spacing=10)
        popup = None

        def on_ok(*args):
            name = name_input.text.strip()
            if name:
                self.presets[name] = content
                self._save_presets_file()
                self._refresh_presets()
                self._log(f"✅ 预设「{name}」已保存")
                popup.dismiss()

        def on_cancel(*args):
            popup.dismiss()

        btn_ok = Button(text='保存', background_color=THEME["accent"])
        btn_ok.bind(on_press=on_ok)
        btn_cancel = Button(text='取消', background_color=THEME["text_sub"])
        btn_cancel.bind(on_press=on_cancel)
        btn_row.add_widget(btn_ok)
        btn_row.add_widget(btn_cancel)
        popup_content.add_widget(btn_row)

        popup = Popup(title='保存预设', content=popup_content,
                      size_hint=(0.85, 0.4))
        popup.open()

    def _load_preset(self, *args):
        name = self.preset_spinner.text
        if name in self.presets:
            self.content_input.text = self.presets[name]
            self._log(f"📂 已加载「{name}」")
        else:
            android_toast("请先选择一个预设")

    def _delete_preset(self, *args):
        name = self.preset_spinner.text
        if name in self.presets:
            del self.presets[name]
            self._save_presets_file()
            self._refresh_presets()
            self._log(f"🗑 已删除「{name}」")

    def _import_file(self, *args):
        """从文件导入"""
        try:
            from kivy.uix.filechooser import FileChooserListView
            content = BoxLayout(orientation='vertical')
            chooser = FileChooserListView(path=os.path.expanduser("~"),
                                           filters=['*.txt'])
            content.add_widget(chooser)

            btn_row = BoxLayout(size_hint_y=None, height='40dp', spacing=10)
            popup = None

            def on_select(*args):
                if chooser.selection:
                    try:
                        with open(chooser.selection[0], "r", encoding="utf-8") as f:
                            self.content_input.text = f.read().strip()
                        lines = len([l for l in self.content_input.text.split('\n') if l.strip()])
                        self._log(f"📥 已导入 {lines} 条消息")
                    except Exception as e:
                        android_toast(f"读取失败: {e}")
                popup.dismiss()

            def on_cancel(*args):
                popup.dismiss()

            btn_ok = Button(text='导入', background_color=THEME["accent"])
            btn_ok.bind(on_press=on_select)
            btn_cancel = Button(text='取消', background_color=THEME["text_sub"])
            btn_cancel.bind(on_press=on_cancel)
            btn_row.add_widget(btn_ok)
            btn_row.add_widget(btn_cancel)
            content.add_widget(btn_row)

            popup = Popup(title='选择文件', content=content,
                          size_hint=(0.9, 0.7))
            popup.open()
        except Exception as e:
            android_toast(f"文件选择失败: {e}")

    # ───────────────────────────────────
    #  核心逻辑
    # ───────────────────────────────────
    def _get_messages(self):
        text = self.content_input.text.strip()
        if not text:
            return []
        return [l.strip() for l in text.split('\n') if l.strip()]

    def start_sending(self, *args):
        if self.is_running:
            return
        messages = self._get_messages()
        if not messages:
            android_toast("请至少输入一条消息！")
            return

        cd_text = self.cd_spinner.text.replace('秒', '')
        try:
            cd = int(cd_text)
        except ValueError:
            cd = 3

        if cd > 0:
            self._start_countdown(cd, messages)
        else:
            self._do_start(messages)

    def _start_countdown(self, seconds, messages):
        self.is_running = True
        self.start_btn.disabled = True
        self.stop_btn.disabled = False
        self._log(f"⏳ {seconds} 秒后开始...")
        android_toast(f"{seconds} 秒后开始，请切换到微信")

        def tick(dt):
            nonlocal seconds
            if seconds <= 0:
                self._do_start(messages)
                return
            self.status_label.text = f"⏳ 倒计时 {seconds} 秒..."
            self.timer_label.text = "请切换到微信聊天窗口"
            seconds -= 1
            Clock.schedule_once(tick, 1)

        Clock.schedule_once(tick, 0)

    def _do_start(self, messages):
        self.is_running = True
        self.is_paused = False
        self.sent_count = 0
        self.last_sent = ""
        self.stop_event.clear()
        self.pause_event.set()

        self.start_btn.disabled = True
        self.pause_btn.disabled = False
        self.stop_btn.disabled = False
        self.status_label.text = "🟢 运行中..."
        self.timer_label.text = ""

        self._log(f"🚀 开始 · {len(messages)} 条 · 间隔 {self.speed_slider.value:.1f}s")

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
            self.timer_label.text = ""
            return
        if self._timer_remaining > 0:
            m, s = divmod(self._timer_remaining, 60)
            self.timer_label.text = f"⏰ 剩余：{m:02d}:{s:02d}"
            self._timer_remaining -= 1
            Clock.schedule_once(self._timer_tick, 1)
        else:
            self.timer_label.text = ""
            self._log("⏰ 定时到达")
            self.stop_sending()

    def _send_loop(self, messages):
        mode = self.mode
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
            if mode == "random":
                msg = random.choice(messages)
                if self.dedup_switch.active and len(messages) > 1:
                    tries = 0
                    while msg == self.last_sent and tries < 10:
                        msg = random.choice(messages)
                        tries += 1
            elif mode == "single":
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
                display = msg if len(msg) <= 15 else msg[:15] + "..."
                Clock.schedule_once(lambda dt, c=self.sent_count, m=display:
                                    self._on_sent(c, m), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt, err=str(e):
                                    self._log(f"❌ 出错：{err}"), 0)
                break

            # 批量检查
            if batch_limit > 0 and self.sent_count >= batch_limit:
                Clock.schedule_once(lambda dt: self._log(f"📊 达到 {batch_limit} 条上限"), 0)
                Clock.schedule_once(lambda dt: self.stop_sending(), 0)
                break

            # 间隔
            self.stop_event.wait(self.speed_slider.value)

        Clock.schedule_once(lambda dt: self._on_send_end(), 0)

    def _on_sent(self, count, msg):
        self.count_label.text = f"已发送：{count} 条"
        self._log(f"📨 #{count} {msg}")

    def _on_send_end(self):
        self.is_running = False
        self.is_paused = False
        self.start_btn.disabled = False
        self.pause_btn.disabled = True
        self.pause_btn.text = "⏸ 暂停"
        self.stop_btn.disabled = True
        self.status_label.text = "⏹ 已停止"
        self.count_label.text = f"共发送 {self.sent_count} 条消息"
        self._log(f"✅ 结束，共 {self.sent_count} 条")
        android_toast(f"刷屏结束，共 {self.sent_count} 条")

    def toggle_pause(self, *args):
        if not self.is_running:
            return
        if self.is_paused:
            self.is_paused = False
            self.pause_event.set()
            self.pause_btn.text = "⏸ 暂停"
            self.status_label.text = "🟢 运行中..."
            self._log("▶ 已恢复")
        else:
            self.is_paused = True
            self.pause_event.clear()
            self.pause_btn.text = "▶ 恢复"
            self.status_label.text = "🟡 已暂停"
            self._log("⏸ 已暂停")

    def stop_sending(self, *args):
        if not self.is_running:
            return
        self.stop_event.set()
        self.pause_event.set()
        self.timer_label.text = ""
        self._log("⏹ 正在停止...")


if __name__ == '__main__':
    WeChatFloodApp().run()
