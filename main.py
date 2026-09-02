# -*- coding: utf-8 -*-
"""
消息助手 v6.0 - 多语言混合架构
Python + Kv + Java + HTML/CSS/JS
"""
import os
import json
import threading
import time
import random
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.webview import WebView
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.utils import platform
from kivy.resources import resource_find
from kivy.logger import Logger

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

# ============ WebView桥接类 ============

class WebViewBridge:
    """Python与WebView的通信桥接"""
    def __init__(self, app):
        self.app = app
    
    def handle_action(self, action, data_json):
        """处理来自WebView的动作"""
        try:
            data = json.loads(data_json) if data_json else {}
            Logger.info(f"WebView Action: {action}, Data: {data}")
            
            if action == 'start':
                self._start_sending(data)
            elif action == 'stop':
                self._stop_sending()
            elif action == 'send':
                self._send_message(data.get('message', ''))
            elif action == 'log':
                Logger.info(f"WebView Log: {data.get('message', '')}")
            
            return json.dumps({'status': 'ok'})
        except Exception as e:
            Logger.error(f"WebView Bridge Error: {e}")
            return json.dumps({'status': 'error', 'message': str(e)})
    
    def _start_sending(self, data):
        """开始发送"""
        self.app.messages = data.get('messages', [])
        self.app.selected_app = data.get('app', '微信')
        self.app.selected_mode = data.get('mode', '顺序')
        self.app.interval = data.get('interval', 1.0)
        self.app.batch = data.get('batch', 0)
        
        self.app.is_running = True
        self.app.is_paused = False
        self.app.sent_count = 0
        self.app.current_index = 0
        self.app.start_time = time.time()
        
        # 在新线程中运行
        thread = threading.Thread(target=self.app._send_loop, daemon=True)
        thread.start()
    
    def _stop_sending(self):
        """停止发送"""
        self.app.is_running = False
        self.app.is_paused = False
    
    def _send_message(self, message):
        """发送单条消息"""
        # 复制到剪贴板
        try:
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(message)
            Logger.info(f"已复制到剪贴板: {message[:20]}...")
        except Exception as e:
            Logger.error(f"复制失败: {e}")

# ============ 主应用 ============

class MessageApp(App):
    """消息助手主应用"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "消息助手"
        
        # 状态
        self.is_running = False
        self.is_paused = False
        self.sent_count = 0
        self.current_index = 0
        self.start_time = None
        self.messages = []
        self.selected_app = '微信'
        self.selected_mode = '顺序'
        self.interval = 1.0
        self.batch = 0
        
        # WebView桥接
        self.bridge = WebViewBridge(self)
        
        # WebView引用
        self.webview = None
    
    def build(self):
        # 设置窗口背景色
        Window.clearcolor = (0.949, 0.949, 0.969, 1)  # iOS灰色背景
        
        # 创建主布局
        layout = BoxLayout(orientation='vertical')
        
        # 创建WebView
        self.webview = WebView()
        layout.add_widget(self.webview)
        
        # 加载HTML页面
        self._load_webview()
        
        return layout
    
    def _load_webview(self):
        """加载WebView页面"""
        web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'web')
        html_path = os.path.join(web_dir, 'index.html')
        
        if os.path.exists(html_path):
            # 使用file://协议加载本地HTML
            self.webview.url = f'file://{html_path}'
            Logger.info(f"加载WebView: {html_path}")
        else:
            Logger.error(f"HTML文件不存在: {html_path}")
    
    def _send_loop(self):
        """发送循环"""
        Logger.info("发送循环开始")
        
        while self.is_running:
            if self.is_paused:
                time.sleep(0.1)
                continue
            
            # 检查批量限制
            if self.batch > 0 and self.sent_count >= self.batch:
                break
            
            # 选择消息
            if self.selected_mode == '随机':
                msg = random.choice(self.messages)
            elif self.selected_mode == '单条':
                msg = self.messages[0]
            else:  # 顺序
                msg = self.messages[self.current_index % len(self.messages)]
                self.current_index += 1
            
            # 发送消息
            try:
                from kivy.core.clipboard import Clipboard
                Clipboard.copy(msg)
                
                self.sent_count += 1
                Logger.info(f"已复制 #{self.sent_count}: {msg[:20]}...")
                
                # 更新WebView
                Clock.schedule_once(lambda dt, m=msg: self._update_webview('on_sent', {
                    'count': self.sent_count,
                    'message': m
                }), 0)
                
                # 振动反馈
                self._vibrate()
                
            except Exception as e:
                Logger.error(f"发送失败: {e}")
                Clock.schedule_once(lambda dt, err=str(e): self._update_webview('on_error', {
                    'message': err
                }), 0)
                break
            
            # 等待间隔
            time.sleep(self.interval)
        
        # 发送完成
        Clock.schedule_once(lambda dt: self._on_complete(), 0)
    
    def _update_webview(self, action, data):
        """更新WebView"""
        if self.webview:
            js_code = f"window.updateFromPython('{action}', {json.dumps(data)})"
            self.webview.evaluate_js(js_code)
    
    def _on_complete(self):
        """发送完成回调"""
        self.is_running = False
        self.is_paused = False
        
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        self._update_webview('on_complete', {
            'count': self.sent_count,
            'elapsed': elapsed
        })
        
        Logger.info(f"发送完成: {self.sent_count} 条, 耗时: {elapsed:.1f} 秒")
    
    def _vibrate(self):
        """振动反馈"""
        if ANDROID:
            try:
                from jnius import autoclass
                activity = autoclass('org.kivy.android.PythonActivity').mActivity
                vibrator = activity.getSystemService(activity.VIBRATOR_SERVICE)
                vibrator.vibrate(50)
            except:
                pass
    
    def on_pause(self):
        """应用暂停"""
        return True
    
    def on_resume(self):
        """应用恢复"""
        pass

# ============ 启动应用 ============

if __name__ == '__main__':
    MessageApp().run()
