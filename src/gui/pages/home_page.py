# -*- coding: utf-8 -*-

"""
首页页面 - 应用程序主仪表盘
===========================

作者: GraceFox
用户名: HarePhantom
创建日期: 2026-03-14

功能:
- 显示统计信息
- 快速操作入口
- 系统状态检查
"""

import os
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication, QFrame

from qfluentwidgets import (
    CardWidget, TitleLabel, BodyLabel, StrongBodyLabel,
    PushButton, IconWidget, FlowLayout,
    FluentIcon as FIF, InfoBar, ScrollArea, ImageLabel
)

from src.gui.widgets import StatisticCard


class HomePage(QWidget):
    """
    首页界面 - 现代化仪表盘
    
    属性:
        parent_window: 主窗口引用
        download_stat: 下载统计卡片
        convert_stat: 转换统计卡片
        audio_stat: 音频统计卡片
        ffmpeg_stat: FFmpeg状态卡片
    """

    def __init__(self, parent=None):
        """初始化首页"""
        super().__init__(parent)
        self.setObjectName("home_page")
        
        self.parent_window = parent
        
        # 统计卡片引用
        self.download_stat = None
        self.convert_stat = None
        self.audio_stat = None
        self.ffmpeg_stat = None
        
        # Logo路径
        self.logo_paths = [
            "resources/icons/logo.png",
            "resources/icons/logo.ico",
            "resources/icons/logo.svg",
        ]
        
        self.update_timer = None

        self.init_ui()
        self.start_updates()

    def init_ui(self):
        """初始化用户界面"""
        # 创建滚动区域
        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        # 主容器
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        # 欢迎区域（带Logo）
        layout.addWidget(self.create_welcome_section())
        
        # 统计卡片区域
        layout.addWidget(self.create_stats_section())
        
        # 快速操作区域
        layout.addWidget(self.create_quick_actions())
        
        # 最新活动区域
        layout.addWidget(self.create_activity_section())
        
        layout.addStretch()
        
        scroll.setWidget(container)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def create_welcome_section(self) -> QWidget:
        """创建欢迎区域（带Logo）"""
        card = CardWidget()
        card.setBorderRadius(12)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 左侧内容
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)

        title = TitleLabel("欢迎使用易下(EDown)")
        title.setStyleSheet("font-size: 28px; font-weight: 600; color: #0078d4;")
        left_layout.addWidget(title)

        subtitle = BodyLabel("支持多平台视频下载、格式转换和音频提取")
        subtitle.setStyleSheet("color: #666; font-size: 16px;")
        left_layout.addWidget(subtitle)

        # 快捷按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        download_btn = PushButton(FIF.DOWNLOAD, "开始下载")
        download_btn.clicked.connect(self.go_to_download)
        download_btn.setFixedWidth(120)
        btn_layout.addWidget(download_btn)
        
        convert_btn = PushButton(FIF.VIDEO, "格式转换")
        convert_btn.clicked.connect(self.go_to_convert)
        convert_btn.setFixedWidth(120)
        btn_layout.addWidget(convert_btn)
        
        btn_layout.addStretch()
        left_layout.addLayout(btn_layout)

        layout.addLayout(left_layout)

        # 右侧Logo - 无边框版本
        self.logo_widget = self.create_logo_widget()
        layout.addWidget(self.logo_widget)

        return card

    def create_logo_widget(self) -> QWidget:
        """创建Logo组件（无边框）"""
        widget = QWidget()
        widget.setFixedSize(120, 120)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        # 尝试加载自定义Logo
        logo_loaded = False
        
        # 首先检查是否有自定义图标（从主窗口获取）
        if self.parent_window and hasattr(self.parent_window, 'custom_icon_path'):
            custom_icon = self.parent_window.custom_icon_path
            if custom_icon and os.path.exists(custom_icon):
                try:
                    logo_label = ImageLabel(custom_icon)
                    logo_label.scaledToWidth(100)
                    logo_label.setBorderRadius(50, 50, 50, 50)
                    # 无边框样式
                    logo_label.setStyleSheet("""
                        background-color: transparent;
                        border: none;
                    """)
                    layout.addWidget(logo_label)
                    logo_loaded = True
                except Exception:
                    pass

        # 如果没有自定义图标，尝试从预设路径加载
        if not logo_loaded:
            for logo_path in self.logo_paths:
                if os.path.exists(logo_path):
                    try:
                        logo_label = ImageLabel(logo_path)
                        logo_label.scaledToWidth(100)
                        logo_label.setBorderRadius(50, 50, 50, 50)
                        # 无边框样式
                        logo_label.setStyleSheet("""
                            background-color: transparent;
                            border: none;
                        """)
                        layout.addWidget(logo_label)
                        logo_loaded = True
                        break
                    except Exception:
                        continue

        # 如果没有找到任何Logo，使用默认图标（无边框）
        if not logo_loaded:
            icon = IconWidget(FIF.DOWNLOAD)
            icon.setFixedSize(100, 100)
            icon.setStyleSheet("""
                IconWidget {
                    color: #0078d4;
                    background-color: rgba(0, 120, 212, 0.1);
                    border-radius: 50px;
                    padding: 20px;
                    border: none;
                }
            """)
            layout.addWidget(icon)

        return widget

    def create_stats_section(self) -> QWidget:
        """创建统计卡片区域"""
        widget = QWidget()
        layout = FlowLayout(widget, needAni=False)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 创建统计卡片
        self.download_stat = StatisticCard("下载次数", "0", FIF.DOWNLOAD)
        layout.addWidget(self.download_stat)

        self.convert_stat = StatisticCard("转换次数", "0", FIF.VIDEO)
        layout.addWidget(self.convert_stat)

        self.audio_stat = StatisticCard("音频提取", "0", FIF.MUSIC)
        layout.addWidget(self.audio_stat)

        self.ffmpeg_stat = StatisticCard("FFmpeg", "检查中", FIF.CLOUD)
        layout.addWidget(self.ffmpeg_stat)

        return widget

    def create_quick_actions(self) -> QWidget:
        """创建快速操作区域"""
        card = CardWidget()
        card.setBorderRadius(12)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title = StrongBodyLabel("快速操作")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(title)

        # 按钮网格
        grid_layout = FlowLayout(needAni=False)
        grid_layout.setSpacing(12)

        actions = [
            (FIF.PASTE, "粘贴链接并下载", self.paste_and_download),
            (FIF.DOCUMENT, "批量转换", self.go_to_convert),
            (FIF.MUSIC, "音频提取", self.go_to_audio),
            (FIF.SETTING, "设置", self.go_to_settings),
        ]

        for icon, text, callback in actions:
            btn = PushButton(icon, text)
            btn.clicked.connect(callback)
            btn.setFixedSize(150, 40)
            grid_layout.addWidget(btn)

        layout.addLayout(grid_layout)

        return card

    def create_activity_section(self) -> QWidget:
        """创建活动区域"""
        card = CardWidget()
        card.setBorderRadius(12)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title = StrongBodyLabel("最新活动")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(title)

        # 活动内容
        self.activity_text = BodyLabel("暂无活动记录")
        self.activity_text.setStyleSheet("color: #999; padding: 30px;")
        self.activity_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.activity_text)

        return card

    def start_updates(self):
        """启动定时更新"""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(1000)

    def update_stats(self):
        """更新统计信息"""
        if self.parent_window:
            self.download_stat.set_value(str(self.parent_window.download_count))
            self.convert_stat.set_value(str(self.parent_window.convert_count))
            self.audio_stat.set_value(str(self.parent_window.audio_count))

    def update_logo(self):
        """更新Logo（当图标改变时调用）"""
        # 重新创建Logo组件
        if hasattr(self, 'logo_widget'):
            # 获取欢迎区域卡片
            parent_widget = self.logo_widget.parent()
            if parent_widget:
                layout = parent_widget.layout()
                if layout:
                    # 移除旧的Logo
                    layout.removeWidget(self.logo_widget)
                    self.logo_widget.deleteLater()
                    
                    # 创建新的Logo（无边框）
                    self.logo_widget = self.create_logo_widget()
                    layout.addWidget(self.logo_widget)

    def paste_and_download(self):
        """粘贴链接并下载"""
        try:
            clipboard = QApplication.clipboard()
            url = clipboard.text().strip()
            if url:
                if hasattr(self.parent_window, 'download_page'):
                    self.parent_window.download_page.set_url(url)
                    self.parent_window.go_to_download()
                    QTimer.singleShot(500, self.parent_window.download_page.analyze)
            else:
                InfoBar.warning("提示", "剪贴板为空", parent=self)
        except Exception as e:
            InfoBar.error("错误", str(e), parent=self)

    def go_to_download(self):
        """跳转到下载页面"""
        if self.parent_window:
            self.parent_window.go_to_download()

    def go_to_convert(self):
        """跳转到转换页面"""
        if self.parent_window:
            self.parent_window.go_to_convert()

    def go_to_audio(self):
        """跳转到音频页面"""
        if self.parent_window:
            self.parent_window.go_to_audio()

    def go_to_settings(self):
        """跳转到设置页面"""
        if self.parent_window:
            self.parent_window.go_to_settings()