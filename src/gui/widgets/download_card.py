# -*- coding: utf-8 -*-

"""
下载卡片组件 - 显示下载任务状态
===============================

作者: GraceFox
用户名: HarePhantom
创建日期: 2026-03-14
"""

import os
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout

from qfluentwidgets import (
    CardWidget, IconWidget, StrongBodyLabel, CaptionLabel,
    ProgressBar, TransparentToolButton, FluentIcon as FIF
)


class DownloadCard(CardWidget):
    """
    下载任务卡片 - 现代化设计
    
    信号:
        cancelled: 取消信号
        paused: 暂停信号
        resumed: 恢复信号
    """

    cancelled = Signal(object)
    paused = Signal(object)
    resumed = Signal(object)

    def __init__(self, url: str, title: str = "", parent=None):
        """
        初始化下载卡片
        
        Args:
            url: 下载URL
            title: 视频标题
            parent: 父窗口
        """
        super().__init__(parent)
        self.url = url
        self.title = title or os.path.basename(url)
        self.progress = 0
        self.status = "等待中"
        self.paused_state = False
        self.file_path = None
        self.file_size = 0

        self.init_ui()
        self.setup_animations()

    def init_ui(self):
        """初始化用户界面"""
        self.setBorderRadius(8)
        self.setFixedHeight(120)

        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        # 头部区域
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # 图标
        self.icon = IconWidget(FIF.DOWNLOAD)
        self.icon.setFixedSize(24, 24)
        self.icon.setStyleSheet("color: #0078d4;")
        header_layout.addWidget(self.icon)

        # 标题
        self.title_label = StrongBodyLabel(self.title)
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumWidth(400)
        self.title_label.setStyleSheet("font-size: 14px;")
        header_layout.addWidget(self.title_label, 1)

        # 状态标签
        self.status_label = CaptionLabel(self.status)
        self.status_label.setStyleSheet("color: #666; padding: 2px 8px; border-radius: 10px;")
        header_layout.addWidget(self.status_label)

        layout.addLayout(header_layout)

        # 进度条
        self.progress_bar = ProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            ProgressBar {
                border: none;
                background-color: #f0f0f0;
            }
            ProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # 底部信息栏
        info_layout = QHBoxLayout()
        info_layout.setSpacing(16)

        # 文件大小
        self.size_label = CaptionLabel("0 MB")
        self.size_label.setStyleSheet("color: #999;")
        info_layout.addWidget(self.size_label)

        # 速度信息（可选）
        self.speed_label = CaptionLabel("")
        self.speed_label.setStyleSheet("color: #999;")
        info_layout.addWidget(self.speed_label)

        info_layout.addStretch()

        # 控制按钮
        self.pause_btn = TransparentToolButton(FIF.PAUSE)
        self.pause_btn.setFixedSize(28, 28)
        self.pause_btn.clicked.connect(self.toggle_pause)
        info_layout.addWidget(self.pause_btn)

        self.cancel_btn = TransparentToolButton(FIF.CLOSE)
        self.cancel_btn.setFixedSize(28, 28)
        self.cancel_btn.clicked.connect(self.cancel_download)
        info_layout.addWidget(self.cancel_btn)

        layout.addLayout(info_layout)

        # 设置样式
        self.setStyleSheet("""
            DownloadCard {
                background-color: white;
                border: 1px solid #e0e0e0;
            }
            DownloadCard:hover {
                border-color: #0078d4;
                background-color: #f8f9fa;
            }
        """)

    def setup_animations(self):
        """设置动画效果"""
        self.hover_animation = QPropertyAnimation(self, b"pos")
        self.hover_animation.setDuration(200)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)

    def update_progress(self, value: int, message: str = ""):
        """
        更新进度
        
        Args:
            value: 进度百分比
            message: 状态信息
        """
        self.progress = value
        self.progress_bar.setValue(value)

        # 更新状态
        if value >= 100:
            self.set_status("已完成", "success")
            self.pause_btn.hide()
        elif "失败" in message:
            self.set_status("失败", "error")
            self.pause_btn.hide()
        else:
            self.set_status(f"下载中 {value}%", "normal")

        # 解析文件大小
        if "大小:" in message:
            try:
                size_str = message.split("大小:")[1].strip()
                self.size_label.setText(size_str)
            except Exception:
                pass

    def set_status(self, status: str, status_type: str = "normal"):
        """
        设置状态
        
        Args:
            status: 状态文本
            status_type: 状态类型 (normal, success, warning, error)
        """
        self.status = status
        self.status_label.setText(status)
        
        colors = {
            "normal": "#0078d4",
            "success": "#28a745",
            "warning": "#ffc107",
            "error": "#dc3545",
            "info": "#666"
        }
        color = colors.get(status_type, colors["info"])
        
        self.status_label.setStyleSheet(f"""
            color: {color};
            background-color: {color}10;
            padding: 2px 8px;
            border-radius: 10px;
        """)

    def toggle_pause(self):
        """切换暂停/继续"""
        self.paused_state = not self.paused_state
        
        if self.paused_state:
            self.pause_btn.setIcon(FIF.PLAY)
            self.set_status("已暂停", "warning")
            self.paused.emit(self)
        else:
            self.pause_btn.setIcon(FIF.PAUSE)
            self.set_status(f"下载中 {self.progress}%", "normal")
            self.resumed.emit(self)

    def cancel_download(self):
        """取消下载"""
        self.set_status("已取消", "info")
        self.pause_btn.hide()
        self.cancel_btn.hide()
        self.cancelled.emit(self)

    def enterEvent(self, event):
        """鼠标进入事件"""
        self.setStyleSheet("""
            DownloadCard {
                background-color: #f8f9fa;
                border: 1px solid #0078d4;
            }
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.setStyleSheet("""
            DownloadCard {
                background-color: white;
                border: 1px solid #e0e0e0;
            }
        """)
        super().leaveEvent(event)