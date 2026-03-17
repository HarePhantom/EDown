# -*- coding: utf-8 -*-

"""
Fluent Design 主窗口 - 应用程序主界面
=====================================

作者: GraceFox
用户名: HarePhantom
创建日期: 2026-03-14

功能:
- 导航栏管理
- 页面切换
- 窗口拖动
- 设置管理
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QFont, QMouseEvent, QAction, QIcon, QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication, QFrame

from qfluentwidgets import (
    FluentWindow, FluentIcon as FIF, NavigationItemPosition,
    TitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    PushButton, ToolButton, InfoBar,
    setTheme, Theme, CardWidget, IconWidget,
    FluentStyleSheet, isDarkTheme, ImageLabel
)

from src.gui.pages import HomePage, DownloadPage, ConvertPage, AudioPage, SettingsPage


class FluentVideoDownloaderApp(FluentWindow):
    """
    Fluent Design 主窗口 - 支持任意位置拖动
    
    属性:
        download_count: 下载计数
        convert_count: 转换计数
        audio_count: 音频提取计数
        custom_icon_path: 自定义图标路径
        dragging: 拖动状态
    """

    def __init__(self):
        """初始化主窗口"""
        super().__init__()

        # 初始化变量
        self.download_count = 0
        self.convert_count = 0
        self.audio_count = 0
        
        # 拖动相关变量
        self.dragging = False
        self.drag_position = None
        
        # 图标路径
        self.custom_icon_path = None

        # 加载设置
        self.load_settings()

        # 初始化界面
        self.init_window()
        self.init_navigation()
        
        # 设置应用图标
        self.set_app_icon()
        
        # 检查FFmpeg
        QTimer.singleShot(500, self.check_ffmpeg)

    def init_window(self):
        """初始化窗口属性"""
        self.setWindowTitle("易下(EDown)")
        self.resize(1200, 800)
        self.setMinimumSize(1000, 600)

        # 设置窗口属性
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # 设置窗口样式
        FluentStyleSheet.FLUENT_WINDOW.apply(self)

        # 设置窗口位置居中
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )

        # 设置应用字体
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)

    def set_app_icon(self):
        """设置应用图标"""
        icon_paths = [
            self.custom_icon_path,
            "resources/icons/logo.ico",
            "resources/icons/logo.png",
            "resources/icons/logo.svg",
        ]
        
        for path in icon_paths:
            if path and os.path.exists(path):
                icon = QIcon(path)
                if not icon.isNull():
                    self.setWindowIcon(icon)
                    # 同时设置任务栏图标
                    if hasattr(QApplication, 'setWindowIcon'):
                        QApplication.instance().setWindowIcon(icon)
                    return
        
        # 如果没有找到自定义图标，使用默认图标
        try:
            self.setWindowIcon(FIF.DOWNLOAD)
        except Exception:
            pass

    def init_navigation(self):
        """初始化导航栏"""
        # 创建各页面实例
        self.home_page = HomePage(self)
        self.download_page = DownloadPage(self)
        self.convert_page = ConvertPage(self)
        self.audio_page = AudioPage(self)
        self.settings_page = SettingsPage(self)

        # 添加导航项
        self.addSubInterface(self.home_page, FIF.HOME, "首页")
        self.addSubInterface(self.download_page, FIF.DOWNLOAD, "下载")
        self.addSubInterface(self.convert_page, FIF.VIDEO, "转换")
        self.addSubInterface(self.audio_page, FIF.MUSIC, "音频")
        self.addSubInterface(self.settings_page, FIF.SETTING, "设置", NavigationItemPosition.BOTTOM)

        # 关于页面
        about_widget = self.create_about_page()
        self.addSubInterface(about_widget, FIF.INFO, "关于", NavigationItemPosition.BOTTOM)

        # 设置初始页面
        self.switchTo(self.home_page)

    def create_about_page(self) -> QWidget:
        """创建关于页面"""
        widget = QWidget()
        widget.setObjectName("about_page")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 关于卡片
        card = CardWidget()
        card.setBorderRadius(12)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(20)
        card_layout.setAlignment(Qt.AlignCenter)

        # 图标 - 使用自定义图标或默认图标
        icon_widget = QWidget()
        icon_layout = QHBoxLayout(icon_widget)
        icon_layout.setAlignment(Qt.AlignCenter)
        
        # 尝试加载自定义图标
        icon_path = self.custom_icon_path or "resources/icons/logo.png"
        if os.path.exists(icon_path):
            icon_label = ImageLabel(icon_path)
            icon_label.scaledToWidth(80)
            icon_label.setBorderRadius(40, 40, 40, 40)
            icon_layout.addWidget(icon_label)
        else:
            icon = IconWidget(FIF.DOWNLOAD)
            icon.setFixedSize(80, 80)
            icon.setStyleSheet("""
                IconWidget {
                    color: #0078d4;
                    background-color: rgba(0, 120, 212, 0.1);
                    border-radius: 40px;
                    padding: 16px;
                }
            """)
            icon_layout.addWidget(icon)
        
        card_layout.addWidget(icon_widget)

        # 标题
        title = TitleLabel("易下(EDown)")
        title.setStyleSheet("font-size: 28px; font-weight: 600; color: #0078d4;")
        card_layout.addWidget(title, 0, Qt.AlignCenter)

        # 版本
        version = BodyLabel("版本 0.1.0")
        version.setStyleSheet("color: #666; font-size: 14px;")
        card_layout.addWidget(version, 0, Qt.AlignCenter)

        # 作者信息
        author = BodyLabel("作者: GraceFox (HarePhantom)")
        author.setStyleSheet("color: #666; font-size: 14px;")
        card_layout.addWidget(author, 0, Qt.AlignCenter)

        # 联系方式
        contact = BodyLabel("邮箱: 948743980@qq.com")
        contact.setStyleSheet("color: #666; font-size: 14px;")
        card_layout.addWidget(contact, 0, Qt.AlignCenter)

        # 分割线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #e0e0e0; margin: 10px 0;")
        card_layout.addWidget(separator)

        # 功能列表
        features_title = StrongBodyLabel("功能特点")
        features_title.setStyleSheet("font-size: 16px; margin-top: 10px;")
        card_layout.addWidget(features_title, 0, Qt.AlignLeft)

        features = [
            "✓ 支持多平台视频下载（YouTube、Bilibili、优酷等）",
            "✓ 内置FFmpeg视频转换",
            "✓ 音频提取功能（MP3、AAC、FLAC等）",
            "✓ 批量处理功能",
            "✓ 现代化的Fluent Design界面",
            "✓ 支持自定义应用图标",
        ]

        for feature in features:
            label = BodyLabel(feature)
            label.setStyleSheet("color: #333; font-size: 13px; margin: 2px 0;")
            card_layout.addWidget(label, 0, Qt.AlignLeft)

        # 版权信息
        copyright_label = CaptionLabel("© 2026 GraceFox. All rights reserved.")
        copyright_label.setStyleSheet("color: #999; margin-top: 20px;")
        card_layout.addWidget(copyright_label, 0, Qt.AlignCenter)

        layout.addWidget(card)
        layout.addStretch()

        return widget

    def set_custom_icon(self, icon_path: str):
        """
        设置自定义图标
        
        Args:
            icon_path: 图标文件路径
        """
        if os.path.exists(icon_path):
            self.custom_icon_path = icon_path
            self.set_app_icon()
            # 保存图标路径到设置
            self.save_custom_icon_setting(icon_path)
            
            # 更新首页Logo
            if hasattr(self, 'home_page') and hasattr(self.home_page, 'update_logo'):
                self.home_page.update_logo()
            
            InfoBar.success("图标已更新", "应用图标已成功更改", parent=self)
        else:
            InfoBar.error("图标文件不存在", f"找不到图标文件：{icon_path}", parent=self)

    def save_custom_icon_setting(self, icon_path: str):
        """
        保存自定义图标设置
        
        Args:
            icon_path: 图标文件路径
        """
        try:
            settings_dir = Path("output")
            settings_dir.mkdir(exist_ok=True)
            settings_file = settings_dir / "settings.json"

            settings = {}
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

            settings['custom_icon'] = icon_path

            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存图标设置失败: {e}")

    # ==================== 窗口拖动功能 ====================
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 检查是否点击在标题栏区域（窗口顶部80像素）
            if event.position().y() <= 80:
                self.dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件"""
        if self.dragging and not self.isMaximized():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    # ==================== 设置管理 ====================
    def load_settings(self):
        """加载设置"""
        try:
            settings_file = Path("output/settings.json")
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                # 应用主题
                theme = settings.get('theme', '浅色')
                if theme == '深色':
                    setTheme(Theme.DARK)
                elif theme == '浅色':
                    setTheme(Theme.LIGHT)
                    
                # 加载计数
                self.download_count = settings.get('download_count', 0)
                self.convert_count = settings.get('convert_count', 0)
                self.audio_count = settings.get('audio_count', 0)
                
                # 加载自定义图标
                custom_icon = settings.get('custom_icon')
                if custom_icon and os.path.exists(custom_icon):
                    self.custom_icon_path = custom_icon
        except Exception as e:
            print(f"加载设置失败: {e}")

    def save_settings(self):
        """保存设置"""
        try:
            settings_dir = Path("output")
            settings_dir.mkdir(exist_ok=True)
            settings_file = settings_dir / "settings.json"
            
            settings = {}
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            settings.update({
                'download_count': self.download_count,
                'convert_count': self.convert_count,
                'audio_count': self.audio_count,
                'custom_icon': self.custom_icon_path
            })
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置失败: {e}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        self.save_settings()
        super().closeEvent(event)

    # ==================== 导航方法 ====================
    def go_to_download(self):
        """跳转到下载页面"""
        self.switchTo(self.download_page)

    def go_to_convert(self):
        """跳转到转换页面"""
        self.switchTo(self.convert_page)

    def go_to_audio(self):
        """跳转到音频页面"""
        self.switchTo(self.audio_page)

    def go_to_settings(self):
        """跳转到设置页面"""
        self.switchTo(self.settings_page)

    def check_ffmpeg(self):
        """检查FFmpeg"""
        from src.core.utils import get_ffmpeg_path
        ffmpeg_path = get_ffmpeg_path()
        
        if ffmpeg_path and hasattr(self, 'home_page'):
            try:
                result = subprocess.run([ffmpeg_path, '-version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version = result.stdout.split('\n')[0][:50]
                    self.home_page.ffmpeg_stat.set_value("正常", "success")
                    self.home_page.ffmpeg_stat.setToolTip(version)
                    return
            except Exception as e:
                print(f"FFmpeg检查错误: {e}")
        
        if hasattr(self, 'home_page'):
            self.home_page.ffmpeg_stat.set_value("异常", "error")
            self.home_page.ffmpeg_stat.setToolTip("请安装FFmpeg并添加到系统PATH")

    def show_notification(self, title: str, content: str, type: str = "info"):
        """
        显示通知
        
        Args:
            title: 标题
            content: 内容
            type: 类型 (info, success, error, warning)
        """
        if type == "success":
            InfoBar.success(title, content, parent=self)
        elif type == "error":
            InfoBar.error(title, content, parent=self)
        elif type == "warning":
            InfoBar.warning(title, content, parent=self)
        else:
            InfoBar.info(title, content, parent=self)