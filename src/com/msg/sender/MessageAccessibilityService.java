package com.msg.sender;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.content.ClipboardManager;
import android.content.ClipData;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

import java.util.List;

/**
 * 消息助手无障碍服务
 * 实现真正的自动发送功能
 */
public class MessageAccessibilityService extends AccessibilityService {
    private static final String TAG = "MsgSender";
    private static MessageAccessibilityService instance;
    private static String pendingMessage = null;
    private static boolean autoMode = false;
    
    // 支持的应用包名
    private static final String[] SUPPORTED_PACKAGES = {
        "com.tencent.mm",           // 微信
        "com.tencent.mobileqq",     // QQ
        "com.alibaba.android.rimet", // 钉钉
        "com.ss.android.lark",      // 飞书
        "org.telegram.messenger",   // Telegram
        "com.whatsapp"              // WhatsApp
    };
    
    public static MessageAccessibilityService getInstance() {
        return instance;
    }
    
    @Override
    public void onServiceConnected() {
        super.onServiceConnected();
        instance = this;
        Log.d(TAG, "无障碍服务已连接");
        
        // 配置服务
        AccessibilityServiceInfo info = new AccessibilityServiceInfo();
        info.eventTypes = AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED |
                         AccessibilityEvent.TYPE_VIEW_CLICKED |
                         AccessibilityEvent.TYPE_VIEW_FOCUSED;
        info.feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC;
        info.notificationTimeout = 100;
        info.flags = AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS |
                    AccessibilityServiceFlag.RETRIEVE_INTERACTIVE_WINDOWS;
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            info.flags |= AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS;
        }
        
        setServiceInfo(info);
    }
    
    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event == null) return;
        
        // 检查是否是目标应用
        CharSequence packageName = event.getPackageName();
        if (packageName == null) return;
        
        String pkg = packageName.toString();
        if (!isSupportedPackage(pkg)) return;
        
        // 如果有待发送消息，尝试发送
        if (pendingMessage != null && !pendingMessage.isEmpty()) {
            trySendMessage(pkg);
        }
    }
    
    @Override
    public void onInterrupt() {
        Log.d(TAG, "无障碍服务被中断");
    }
    
    @Override
    public void onDestroy() {
        super.onDestroy();
        instance = null;
        Log.d(TAG, "无障碍服务已销毁");
    }
    
    /**
     * 检查是否是支持的应用包名
     */
    private boolean isSupportedPackage(String packageName) {
        for (String pkg : SUPPORTED_PACKAGES) {
            if (pkg.equals(packageName)) {
                return true;
            }
        }
        return false;
    }
    
    /**
     * 设置待发送消息
     */
    public static void setPendingMessage(String message) {
        pendingMessage = message;
        autoMode = true;
        Log.d(TAG, "设置待发送消息: " + message);
    }
    
    /**
     * 清除待发送消息
     */
    public static void clearPendingMessage() {
        pendingMessage = null;
        autoMode = false;
    }
    
    /**
     * 尝试发送消息
     */
    private void trySendMessage(String packageName) {
        if (pendingMessage == null || pendingMessage.isEmpty()) return;
        
        AccessibilityNodeInfo rootNode = getRootInActiveWindow();
        if (rootNode == null) return;
        
        try {
            // 查找输入框
            AccessibilityNodeInfo inputNode = findInputNode(rootNode, packageName);
            if (inputNode != null) {
                // 设置文本
                setTextToNode(inputNode, pendingMessage);
                
                // 查找发送按钮并点击
                AccessibilityNodeInfo sendButton = findSendButton(rootNode, packageName);
                if (sendButton != null) {
                    sendButton.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                    Log.d(TAG, "消息已发送: " + pendingMessage);
                    
                    // 清除待发送消息
                    if (!autoMode) {
                        clearPendingMessage();
                    }
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "发送消息失败: " + e.getMessage());
        } finally {
            rootNode.recycle();
        }
    }
    
    /**
     * 查找输入框节点
     */
    private AccessibilityNodeInfo findInputNode(AccessibilityNodeInfo root, String packageName) {
        // 微信输入框ID
        if ("com.tencent.mm".equals(packageName)) {
            return findNodeById(root, "com.tencent.mm:id/chatting_content_et");
        }
        // QQ输入框ID
        else if ("com.tencent.mobileqq".equals(packageName)) {
            return findNodeById(root, "com.tencent.mobileqq:id/input");
        }
        // 钉钉输入框ID
        else if ("com.alibaba.android.rimet".equals(packageName)) {
            return findNodeById(root, "com.alibaba.android.rimet:id/et_chat_input");
        }
        // 飞书输入框ID
        else if ("com.ss.android.lark".equals(packageName)) {
            return findNodeById(root, "com.ss.android.lark:id/et_chat_input");
        }
        // Telegram输入框ID
        else if ("org.telegram.messenger".equals(packageName)) {
            return findNodeById(root, "org.telegram.messenger:id/chat_text_edit");
        }
        // WhatsApp输入框ID
        else if ("com.whatsapp".equals(packageName)) {
            return findNodeById(root, "com.whatsapp:id/entry");
        }
        
        return null;
    }
    
    /**
     * 查找发送按钮
     */
    private AccessibilityNodeInfo findSendButton(AccessibilityNodeInfo root, String packageName) {
        // 微信发送按钮
        if ("com.tencent.mm".equals(packageName)) {
            return findNodeById(root, "com.tencent.mm:id/chatting_send_btn");
        }
        // QQ发送按钮
        else if ("com.tencent.mobileqq".equals(packageName)) {
            return findNodeById(root, "com.tencent.mobileqq:id/fun_btn");
        }
        // 钉钉发送按钮
        else if ("com.alibaba.android.rimet".equals(packageName)) {
            return findNodeById(root, "com.alibaba.android.rimet:id/btn_send");
        }
        // 飞书发送按钮
        else if ("com.ss.android.lark".equals(packageName)) {
            return findNodeById(root, "com.ss.android.lark:id/btn_send");
        }
        // Telegram发送按钮
        else if ("org.telegram.messenger".equals(packageName)) {
            return findNodeById(root, "org.telegram.messenger:id/send_button");
        }
        // WhatsApp发送按钮
        else if ("com.whatsapp".equals(packageName)) {
            return findNodeById(root, "com.whatsapp:id/send");
        }
        
        return null;
    }
    
    /**
     * 根据ID查找节点
     */
    private AccessibilityNodeInfo findNodeById(AccessibilityNodeInfo root, String viewId) {
        List<AccessibilityNodeInfo> nodes = root.findAccessibilityNodeInfosByViewId(viewId);
        if (nodes != null && !nodes.isEmpty()) {
            return nodes.get(0);
        }
        return null;
    }
    
    /**
     * 设置节点文本
     */
    private void setTextToNode(AccessibilityNodeInfo node, String text) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            Bundle arguments = new Bundle();
            arguments.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text);
            node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments);
        } else {
            // 对于旧版本，使用剪贴板方式
            ClipboardManager clipboard = (ClipboardManager) getSystemService(CLIPBOARD_SERVICE);
            ClipData clip = ClipData.newPlainText("message", text);
            clipboard.setPrimaryClip(clip);
            node.performAction(AccessibilityNodeInfo.ACTION_PASTE);
        }
    }
    
    /**
     * 打开目标应用
     */
    public void openApp(String packageName) {
        Intent intent = getPackageManager().getLaunchIntentForPackage(packageName);
        if (intent != null) {
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(intent);
            Log.d(TAG, "打开应用: " + packageName);
        }
    }
    
    /**
     * 检查无障碍服务是否已启用
     */
    public static boolean isServiceEnabled() {
        return instance != null;
    }
}
