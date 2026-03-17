# -*- coding: utf-8 -*-

"""
设置页面 - 应用程序配置
=======================

作者: GraceFox
用户名: HarePhantom
创建日期: 2026-03-14

功能:
- 通用设置
- 下载设置
- 转换设置
- 音频设置
- 图标自定义
"""

import os
import json
import platform
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QGroupBox
)
from PySide6.QtGui import QPixmap

from qfluentwidgets import (
    CardWidget, PushButton, PrimaryPushButton, ToolButton,
    BodyLabel, StrongBodyLabel, TitleLabel, CaptionLabel,
    InfoBar, FluentIcon as FIF,
    ComboBox, CheckBox, LineEdit, ScrollArea, TabWidget,
    SwitchButton, Slider, CompactSpinBox, ImageLabel
)

from src.core.utils import get_ffmpeg_path


class SettingsPage(QWidget):
    """
    设置页面
    
    属性:
        parent_window: 主窗口引用
    """

    def __init__(self, parent=None):
        """初始化设置页面"""
        super().__init__(parent)
        self.setObjectName("settings_page")
        
        self.parent_window = parent

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title = TitleLabel("设置")
        title.setStyleSheet("font-size: 24px; font-weight: 600; margin-bottom: 8px;")
        layout.addWidget(title)

        # 创建选项卡
        tab_widget = TabWidget()
        layout.addWidget(tab_widget)

        # 通用设置
        general_tab = self.create_general_tab()
        tab_widget.addTab(general_tab, "通用", FIF.SETTING)

        # 下载设置
        download_tab = self.create_download_tab()
        tab_widget.addTab(download_tab, "下载", FIF.DOWNLOAD)

        # 转换设置
        convert_tab = self.create_convert_tab()
        tab_widget.addTab(convert_tab, "转换", FIF.VIDEO)

        # 音频设置
        audio_tab = self.create_audio_tab()
        tab_widget.addTab(audio_tab, "音频", FIF.MUSIC)

        # 关于
        about_tab = self.create_about_tab()
        tab_widget.addTab(about_tab, "关于", FIF.INFO)

    def create_general_tab(self) -> QWidget:
        """创建通用设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 主题设置
        theme_card = CardWidget()
        theme_card.setBorderRadius(12)
        theme_layout = QVBoxLayout(theme_card)
        theme_layout.setContentsMargins(20, 16, 20, 16)
        theme_layout.setSpacing(12)

        theme_title = StrongBodyLabel("主题设置")
        theme_layout.addWidget(theme_title)

        # 主题选择
        theme_select_layout = QHBoxLayout()
        theme_select_layout.addWidget(BodyLabel("界面主题："))

        self.theme_combo = ComboBox()
        self.theme_combo.addItems(["浅色", "深色", "跟随系统"])
        self.theme_combo.setCurrentText("浅色")
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_select_layout.addWidget(self.theme_combo)

        theme_select_layout.addStretch()
        theme_layout.addLayout(theme_select_layout)

        # 语言设置
        lang_select_layout = QHBoxLayout()
        lang_select_layout.addWidget(BodyLabel("界面语言："))

        self.lang_combo = ComboBox()
        self.lang_combo.addItems(["中文(简体)", "中文(繁体)", "English"])
        self.lang_combo.setCurrentText("中文(简体)")
        lang_select_layout.addWidget(self.lang_combo)

        lang_select_layout.addStretch()
        theme_layout.addLayout(lang_select_layout)

        layout.addWidget(theme_card)

        # 图标设置
        icon_card = CardWidget()
        icon_card.setBorderRadius(12)
        icon_layout = QVBoxLayout(icon_card)
        icon_layout.setContentsMargins(20, 16, 20, 16)
        icon_layout.setSpacing(12)

        icon_title = StrongBodyLabel("图标设置")
        icon_layout.addWidget(icon_title)

        # 当前图标预览
        preview_layout = QHBoxLayout()
        preview_layout.addWidget(BodyLabel("当前图标："))
        
        self.icon_preview = ImageLabel()
        self.icon_preview.setFixedSize(48, 48)
        self.icon_preview.setBorderRadius(24, 24, 24, 24)
        self.icon_preview.setStyleSheet("border: 2px solid #e0e0e0; background-color: #f5f5f5;")
        
        # 加载当前图标
        self.update_icon_preview()
        
        preview_layout.addWidget(self.icon_preview)
        preview_layout.addStretch()
        icon_layout.addLayout(preview_layout)

        # 选择图标按钮
        icon_select_layout = QHBoxLayout()
        icon_select_layout.addWidget(BodyLabel("自定义图标："))
        
        self.icon_path_input = LineEdit()
        self.icon_path_input.setPlaceholderText("选择图标文件 (PNG, ICO, SVG)")
        self.icon_path_input.setReadOnly(True)
        icon_select_layout.addWidget(self.icon_path_input)
        
        icon_browse_btn = ToolButton(FIF.FOLDER)
        icon_browse_btn.setToolTip("浏览图标文件")
        icon_browse_btn.clicked.connect(self.browse_icon_file)
        icon_select_layout.addWidget(icon_browse_btn)
        
        icon_apply_btn = PushButton(FIF.ACCEPT, "应用")
        icon_apply_btn.clicked.connect(self.apply_custom_icon)
        icon_apply_btn.setFixedWidth(60)
        icon_select_layout.addWidget(icon_apply_btn)
        
        icon_layout.addLayout(icon_select_layout)
        
        # 重置默认图标
        reset_icon_btn = PushButton(FIF.CLOSE, "恢复默认图标")
        reset_icon_btn.clicked.connect(self.reset_default_icon)
        icon_layout.addWidget(reset_icon_btn)

        layout.addWidget(icon_card)

        # 系统设置
        system_card = CardWidget()
        system_card.setBorderRadius(12)
        system_layout = QVBoxLayout(system_card)
        system_layout.setContentsMargins(20, 16, 20, 16)
        system_layout.setSpacing(12)

        system_title = StrongBodyLabel("系统设置")
        system_layout.addWidget(system_title)

        # 开机自启
        auto_start_layout = QHBoxLayout()
        auto_start_label = BodyLabel("开机自启动")
        auto_start_layout.addWidget(auto_start_label)
        auto_start_layout.addStretch()
        
        self.auto_start_switch = SwitchButton()
        self.auto_start_switch.setChecked(False)
        auto_start_layout.addWidget(self.auto_start_switch)
        system_layout.addLayout(auto_start_layout)

        # 托盘图标
        tray_layout = QHBoxLayout()
        tray_label = BodyLabel("显示托盘图标")
        tray_layout.addWidget(tray_label)
        tray_layout.addStretch()
        
        self.tray_switch = SwitchButton()
        self.tray_switch.setChecked(True)
        tray_layout.addWidget(self.tray_switch)
        system_layout.addLayout(tray_layout)

        # 最小化到托盘
        minimize_layout = QHBoxLayout()
        minimize_label = BodyLabel("最小化时隐藏到托盘")
        minimize_layout.addWidget(minimize_label)
        minimize_layout.addStretch()
        
        self.minimize_tray_switch = SwitchButton()
        self.minimize_tray_switch.setChecked(False)
        minimize_layout.addWidget(self.minimize_tray_switch)
        system_layout.addLayout(minimize_layout)

        layout.addWidget(system_card)

        # 默认目录设置
        dirs_card = CardWidget()
        dirs_card.setBorderRadius(12)
        dirs_layout = QVBoxLayout(dirs_card)
        dirs_layout.setContentsMargins(20, 16, 20, 16)
        dirs_layout.setSpacing(12)

        dirs_title = StrongBodyLabel("默认目录")
        dirs_layout.addWidget(dirs_title)

        # 下载目录
        download_dir_layout = QHBoxLayout()
        download_dir_layout.addWidget(BodyLabel("下载目录："))

        self.download_dir_input = LineEdit()
        self.download_dir_input.setPlaceholderText("默认下载目录")
        download_dir_layout.addWidget(self.download_dir_input)

        download_dir_btn = ToolButton(FIF.FOLDER)
        download_dir_btn.clicked.connect(lambda: self.browse_dir(self.download_dir_input, "选择下载目录"))
        download_dir_layout.addWidget(download_dir_btn)

        dirs_layout.addLayout(download_dir_layout)

        # 转换输出目录
        convert_dir_layout = QHBoxLayout()
        convert_dir_layout.addWidget(BodyLabel("转换目录："))

        self.convert_dir_input = LineEdit()
        self.convert_dir_input.setPlaceholderText("默认转换输出目录")
        convert_dir_layout.addWidget(self.convert_dir_input)

        convert_dir_btn = ToolButton(FIF.FOLDER)
        convert_dir_btn.clicked.connect(lambda: self.browse_dir(self.convert_dir_input, "选择转换目录"))
        convert_dir_layout.addWidget(convert_dir_btn)

        dirs_layout.addLayout(convert_dir_layout)

        # 音频输出目录
        audio_dir_layout = QHBoxLayout()
        audio_dir_layout.addWidget(BodyLabel("音频目录："))

        self.audio_dir_input = LineEdit()
        self.audio_dir_input.setPlaceholderText("默认音频输出目录")
        audio_dir_layout.addWidget(self.audio_dir_input)

        audio_dir_btn = ToolButton(FIF.FOLDER)
        audio_dir_btn.clicked.connect(lambda: self.browse_dir(self.audio_dir_input, "选择音频目录"))
        audio_dir_layout.addWidget(audio_dir_btn)

        dirs_layout.addLayout(audio_dir_layout)

        layout.addWidget(dirs_card)

        # 保存按钮
        save_btn = PrimaryPushButton(FIF.SAVE, "保存设置")
        save_btn.clicked.connect(self.save_general_settings)
        layout.addWidget(save_btn)

        layout.addStretch()
        return widget

    def create_download_tab(self) -> QWidget:
        """创建下载设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 下载选项
        download_card = CardWidget()
        download_card.setBorderRadius(12)
        download_layout = QVBoxLayout(download_card)
        download_layout.setContentsMargins(20, 16, 20, 16)
        download_layout.setSpacing(12)

        download_title = StrongBodyLabel("下载选项")
        download_layout.addWidget(download_title)

        # 默认质量
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(BodyLabel("默认质量："))

        self.default_quality_combo = ComboBox()
        self.default_quality_combo.addItems(["最佳质量", "1080p", "720p", "480p", "360p", "音频仅"])
        self.default_quality_combo.setCurrentText("最佳质量")
        quality_layout.addWidget(self.default_quality_combo)

        quality_layout.addStretch()
        download_layout.addLayout(quality_layout)

        # 默认格式
        format_layout = QHBoxLayout()
        format_layout.addWidget(BodyLabel("默认格式："))

        self.default_format_combo = ComboBox()
        self.default_format_combo.addItems(["mp4", "webm", "mkv", "flv"])
        self.default_format_combo.setCurrentText("mp4")
        format_layout.addWidget(self.default_format_combo)

        format_layout.addStretch()
        download_layout.addLayout(format_layout)

        # 自动转换格式
        auto_convert_layout = QHBoxLayout()
        auto_convert_layout.addWidget(BodyLabel("自动转换格式"))
        auto_convert_layout.addStretch()
        self.auto_convert_switch = SwitchButton()
        self.auto_convert_switch.setChecked(True)
        auto_convert_layout.addWidget(self.auto_convert_switch)
        download_layout.addLayout(auto_convert_layout)

        # 下载播放列表
        playlist_layout = QHBoxLayout()
        playlist_layout.addWidget(BodyLabel("下载播放列表"))
        playlist_layout.addStretch()
        self.playlist_switch = SwitchButton()
        self.playlist_switch.setChecked(False)
        playlist_layout.addWidget(self.playlist_switch)
        download_layout.addLayout(playlist_layout)

        # 下载字幕
        subtitle_layout = QHBoxLayout()
        subtitle_layout.addWidget(BodyLabel("下载字幕"))
        subtitle_layout.addStretch()
        self.subtitle_switch = SwitchButton()
        self.subtitle_switch.setChecked(True)
        subtitle_layout.addWidget(self.subtitle_switch)
        download_layout.addLayout(subtitle_layout)

        layout.addWidget(download_card)

        # 网络设置
        network_card = CardWidget()
        network_card.setBorderRadius(12)
        network_layout = QVBoxLayout(network_card)
        network_layout.setContentsMargins(20, 16, 20, 16)
        network_layout.setSpacing(12)

        network_title = StrongBodyLabel("网络设置")
        network_layout.addWidget(network_title)

        # 并发下载数
        concurrent_layout = QHBoxLayout()
        concurrent_layout.addWidget(BodyLabel("并发下载数："))

        self.concurrent_spin = CompactSpinBox()
        self.concurrent_spin.setRange(1, 10)
        self.concurrent_spin.setValue(3)
        concurrent_layout.addWidget(self.concurrent_spin)

        concurrent_layout.addStretch()
        network_layout.addLayout(concurrent_layout)

        # 重试次数
        retry_layout = QHBoxLayout()
        retry_layout.addWidget(BodyLabel("重试次数："))

        self.retry_spin = CompactSpinBox()
        self.retry_spin.setRange(0, 10)
        self.retry_spin.setValue(3)
        retry_layout.addWidget(self.retry_spin)

        retry_layout.addStretch()
        network_layout.addLayout(retry_layout)

        # 超时时间
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(BodyLabel("超时时间(秒)："))

        self.timeout_spin = CompactSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setValue(30)
        timeout_layout.addWidget(self.timeout_spin)

        timeout_layout.addStretch()
        network_layout.addLayout(timeout_layout)

        layout.addWidget(network_card)

        # 保存按钮
        save_btn = PrimaryPushButton(FIF.SAVE, "保存设置")
        save_btn.clicked.connect(self.save_download_settings)
        layout.addWidget(save_btn)

        layout.addStretch()
        return widget

    def create_convert_tab(self) -> QWidget:
        """创建转换设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 转换选项
        convert_card = CardWidget()
        convert_card.setBorderRadius(12)
        convert_layout = QVBoxLayout(convert_card)
        convert_layout.setContentsMargins(20, 16, 20, 16)
        convert_layout.setSpacing(12)

        convert_title = StrongBodyLabel("转换选项")
        convert_layout.addWidget(convert_title)

        # 默认输出格式
        output_format_layout = QHBoxLayout()
        output_format_layout.addWidget(BodyLabel("默认输出格式："))

        self.convert_format_combo = ComboBox()
        self.convert_format_combo.addItems(["mp4", "mp3", "aac", "flac", "wav", "ogg", "m4a"])
        self.convert_format_combo.setCurrentText("mp4")
        output_format_layout.addWidget(self.convert_format_combo)

        output_format_layout.addStretch()
        convert_layout.addLayout(output_format_layout)

        # 默认视频质量
        video_quality_layout = QHBoxLayout()
        video_quality_layout.addWidget(BodyLabel("默认视频质量："))

        self.convert_video_quality_combo = ComboBox()
        self.convert_video_quality_combo.addItems(["原质量", "1080p", "720p", "480p", "360p"])
        self.convert_video_quality_combo.setCurrentText("原质量")
        video_quality_layout.addWidget(self.convert_video_quality_combo)

        video_quality_layout.addStretch()
        convert_layout.addLayout(video_quality_layout)

        # 保留原文件
        keep_original_layout = QHBoxLayout()
        keep_original_layout.addWidget(BodyLabel("保留原文件"))
        keep_original_layout.addStretch()
        self.convert_keep_original_switch = SwitchButton()
        self.convert_keep_original_switch.setChecked(True)
        keep_original_layout.addWidget(self.convert_keep_original_switch)
        convert_layout.addLayout(keep_original_layout)

        # 覆盖已存在文件
        overwrite_layout = QHBoxLayout()
        overwrite_layout.addWidget(BodyLabel("覆盖已存在文件"))
        overwrite_layout.addStretch()
        self.convert_overwrite_switch = SwitchButton()
        self.convert_overwrite_switch.setChecked(False)
        overwrite_layout.addWidget(self.convert_overwrite_switch)
        convert_layout.addLayout(overwrite_layout)

        layout.addWidget(convert_card)

        # FFmpeg设置
        ffmpeg_card = CardWidget()
        ffmpeg_card.setBorderRadius(12)
        ffmpeg_layout = QVBoxLayout(ffmpeg_card)
        ffmpeg_layout.setContentsMargins(20, 16, 20, 16)
        ffmpeg_layout.setSpacing(12)

        ffmpeg_title = StrongBodyLabel("FFmpeg设置")
        ffmpeg_layout.addWidget(ffmpeg_title)

        # FFmpeg路径
        ffmpeg_path_layout = QHBoxLayout()
        ffmpeg_path_layout.addWidget(BodyLabel("FFmpeg路径："))

        self.ffmpeg_path_input = LineEdit()
        self.ffmpeg_path_input.setPlaceholderText("自动检测FFmpeg路径")
        ffmpeg_path_layout.addWidget(self.ffmpeg_path_input)

        ffmpeg_browse_btn = ToolButton(FIF.FOLDER)
        ffmpeg_browse_btn.clicked.connect(self.browse_ffmpeg_path)
        ffmpeg_path_layout.addWidget(ffmpeg_browse_btn)

        ffmpeg_layout.addLayout(ffmpeg_path_layout)

        # 检测按钮
        detect_btn = PushButton(FIF.SEARCH, "检测FFmpeg")
        detect_btn.clicked.connect(self.detect_ffmpeg)
        ffmpeg_layout.addWidget(detect_btn)

        layout.addWidget(ffmpeg_card)

        # 保存按钮
        save_btn = PrimaryPushButton(FIF.SAVE, "保存设置")
        save_btn.clicked.connect(self.save_convert_settings)
        layout.addWidget(save_btn)

        layout.addStretch()
        return widget

    def create_audio_tab(self) -> QWidget:
        """创建音频设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 音频提取选项
        audio_card = CardWidget()
        audio_card.setBorderRadius(12)
        audio_layout = QVBoxLayout(audio_card)
        audio_layout.setContentsMargins(20, 16, 20, 16)
        audio_layout.setSpacing(12)

        audio_title = StrongBodyLabel("音频提取选项")
        audio_layout.addWidget(audio_title)

        # 默认音频格式
        audio_format_layout = QHBoxLayout()
        audio_format_layout.addWidget(BodyLabel("默认音频格式："))

        self.audio_format_combo = ComboBox()
        self.audio_format_combo.addItems(["mp3", "aac", "flac", "wav", "ogg", "m4a"])
        self.audio_format_combo.setCurrentText("mp3")
        audio_format_layout.addWidget(self.audio_format_combo)

        audio_format_layout.addStretch()
        audio_layout.addLayout(audio_format_layout)

        # 默认音频质量
        audio_quality_layout = QHBoxLayout()
        audio_quality_layout.addWidget(BodyLabel("默认音频质量："))

        self.audio_quality_combo = ComboBox()
        self.audio_quality_combo.addItems(["64k", "128k", "192k", "256k", "320k"])
        self.audio_quality_combo.setCurrentText("192k")
        audio_quality_layout.addWidget(self.audio_quality_combo)

        audio_quality_layout.addStretch()
        audio_layout.addLayout(audio_quality_layout)

        # 保留原视频文件
        keep_video_layout = QHBoxLayout()
        keep_video_layout.addWidget(BodyLabel("保留原视频文件"))
        keep_video_layout.addStretch()
        self.audio_keep_video_switch = SwitchButton()
        self.audio_keep_video_switch.setChecked(True)
        keep_video_layout.addWidget(self.audio_keep_video_switch)
        audio_layout.addLayout(keep_video_layout)

        # 音频标准化
        normalize_layout = QHBoxLayout()
        normalize_layout.addWidget(BodyLabel("音频标准化"))
        normalize_layout.addStretch()
        self.audio_normalize_switch = SwitchButton()
        self.audio_normalize_switch.setChecked(False)
        normalize_layout.addWidget(self.audio_normalize_switch)
        audio_layout.addLayout(normalize_layout)

        layout.addWidget(audio_card)

        # 保存按钮
        save_btn = PrimaryPushButton(FIF.SAVE, "保存设置")
        save_btn.clicked.connect(self.save_audio_settings)
        layout.addWidget(save_btn)

        layout.addStretch()
        return widget

    def create_about_tab(self) -> QWidget:
        """创建关于选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        # 应用信息卡片
        about_card = CardWidget()
        about_card.setBorderRadius(16)
        about_layout = QVBoxLayout(about_card)
        about_layout.setSpacing(16)
        about_layout.setAlignment(Qt.AlignCenter)

        # 应用图标
        icon = ImageLabel()
        icon_path = self.parent_window.custom_icon_path if self.parent_window and self.parent_window.custom_icon_path else None
        if icon_path and os.path.exists(icon_path):
            icon.setImage(icon_path)
        else:
            icon.setImage(":/qfluentwidgets/images/logo.png")
        icon.setFixedSize(80, 80)
        icon.setBorderRadius(40, 40, 40, 40)
        about_layout.addWidget(icon, 0, Qt.AlignCenter)

        # 应用名称
        app_name = TitleLabel("易下(EDown)")
        app_name.setStyleSheet("font-size: 28px; font-weight: 600;")
        about_layout.addWidget(app_name, 0, Qt.AlignCenter)

        # 版本
        version = BodyLabel("版本 0.1.0")
        version.setStyleSheet("color: #6c757d;")
        about_layout.addWidget(version, 0, Qt.AlignCenter)

        about_layout.addSpacing(20)

        # 作者信息
        author_info = StrongBodyLabel("作者信息")
        about_layout.addWidget(author_info)

        author_name = BodyLabel("作者: GraceFox (HarePhantom)")
        about_layout.addWidget(author_name)

        author_email = BodyLabel("邮箱: 948743980@qq.com")
        about_layout.addWidget(author_email)

        author_bilibili = BodyLabel("哔哩哔哩: https://space.bilibili.com/3546644268190339")
        about_layout.addWidget(author_bilibili)

        author_date = BodyLabel("创建日期: 2026-03-14")
        about_layout.addWidget(author_date)

        about_layout.addSpacing(20)

        # 功能特点
        features_title = StrongBodyLabel("功能特点")
        about_layout.addWidget(features_title)

        features = [
            "• 支持多平台视频下载（YouTube、Bilibili、优酷等）",
            "• 内置FFmpeg视频转换",
            "• 音频提取功能（MP3、AAC、FLAC等）",
            "• 批量处理功能",
            "• 现代化的Fluent Design界面",
            "• 支持自定义应用图标",
        ]

        for feature in features:
            label = BodyLabel(feature)
            about_layout.addWidget(label)

        about_layout.addSpacing(20)

        # 系统信息
        system_title = StrongBodyLabel("系统信息")
        about_layout.addWidget(system_title)

        system_info = [
            f"• 操作系统：{platform.system()} {platform.release()}",
            f"• 架构：{platform.machine()}",
            f"• Python版本：{platform.python_version()}",
        ]

        for info in system_info:
            label = BodyLabel(info)
            about_layout.addWidget(label)

        about_layout.addSpacing(20)

        # 版权信息
        copyright_label = CaptionLabel("© 2026 GraceFox. All rights reserved.")
        copyright_label.setStyleSheet("color: #adb5bd;")
        about_layout.addWidget(copyright_label, 0, Qt.AlignCenter)

        layout.addWidget(about_card)
        layout.addStretch()

        return widget

    # ==================== 图标相关方法 ====================
    def browse_icon_file(self):
        """浏览图标文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图标文件",
            "",
            "图标文件 (*.png *.ico *.svg *.jpg *.jpeg);;所有文件 (*.*)"
        )
        if file_path:
            self.icon_path_input.setText(file_path)
            # 预览图标
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.icon_preview.setPixmap(scaled_pixmap)
                self.icon_preview.setStyleSheet("border: 2px solid #0078d4; border-radius: 24px;")

    def apply_custom_icon(self):
        """应用自定义图标"""
        icon_path = self.icon_path_input.text()
        if not icon_path:
            InfoBar.warning("提示", "请先选择图标文件", parent=self)
            return
        
        if not os.path.exists(icon_path):
            InfoBar.error("错误", "图标文件不存在", parent=self)
            return
        
        # 调用主窗口的设置图标方法
        if self.parent_window and hasattr(self.parent_window, 'set_custom_icon'):
            self.parent_window.set_custom_icon(icon_path)
            self.update_icon_preview()
            InfoBar.success("成功", "图标已应用", parent=self)

    def reset_default_icon(self):
        """恢复默认图标"""
        self.icon_path_input.clear()
        # 恢复默认图标
        if self.parent_window:
            # 清除自定义图标设置
            self.parent_window.custom_icon_path = None
            self.parent_window.set_app_icon()
            self.parent_window.save_settings()
        
        self.update_icon_preview()
        InfoBar.info("图标已恢复", "已恢复为默认图标", parent=self)

    def update_icon_preview(self):
        """更新图标预览"""
        if self.parent_window and hasattr(self.parent_window, 'custom_icon_path') and self.parent_window.custom_icon_path:
            icon_path = self.parent_window.custom_icon_path
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.icon_preview.setPixmap(scaled)
                    self.icon_preview.setStyleSheet("border: 2px solid #28a745; border-radius: 24px;")
                    self.icon_path_input.setText(icon_path)
                    return
        
        # 显示默认图标
        self.icon_preview.clear()
        self.icon_preview.setText("默认")
        self.icon_preview.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 2px solid #e0e0e0;
                border-radius: 24px;
                color: #666;
                qproperty-alignment: AlignCenter;
            }
        """)

    # ==================== 其他辅助方法 ====================
    def browse_dir(self, input_field: LineEdit, title: str):
        """浏览目录"""
        current_dir = input_field.text() or "output"
        dir_path = QFileDialog.getExistingDirectory(self, title, current_dir)
        if dir_path:
            input_field.setText(dir_path)

    def browse_ffmpeg_path(self):
        """浏览FFmpeg路径"""
        current_path = self.ffmpeg_path_input.text()
        if not current_path:
            current_path = "ffmpeg/ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg/ffmpeg"

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择FFmpeg可执行文件",
            current_path,
            "可执行文件 (*.exe);;所有文件 (*.*)" if platform.system() == "Windows" else "所有文件 (*.*)"
        )
        if file_path:
            self.ffmpeg_path_input.setText(file_path)

    def detect_ffmpeg(self):
        """检测FFmpeg"""
        ffmpeg_path = get_ffmpeg_path()
        if ffmpeg_path:
            self.ffmpeg_path_input.setText(ffmpeg_path)
            InfoBar.success("检测成功", f"找到FFmpeg：{ffmpeg_path}", parent=self)
        else:
            InfoBar.error("检测失败", "未找到FFmpeg，请手动指定路径", parent=self)

    def on_theme_changed(self, theme: str):
        """主题改变"""
        InfoBar.info("主题设置", f"切换到{theme}主题", parent=self)

    def load_settings(self):
        """加载设置"""
        try:
            settings_file = Path("output/settings.json")
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                # 通用设置
                self.theme_combo.setCurrentText(settings.get('theme', '浅色'))
                self.lang_combo.setCurrentText(settings.get('language', '中文(简体)'))
                self.auto_start_switch.setChecked(settings.get('auto_start', False))
                self.tray_switch.setChecked(settings.get('show_tray', True))
                self.minimize_tray_switch.setChecked(settings.get('minimize_to_tray', False))
                self.download_dir_input.setText(settings.get('download_dir', 'output'))
                self.convert_dir_input.setText(settings.get('convert_dir', 'output/converted'))
                self.audio_dir_input.setText(settings.get('audio_dir', 'output/audio'))

                # 下载设置
                self.default_quality_combo.setCurrentText(settings.get('default_quality', '最佳质量'))
                self.default_format_combo.setCurrentText(settings.get('default_format', 'mp4'))
                self.auto_convert_switch.setChecked(settings.get('auto_convert', True))
                self.playlist_switch.setChecked(settings.get('download_playlist', False))
                self.subtitle_switch.setChecked(settings.get('download_subtitle', True))
                self.concurrent_spin.setValue(settings.get('concurrent_downloads', 3))
                self.retry_spin.setValue(settings.get('retry_count', 3))
                self.timeout_spin.setValue(settings.get('timeout', 30))

                # 转换设置
                self.convert_format_combo.setCurrentText(settings.get('convert_format', 'mp4'))
                self.convert_video_quality_combo.setCurrentText(settings.get('convert_quality', '原质量'))
                self.convert_keep_original_switch.setChecked(settings.get('keep_original', True))
                self.convert_overwrite_switch.setChecked(settings.get('overwrite_files', False))
                self.ffmpeg_path_input.setText(settings.get('ffmpeg_path', ''))

                # 音频设置
                self.audio_format_combo.setCurrentText(settings.get('audio_format', 'mp3'))
                self.audio_quality_combo.setCurrentText(settings.get('audio_quality', '192k'))
                self.audio_keep_video_switch.setChecked(settings.get('keep_video', True))
                self.audio_normalize_switch.setChecked(settings.get('normalize_audio', False))

        except Exception as e:
            print(f"加载设置失败: {e}")

    def save_general_settings(self):
        """保存通用设置"""
        try:
            settings_dir = Path("output")
            settings_dir.mkdir(exist_ok=True)
            settings_file = settings_dir / "settings.json"

            settings = {}
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

            # 通用设置
            settings.update({
                'theme': self.theme_combo.currentText(),
                'language': self.lang_combo.currentText(),
                'auto_start': self.auto_start_switch.isChecked(),
                'show_tray': self.tray_switch.isChecked(),
                'minimize_to_tray': self.minimize_tray_switch.isChecked(),
                'download_dir': self.download_dir_input.text() or 'output',
                'convert_dir': self.convert_dir_input.text() or 'output/converted',
                'audio_dir': self.audio_dir_input.text() or 'output/audio'
            })

            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)

            InfoBar.success("保存成功", "通用设置已保存", parent=self)

        except Exception as e:
            InfoBar.error("保存失败", str(e), parent=self)

    def save_download_settings(self):
        """保存下载设置"""
        try:
            settings_dir = Path("output")
            settings_dir.mkdir(exist_ok=True)
            settings_file = settings_dir / "settings.json"

            settings = {}
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

            # 下载设置
            settings.update({
                'default_quality': self.default_quality_combo.currentText(),
                'default_format': self.default_format_combo.currentText(),
                'auto_convert': self.auto_convert_switch.isChecked(),
                'download_playlist': self.playlist_switch.isChecked(),
                'download_subtitle': self.subtitle_switch.isChecked(),
                'concurrent_downloads': self.concurrent_spin.value(),
                'retry_count': self.retry_spin.value(),
                'timeout': self.timeout_spin.value()
            })

            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)

            InfoBar.success("保存成功", "下载设置已保存", parent=self)

        except Exception as e:
            InfoBar.error("保存失败", str(e), parent=self)

    def save_convert_settings(self):
        """保存转换设置"""
        try:
            settings_dir = Path("output")
            settings_dir.mkdir(exist_ok=True)
            settings_file = settings_dir / "settings.json"

            settings = {}
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

            # 转换设置
            settings.update({
                'convert_format': self.convert_format_combo.currentText(),
                'convert_quality': self.convert_video_quality_combo.currentText(),
                'keep_original': self.convert_keep_original_switch.isChecked(),
                'overwrite_files': self.convert_overwrite_switch.isChecked(),
                'ffmpeg_path': self.ffmpeg_path_input.text()
            })

            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)

            InfoBar.success("保存成功", "转换设置已保存", parent=self)

        except Exception as e:
            InfoBar.error("保存失败", str(e), parent=self)

    def save_audio_settings(self):
        """保存音频设置"""
        try:
            settings_dir = Path("output")
            settings_dir.mkdir(exist_ok=True)
            settings_file = settings_dir / "settings.json"

            settings = {}
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

            # 音频设置
            settings.update({
                'audio_format': self.audio_format_combo.currentText(),
                'audio_quality': self.audio_quality_combo.currentText(),
                'keep_video': self.audio_keep_video_switch.isChecked(),
                'normalize_audio': self.audio_normalize_switch.isChecked()
            })

            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)

            InfoBar.success("保存成功", "音频设置已保存", parent=self)

        except Exception as e:
            InfoBar.error("保存失败", str(e), parent=self)