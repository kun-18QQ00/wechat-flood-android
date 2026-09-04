package com.msg.sender;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.content.ClipboardManager;
import android.content.ClipData;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

import java.util.List;

public class MessageAccessibilityService extends AccessibilityService {
    private static final String TAG = "MsgSender";
    private static MessageAccessibilityService instance;

    private static String pendingMessage = null;
    private static boolean autoMode = false;
    private static int sendCount = 0;
    private static int maxCount = 0;

    public static MessageAccessibilityService getInstance() {
        return instance;
    }

    @Override
    public void onServiceConnected() {
        super.onServiceConnected();
        instance = this;
        Log.i(TAG, "无障碍服务已连接");

        AccessibilityServiceInfo info = getServiceInfo();
        if (info == null) info = new AccessibilityServiceInfo();
        info.eventTypes = AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED
                | AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED
                | AccessibilityEvent.TYPE_VIEW_CLICKED;
        info.feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC;
        info.notificationTimeout = 100;
        info.flags = AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS
                | AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS
                | AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS;
        setServiceInfo(info);
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event == null) return;
        if (!autoMode || pendingMessage == null || pendingMessage.isEmpty()) return;

        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) return;

        try {
            AccessibilityNodeInfo input = findEditableNode(root);
            if (input != null) {
                doSend(input, root);
            }
        } catch (Exception e) {
            Log.e(TAG, "处理失败: " + e.getMessage());
        } finally {
            root.recycle();
        }
    }

    @Override
    public void onInterrupt() {}

    @Override
    public void onDestroy() {
        super.onDestroy();
        instance = null;
    }

    public boolean sendMessage(String message, String pkg, int count, long delay) {
        if (message == null || message.isEmpty()) return false;
        pendingMessage = message;
        maxCount = count;
        sendCount = 0;
        autoMode = true;
        Log.i(TAG, "发送: " + message);

        // 尝试立即发送
        new android.os.Handler(android.os.Looper.getMainLooper()).postDelayed(() -> {
            tryNow();
        }, 500);
        return true;
    }

    public void stopSending() {
        autoMode = false;
        pendingMessage = null;
        maxCount = 0;
        sendCount = 0;
    }

    private void tryNow() {
        if (!autoMode || pendingMessage == null) return;
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) return;
        try {
            AccessibilityNodeInfo input = findEditableNode(root);
            if (input != null) doSend(input, root);
        } catch (Exception e) {
            Log.e(TAG, "尝试发送失败: " + e.getMessage());
        } finally {
            root.recycle();
        }
    }

    private void doSend(AccessibilityNodeInfo input, AccessibilityNodeInfo root) {
        // 输入文本
        if (!setText(input, pendingMessage)) {
            pasteText(input, pendingMessage);
        }
        // 延迟点击发送
        new android.os.Handler(android.os.Looper.getMainLooper()).postDelayed(() -> {
            if (!autoMode) return;
            AccessibilityNodeInfo r = getRootInActiveWindow();
            if (r == null) return;
            try {
                if (clickSend(r)) {
                    sendCount++;
                    Log.i(TAG, "已发送 #" + sendCount);
                    if (maxCount > 0 && sendCount >= maxCount) {
                        stopSending();
                    }
                }
            } catch (Exception e) {
                Log.e(TAG, "点击发送失败: " + e.getMessage());
            } finally {
                r.recycle();
            }
        }, 300);
    }

    private AccessibilityNodeInfo findEditableNode(AccessibilityNodeInfo node) {
        if (node == null) return null;
        if (node.isEditable() && node.isVisibleToUser()) return node;
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            if (child != null) {
                AccessibilityNodeInfo r = findEditableNode(child);
                if (r != null) return r;
            }
        }
        return null;
    }

    private boolean setText(AccessibilityNodeInfo node, String text) {
        if (node == null) return false;
        node.performAction(AccessibilityNodeInfo.ACTION_FOCUS);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            Bundle args = new Bundle();
            args.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text);
            return node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args);
        }
        return false;
    }

    private void pasteText(AccessibilityNodeInfo node, String text) {
        if (node == null) return;
        ClipboardManager cm = (ClipboardManager) getSystemService(CLIPBOARD_SERVICE);
        cm.setPrimaryClip(ClipData.newPlainText("msg", text));
        node.performAction(AccessibilityNodeInfo.ACTION_FOCUS);
        node.performAction(AccessibilityNodeInfo.ACTION_PASTE);
    }

    private boolean clickSend(AccessibilityNodeInfo root) {
        // 方案1: 按文本查找
        String[] texts = {"发送", "Send", "send", "确定", "OK"};
        for (String t : texts) {
            List<AccessibilityNodeInfo> nodes = root.findAccessibilityNodeInfosByText(t);
            if (nodes != null) {
                for (AccessibilityNodeInfo n : nodes) {
                    if (n != null && n.isVisibleToUser() && n.isClickable()) {
                        boolean r = n.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                        n.recycle();
                        if (r) return true;
                    }
                    if (n != null) n.recycle();
                }
            }
        }
        // 方案2: 查找右下角可点击元素
        return clickRightBottom(root);
    }

    private boolean clickRightBottom(AccessibilityNodeInfo node) {
        if (node == null) return false;
        android.graphics.Rect rect = new android.graphics.Rect();
        node.getBoundsInScreen(rect);
        android.util.DisplayMetrics dm = getResources().getDisplayMetrics();
        int sw = dm.widthPixels;
        int sh = dm.heightPixels;
        if (rect.right > sw * 0.7 && rect.bottom > sh * 0.6
                && node.isClickable() && node.isVisibleToUser()) {
            CharSequence text = node.getText();
            CharSequence desc = node.getContentDescription();
            if (text != null && text.length() <= 6) {
                boolean r = node.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                if (r) return true;
            }
            if (desc != null && (desc.toString().contains("发送") || desc.toString().contains("send"))) {
                boolean r = node.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                if (r) return true;
            }
        }
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            if (child != null) {
                if (clickRightBottom(child)) return true;
            }
        }
        return false;
    }

    private AccessibilityNodeInfo findNodeById(AccessibilityNodeInfo root, String id) {
        List<AccessibilityNodeInfo> nodes = root.findAccessibilityNodeInfosByViewId(id);
        if (nodes != null && !nodes.isEmpty()) return nodes.get(0);
        return null;
    }
}
