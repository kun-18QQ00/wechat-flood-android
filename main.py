from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label

class MsgApp(App):
    def build(self):
        self.title = "消息助手"
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        self.input = TextInput(hint_text="输入消息每行一条", multiline=True, size_hint_y=0.4, font_size=16)
        layout.add_widget(self.input)
        self.status = Label(text="就绪", size_hint_y=0.1)
        layout.add_widget(self.status)
        btn = Button(text="复制消息", size_hint_y=0.2, font_size=20)
        btn.bind(on_press=self.copy_msg)
        layout.add_widget(btn)
        return layout
    def copy_msg(self, instance):
        msg = self.input.text.strip()
        if not msg:
            self.status.text = "请输入消息"
            return
        try:
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(msg)
            self.status.text = "已复制"
        except Exception as e:
            self.status.text = str(e)

if __name__ == "__main__":
    MsgApp().run()
