# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
import threading
import time
import random

class MsgApp(App):
    def build(self):
        self.title = "消息助手 v3.0"
        self.is_running = False
        self.is_paused = False
        self.sent_count = 0
        self.current_idx = 0
        
        root = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # 标题
        title = Label(
            text="[b]消息助手 v3.0[/b]",
            markup=True,
            font_size=24,
            size_hint_y=None,
            height=40,
            color=(0.07, 0.75, 0.38, 1)
        )
        root.add_widget(title)
        
        # 消息输入
        self.msg_input = TextInput(
            hint_text="输入消息，每行一条\n示例：\n你好\n在吗\n哈哈哈",
            multiline=True,
            size_hint_y=0.35,
            font_size=16,
            padding=[10, 10]
        )
        root.add_widget(self.msg_input)
        
        # 预设按钮行
        preset_layout = GridLayout(cols=3, size_hint_y=None, height=40, spacing=5)
        for name, msgs in [
            ("表情", ["😀","😂","🤣","😍","🥰","😎","🤩","😘","😋","🤔","👍","❤️","🔥","✨","🎉","💪"]),
            ("数字", [str(i) for i in range(1, 21)]),
            ("测试", ["测试消息1","测试消息2","测试消息3","测试消息4","测试消息5"])
        ]:
            btn = Button(text=name, font_size=14, background_color=(0.07, 0.75, 0.38, 1))
            btn.bind(on_press=lambda x, m=msgs: self.load_preset(m))
            preset_layout.add_widget(btn)
        root.add_widget(preset_layout)
        
        # 设置行
        settings = BoxLayout(size_hint_y=None, height=45, spacing=10)
        
        settings.add_widget(Label(text="模式:", font_size=14, size_hint_x=0.15))
        self.mode_spinner = Spinner(
            text='顺序',
            values=('顺序', '随机', '单条'),
            size_hint_x=0.25
        )
        settings.add_widget(self.mode_spinner)
        
        settings.add_widget(Label(text="间隔:", font_size=14, size_hint_x=0.12))
        self.speed_slider = Slider(min=0.1, max=5.0, value=1.0, step=0.1, size_hint_x=0.3)
        settings.add_widget(self.speed_slider)
        self.speed_label = Label(text="1.0s", font_size=12, size_hint_x=0.13)
        settings.add_widget(self.speed_label)
        
        root.add_widget(settings)
        
        # 控制按钮
        btn_layout = GridLayout(cols=3, size_hint_y=None, height=55, spacing=8)
        
        self.start_btn = Button(
            text="▶ 开始",
            font_size=18,
            background_color=(0.07, 0.75, 0.38, 1),
            color=(1, 1, 1, 1)
        )
        self.start_btn.bind(on_press=self.start_sending)
        
        self.pause_btn = Button(
            text="⏸ 暂停",
            font_size=18,
            background_color=(0.95, 0.61, 0.07, 1),
            disabled=True
        )
        self.pause_btn.bind(on_press=self.toggle_pause)
        
        self.stop_btn = Button(
            text="⏹ 停止",
            font_size=18,
            background_color=(0.91, 0.30, 0.24, 1),
            disabled=True
        )
        self.stop_btn.bind(on_press=self.stop_sending)
        
        btn_layout.add_widget(self.start_btn)
        btn_layout.add_widget(self.pause_btn)
        btn_layout.add_widget(self.stop_btn)
        root.add_widget(btn_layout)
        
        # 状态栏
        status_layout = BoxLayout(size_hint_y=None, height=30)
        self.status_label = Label(text="就绪", font_size=14, color=(0.5, 0.5, 0.5, 1))
        self.count_label = Label(text="0", font_size=18, bold=True, color=(0.07, 0.75, 0.38, 1))
        status_layout.add_widget(self.status_label)
        status_layout.add_widget(self.count_label)
        root.add_widget(status_layout)
        
        # 日志区域
        log_label = Label(text="运行日志", font_size=14, size_hint_y=None, height=25, halign='left')
        root.add_widget(log_label)
        
        self.log_area = TextInput(
            readonly=True,
            background_color=(0.12, 0.12, 0.18, 1),
            foreground_color=(0.65, 0.89, 0.63, 1),
            font_size=12,
            size_hint_y=0.25
        )
        root.add_widget(self.log_area)
        
        return root
    
    def load_preset(self, msgs):
        self.msg_input.text = "\n".join(msgs)
        self.log(f"已加载 {len(msgs)} 条预设消息")
    
    def log(self, msg):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_area.text += f"[{ts}] {msg}\n"
    
    def start_sending(self, *args):
        if self.is_running:
            return
        
        raw = self.msg_input.text.strip()
        if not raw:
            self.status_label.text = "请输入消息"
            return
        
        self.messages = [m.strip() for m in raw.split("\n") if m.strip()]
        if not self.messages:
            self.status_label.text = "消息不能为空"
            return
        
        self.is_running = True
        self.is_paused = False
        self.sent_count = 0
        self.current_idx = 0
        
        self.start_btn.disabled = True
        self.pause_btn.disabled = False
        self.stop_btn.disabled = False
        self.status_label.text = "运行中..."
        
        self.log(f"开始发送 {len(self.messages)} 条消息")
        
        # 启动发送线程
        self.send_thread = threading.Thread(target=self._send_loop, daemon=True)
        self.send_thread.start()
    
    def _send_loop(self):
        mode = self.mode_spinner.text
        interval = self.speed_slider.value
        
        while self.is_running:
            if self.is_paused:
                time.sleep(0.1)
                continue
            
            # 选择消息
            if mode == "随机":
                msg = random.choice(self.messages)
            elif mode == "单条":
                msg = self.messages[0]
            else:
                msg = self.messages[self.current_idx % len(self.messages)]
                self.current_idx += 1
            
            try:
                # 复制到剪贴板
                from kivy.core.clipboard import Clipboard
                Clipboard.copy(msg)
                self.sent_count += 1
                
                display = msg if len(msg) <= 15 else msg[:15] + "..."
                Clock.schedule_once(lambda dt, m=display: self.log(f"已复制 #{self.sent_count}: {m}"))
                Clock.schedule_once(lambda dt: setattr(self.count_label, 'text', str(self.sent_count)), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt, err=str(e): self.log(f"错误: {err}"))
                break
            
            # 间隔等待
            time.sleep(interval)
        
        Clock.schedule_once(lambda dt: self._on_send_end())
    
    def _on_send_end(self):
        self.is_running = False
        self.is_paused = False
        self.start_btn.disabled = False
        self.pause_btn.disabled = True
        self.pause_btn.text = "⏸ 暂停"
        self.stop_btn.disabled = True
        self.status_label.text = "已停止"
        self.log(f"发送完成，共 {self.sent_count} 条")
    
    def toggle_pause(self, *args):
        if not self.is_running:
            return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_btn.text = "▶ 继续"
            self.status_label.text = "已暂停"
            self.log("已暂停")
        else:
            self.pause_btn.text = "⏸ 暂停"
            self.status_label.text = "运行中..."
            self.log("已继续")
    
    def stop_sending(self, *args):
        if not self.is_running:
            return
        self.is_running = False
        self.is_paused = False
        self.log("正在停止...")

if __name__ == "__main__":
    MsgApp().run()
