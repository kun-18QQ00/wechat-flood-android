package com.msg.sender;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.content.ClipboardManager;
import android.content.ClipData;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

import java.util.List;

/**
 * 消息助手无障碍服务 v7.0
 * 自动识别聊天输入框，输入文本并点击发送
 */
public class MessageAccessibilityService extends AccessibilityService {
    private static final String TAG = "MsgSender";
    private static MessageAccessibilityService instance;

    // 待发送队列
    private static String pendingMessage = null;
    private static boolean autoMode = false;
    private static int sendCount = 0;
    private static int maxCount = 0;
    private static String targetPackage = null;

    // 支持的应用
    private static final String[] SUPPORTED_PACKAGES = {
        "com.tencent.mm",
        "com.tencent.mobileqq",
        "com.alibaba.android.rimet",
        "com.ss.android.lark",
        "org.telegram.messenger",
        "com.whatsapp"
    };

    public static MessageAccessibilityService getInstance() {
        return instance;
    }

    @Override
    public void onServiceConnected() {
        super.onServiceConnected();
        instance = this;
        Log.i(TAG, "无障碍服务已连接");

        AccessibilityServiceInfo info = getServiceInfo();
        if (info == null) {
            info = new AccessibilityServiceInfo();
        }
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

        CharSequence pkgCs = event.getPackageName();
        if (pkgCs == null) return;
        String pkg = pkgCs.toString();

        // 如果指定了目标包名，只在目标应用中发送
        if (targetPackage != null && !targetPackage.isEmpty()) {
            if (!pkg.equals(targetPackage)) return;
        } else {
            // 没有指定目标，检查是否是支持的应用
            if (!isSupportedPackage(pkg)) return;
        }

        // 检查是否在聊天页面（通过查找可编辑输入框判断）
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) return;

        try {
            AccessibilityNodeInfo inputNode = findEditableNode(root);
            if (inputNode != null) {
                performSend(inputNode, root);
            }
        } catch (Exception e) {
            Log.e(TAG, "处理事件失败: " + e.getMessage());
        } finally {
            root.recycle();
        }
    }

    @Override
    public void onInterrupt() {
        Log.w(TAG, "无障碍服务被中断");
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        instance = null;
        Log.i(TAG, "无障碍服务已销毁");
    }

    // ══════════════════════════════════════
    // 公开 API（供 Python 端调用）
    // ══════════════════════════════════════

    /**
     * 开始自动发送
     * @param message  要发送的消息文本
     * @param pkg      目标应用包名（null=自动检测）
     * @param count    发送次数上限（0=无限）
     * @param delay    每次发送间隔毫秒
     * @return 是否成功启动
     */
    public boolean sendMessage(String message, String pkg, int count, long delay) {
        if (message == null || message.isEmpty()) return false;

        pendingMessage = message;
        targetPackage = pkg;
        maxCount = count;
        sendCount = 0;
        autoMode = true;

        Log.i(TAG, "开始发送: " + message + " -> " + pkg);

        // 尝试打开目标应用
        if (pkg != null && !pkg.isEmpty()) {
            openApp(pkg);
        }

        // 尝试立即发送（不延迟，由Python端控制间隔）
        tryImmediateSend();

        return true;
    }

    /**
     * 停止发送
     */
    public void stopSending() {
        autoMode = false;
        pendingMessage = null;
        targetPackage = null;
        maxCount = 0;
        sendCount = 0;
        Log.i(TAG, "已停止发送");
    }

    /**
     * 检查是否正在运行
     */
    public boolean isRunning() {
        return autoMode;
    }

    /**
     * 获取已发送数量
     */
    public int getSendCount() {
        return sendCount;
    }

    /**
     * 检查服务是否可用
     */
    public boolean isServiceReady() {
        return instance != null;
    }

    // ══════════════════════════════════════
    // 内部方法
    // ══════════════════════════════════════

    private boolean isSupportedPackage(String packageName) {
        for (String pkg : SUPPORTED_PACKAGES) {
            if (pkg.equals(packageName)) return true;
        }
        return false;
    }

    private void openApp(String packageName) {
        try {
            Intent intent = getPackageManager().getLaunchIntentForPackage(packageName);
            if (intent != null) {
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                startActivity(intent);
                Log.d(TAG, "已打开应用: " + packageName);
            } else {
                Log.w(TAG, "找不到应用: " + packageName);
            }
        } catch (Exception e) {
            Log.e(TAG, "打开应用失败: " + e.getMessage());
        }
    }

    /**
     * 尝试立即发送（不等待事件）
     */
    private void tryImmediateSend() {
        if (!autoMode || pendingMessage == null) return;

        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) {
            Log.d(TAG, "无法获取窗口根节点，等待事件触发");
            return;
        }

        try {
            AccessibilityNodeInfo inputNode = findEditableNode(root);
            if (inputNode != null) {
                performSend(inputNode, root);
            } else {
                Log.d(TAG, "未找到输入框，等待页面加载");
            }
        } catch (Exception e) {
            Log.e(TAG, "立即发送失败: " + e.getMessage());
        } finally {
            root.recycle();
        }
    }

    /**
     * 执行发送操作：输入文本 -> 点击发送按钮
     */
    private void performSend(AccessibilityNodeInfo inputNode, AccessibilityNodeInfo root) {
        // 1. 输入文本
        if (!setNodeText(inputNode, pendingMessage)) {
            Log.w(TAG, "输入文本失败，尝试粘贴方式");
            pasteText(inputNode, pendingMessage);
        }

        // 2. 延迟后点击发送按钮
        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            if (!autoMode) return;

            AccessibilityNodeInfo freshRoot = getRootInActiveWindow();
            if (freshRoot == null) return;

            try {
                if (clickSendButton(freshRoot)) {
                    sendCount++;
                    Log.i(TAG, "已发送第 " + sendCount + " 条");

                    if (maxCount > 0 && sendCount >= maxCount) {
                        stopSending();
                        Log.i(TAG, "已达到最大发送次数");
                    }
                } else {
                    Log.w(TAG, "未找到发送按钮");
                }
            } catch (Exception e) {
                Log.e(TAG, "点击发送失败: " + e.getMessage());
            } finally {
                freshRoot.recycle();
            }
        }, 300);
    }

    /**
     * 递归查找可编辑的输入框节点
     */
    private AccessibilityNodeInfo findEditableNode(AccessibilityNodeInfo node) {
        if (node == null) return null;

        if (node.isEditable() && node.isVisibleToUser()) {
            return node;
        }

        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            if (child != null) {
                AccessibilityNodeInfo result = findEditableNode(child);
                if (result != null) return result;
            }
        }
        return null;
    }

    /**
     * 通过 ACTION_SET_TEXT 设置文本
     */
    private boolean setNodeText(AccessibilityNodeInfo node, String text) {
        if (node == null) return false;

        node.performAction(AccessibilityNodeInfo.ACTION_FOCUS);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            Bundle args = new Bundle();
            args.putCharSequence(
                AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text);
            return node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args);
        }
        return false;
    }

    /**
     * 通过剪贴板粘贴文本（备用方案）
     */
    private void pasteText(AccessibilityNodeInfo node, String text) {
        if (node == null) return;

        ClipboardManager clipboard = (ClipboardManager) getSystemService(CLIPBOARD_SERVICE);
        ClipData clip = ClipData.newPlainText("msg", text);
        clipboard.setPrimaryClip(clip);

        node.performAction(AccessibilityNodeInfo.ACTION_FOCUS);
        node.performAction(AccessibilityNodeInfo.ACTION_PASTE);

        Log.d(TAG, "已通过粘贴方式输入文本");
    }

    /**
     * 查找并点击发送按钮
     * 优先通过常见ID查找，然后通过文本"发送"/"Send"查找
     */
    private boolean clickSendButton(AccessibilityNodeInfo root) {
        // 方案1：通过常见发送按钮ID查找
        String[] sendButtonIds = {
            "com.tencent.mm:id/chatting_send_btn",
            "com.tencent.mm:id/send_btn",
            "com.tencent.mobileqq:id/fun_btn",
            "com.tencent.mobileqq:id/send_btn",
            "com.alibaba.android.rimet:id/btn_send",
            "com.ss.android.lark:id/btn_send",
            "org.telegram.messenger:id/send_button",
            "com.whatsapp:id/send"
        };

        for (String id : sendButtonIds) {
            AccessibilityNodeInfo btn = findNodeById(root, id);
            if (btn != null) {
                boolean result = btn.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                btn.recycle();
                if (result) return true;
            }
        }

        // 方案2：通过文本查找"发送"按钮
        String[] sendTexts = {"发送", "Send", "send"};
        for (String text : sendTexts) {
            List<AccessibilityNodeInfo> nodes = root.findAccessibilityNodeInfosByText(text);
            if (nodes != null) {
                for (AccessibilityNodeInfo n : nodes) {
                    if (n != null && n.isVisibleToUser()) {
                        // 检查是否是按钮类型
                        CharSequence className = n.getClassName();
                        if (className != null && className.toString().contains("Button")) {
                            boolean result = n.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                            n.recycle();
                            if (result) return true;
                        }
                        // 尝试点击任何可点击的节点
                        if (n.isClickable()) {
                            boolean result = n.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                            n.recycle();
                            if (result) return true;
                        }
                    }
                    if (n != null) n.recycle();
                }
            }
        }

        // 方案3：查找屏幕右下角的可点击节点（微信等应用的发送按钮通常在右下角）
        AccessibilityNodeInfo rightBottom = findRightBottomClickable(root);
        if (rightBottom != null) {
            boolean result = rightBottom.performAction(AccessibilityNodeInfo.ACTION_CLICK);
            rightBottom.recycle();
            if (result) return true;
        }

        return false;
    }

    /**
     * 查找右下角的可点击节点（可能是发送按钮）
     */
    private AccessibilityNodeInfo findRightBottomClickable(AccessibilityNodeInfo node) {
        if (node == null) return null;

        android.graphics.Rect rect = new android.graphics.Rect();
        node.getBoundsInScreen(rect);

        // 检查是否在屏幕右下角区域（使用屏幕比例而非硬编码像素）
        android.util.DisplayMetrics dm = getResources().getDisplayMetrics();
        int screenWidth = dm.widthPixels;
        int screenHeight = dm.heightPixels;
        if (rect.right > screenWidth * 0.7 && rect.bottom > screenHeight * 0.7
                && node.isClickable() && node.isVisibleToUser()) {
            CharSequence text = node.getText();
            CharSequence desc = node.getContentDescription();
            // 排除明显的非发送按钮
            if (text != null && (text.toString().contains("发送") || text.toString().length() <= 4)) {
                return node;
            }
            if (desc != null && desc.toString().contains("发送")) {
                return node;
            }
        }

        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            if (child != null) {
                AccessibilityNodeInfo result = findRightBottomClickable(child);
                if (result != null) return result;
            }
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
}





