package com.wechat.flood;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.content.ClipboardManager;
import android.content.ClipData;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

import java.util.ArrayList;
import java.util.List;

public class AutoSendService extends AccessibilityService {
    private static final String TAG = "AutoSend";
    private static AutoSendService instance;
    private static String pendingMessage = null;
    private static boolean autoMode = false;
    private static int sendCount = 0;
    private static int maxCount = 0;
    private static long delayMs = 500;
    private static String targetPackage = null;
    
    public static AutoSendService getInstance() {
        return instance;
    }
    
    @Override
    public void onServiceConnected() {
        super.onServiceConnected();
        instance = this;
        
        AccessibilityServiceInfo info = getServiceInfo();
        if (info == null) {
            info = new AccessibilityServiceInfo();
        }
        info.eventTypes = AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED | 
                          AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED;
        info.feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC;
        info.notificationTimeout = 100;
        info.flags = AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS |
                     AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS |
                     AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS;
        
        setServiceInfo(info);
        Log.d(TAG, "自动发送服务已连接");
    }
    
    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event == null || pendingMessage == null) return;
        
        if (autoMode && targetPackage != null) {
            String pkg = event.getPackageName() != null ? event.getPackageName().toString() : "";
            if (pkg.equals(targetPackage)) {
                handleAutoSend();
            }
        }
    }
    
    @Override
    public void onInterrupt() {
        Log.d(TAG, "服务被中断");
    }
    
    @Override
    public void onDestroy() {
        super.onDestroy();
        instance = null;
    }
    
    // 检查服务是否可用
    public boolean isServiceReady() {
        return instance != null;
    }
    
    // 发送消息到指定应用
    public boolean sendMessage(String message, String packageName, int count, long delay) {
        pendingMessage = message;
        targetPackage = packageName;
        maxCount = count;
        delayMs = delay;
        sendCount = 0;
        autoMode = true;
        
        // 打开目标应用
        try {
            Intent intent = getPackageManager().getLaunchIntentForPackage(packageName);
            if (intent != null) {
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                startActivity(intent);
                return true;
            }
        } catch (Exception e) {
            Log.e(TAG, "无法打开应用: " + e.getMessage());
        }
        return false;
    }
    
    // 停止发送
    public void stopSending() {
        pendingMessage = null;
        autoMode = false;
        targetPackage = null;
        maxCount = 0;
        sendCount = 0;
    }
    
    // 获取状态
    public boolean isRunning() {
        return autoMode;
    }
    
    public int getSendCount() {
        return sendCount;
    }
    
    private void handleAutoSend() {
        if (!autoMode || pendingMessage == null) return;
        
        AccessibilityNodeInfo rootNode = getRootInActiveWindow();
        if (rootNode == null) return;
        
        // 查找输入框
        AccessibilityNodeInfo inputBox = findEditableNode(rootNode);
        if (inputBox == null) {
            rootNode.recycle();
            return;
        }
        
        // 输入文本
        if (inputText(inputBox, pendingMessage)) {
            // 延迟后点击发送
            new Handler().postDelayed(() -> {
                if (clickSend(rootNode)) {
                    sendCount++;
                    Log.d(TAG, "已发送第 " + sendCount + " 条");
                    
                    if (maxCount > 0 && sendCount >= maxCount) {
                        stopSending();
                    }
                }
            }, 300);
        }
        
        rootNode.recycle();
    }
    
    // 查找可编辑的输入框
    private AccessibilityNodeInfo findEditableNode(AccessibilityNodeInfo node) {
        if (node == null) return null;
        
        if (node.isEditable() && node.isVisibleToUser()) {
            return node;
        }
        
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            if (child != null) {
                AccessibilityNodeInfo result = findEditableNode(child);
                if (result != null) {
                    return result;
                }
            }
        }
        return null;
    }
    
    // 输入文本
    private boolean inputText(AccessibilityNodeInfo node, String text) {
        if (node == null) return false;
        
        // 复制到剪贴板
        ClipboardManager clipboard = (ClipboardManager) getSystemService(CLIPBOARD_SERVICE);
        ClipData clip = ClipData.newPlainText("msg", text);
        clipboard.setPrimaryClip(clip);
        
        // 设置文本
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            Bundle args = new Bundle();
            args.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text);
            if (node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args)) {
                return true;
            }
        }
        
        // 备用：粘贴
        node.performAction(AccessibilityNodeInfo.ACTION_FOCUS);
        return node.performAction(AccessibilityNodeInfo.ACTION_PASTE);
    }
    
    // 点击发送按钮
    private boolean clickSend(AccessibilityNodeInfo rootNode) {
        if (rootNode == null) return false;
        
        // 查找"发送"按钮
        List<AccessibilityNodeInfo> nodes = rootNode.findAccessibilityNodeInfosByText("发送");
        if (nodes != null) {
            for (AccessibilityNodeInfo n : nodes) {
                if (n.isClickable() && n.isVisibleToUser()) {
                    n.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                    return true;
                }
            }
        }
        
        // 查找"Send"按钮
        nodes = rootNode.findAccessibilityNodeInfosByText("Send");
        if (nodes != null) {
            for (AccessibilityNodeInfo n : nodes) {
                if (n.isClickable() && n.isVisibleToUser()) {
                    n.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                    return true;
                }
            }
        }
        
        return false;
    }
}
