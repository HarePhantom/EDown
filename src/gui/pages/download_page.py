# -*- coding: utf-8 -*-

"""
下载页面 - 视频下载功能
=======================

作者: GraceFox
用户名: HarePhantom
创建日期: 2026-03-14

功能:
- URL输入和分析
- 格式选择
- 下载任务管理
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import timedelta

from PySide6.QtCore import Qt, QThread, Signal, QObject, QUrl, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFileDialog, QApplication, QLabel
)
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from qfluentwidgets import (
    PushButton, PrimaryPushButton, ToolButton,
    BodyLabel, StrongBodyLabel, CaptionLabel,
    InfoBar, FluentIcon as FIF,
    ComboBox, LineEdit, ScrollArea,
    SimpleCardWidget,CheckBox
)

from src.core.downloader import DownloadWorker
from src.core.utils import (
    get_formats_for_url, sanitize_filename, format_file_size, is_supported_url
)
from src.gui.widgets import DownloadCard
from src.gui.dialogs import FormatSelectDialog


class VideoInfoWorker(QObject):
    """
    视频信息获取工作线程
    
    信号:
        finished: 完成信号，返回视频信息
        error: 错误信号，返回错误信息
    """
    
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, url: str):
        super().__init__()
        self.url = url
        
    def run(self):
        """执行获取任务"""
        try:
            result = get_formats_for_url(self.url)
            if result:
                self.finished.emit(result)
            else:
                self.error.emit("无法获取视频信息，请检查URL是否正确")
        except Exception as e:
            self.error.emit(str(e))


class DownloadPage(QWidget):
    """
    下载页面 - 视频下载主界面
    
    属性:
        download_workers: 下载工作线程列表
        video_info: 视频信息
        available_formats: 可用格式列表
        selected_format_id: 选中的格式ID
    """

    # 定义格式类型常量
    FORMAT_TYPE_BEST = "best"
    FORMAT_TYPE_VIDEO = "video"
    FORMAT_TYPE_AUDIO = "audio"
    FORMAT_TYPE_SEPARATOR = "separator"

    def __init__(self, parent=None):
        """初始化下载页面"""
        super().__init__(parent)
        self.setObjectName("download_page")
        
        self.parent_window = parent
        
        # 数据
        self.download_workers = []
        self.download_threads = []
        self.video_info = None
        self.available_formats = []  # 存储原始格式数据
        self.formatted_formats = []  # 存储格式化后的显示文本
        self.info_thread = None
        self.info_worker = None
        self.selected_format_id = None  # 存储选中的格式ID
        
        # 网络
        self.network_manager = QNetworkAccessManager()

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background-color: #e0e0e0; }")

        # 上半部分：控制面板
        control_widget = self.create_control_panel()
        splitter.addWidget(control_widget)

        # 下半部分：任务列表
        tasks_widget = self.create_tasks_panel()
        splitter.addWidget(tasks_widget)

        # 设置分割比例
        splitter.setSizes([500, 300])

        layout.addWidget(splitter)

    def create_control_panel(self) -> QWidget:
        """创建控制面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # URL输入卡片
        url_card = self.create_url_card()
        layout.addWidget(url_card)

        # 视频信息卡片
        self.info_card = self.create_info_card()
        layout.addWidget(self.info_card)
        self.info_card.hide()

        # 下载设置卡片
        settings_card = self.create_settings_card()
        layout.addWidget(settings_card)

        # 下载按钮
        self.download_btn = PrimaryPushButton(FIF.DOWNLOAD, "开始下载")
        self.download_btn.setFixedHeight(44)
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setEnabled(False)
        layout.addWidget(self.download_btn)

        layout.addStretch()
        return widget

    def create_url_card(self) -> QWidget:
        """创建URL输入卡片"""
        card = SimpleCardWidget()
        card.setBorderRadius(8)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 标题
        title = StrongBodyLabel("视频链接")
        title.setStyleSheet("font-size: 16px;")
        layout.addWidget(title)

        # 输入区域
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.url_input = LineEdit()
        self.url_input.setPlaceholderText("粘贴视频链接 (支持YouTube、Bilibili、优酷等)")
        self.url_input.setClearButtonEnabled(True)
        self.url_input.textChanged.connect(self.on_url_changed)
        self.url_input.returnPressed.connect(self.analyze_video)
        input_layout.addWidget(self.url_input)

        paste_btn = ToolButton(FIF.PASTE)
        paste_btn.setToolTip("粘贴链接")
        paste_btn.clicked.connect(self.paste_url)
        input_layout.addWidget(paste_btn)

        self.analyze_btn = PrimaryPushButton(FIF.SEARCH, "分析")
        self.analyze_btn.clicked.connect(self.analyze_video)
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setFixedWidth(80)
        input_layout.addWidget(self.analyze_btn)

        layout.addLayout(input_layout)

        return card

    def create_info_card(self) -> QWidget:
        """创建视频信息卡片"""
        card = SimpleCardWidget()
        card.setBorderRadius(8)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 缩略图
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(160, 90)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
        """)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setText("无缩略图")
        layout.addWidget(self.thumbnail_label)

        # 信息区域
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        self.video_title = StrongBodyLabel("")
        self.video_title.setWordWrap(True)
        info_layout.addWidget(self.video_title)

        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(16)

        self.video_duration = CaptionLabel("")
        self.video_duration.setStyleSheet("color: #666;")
        meta_layout.addWidget(self.video_duration)

        self.video_uploader = CaptionLabel("")
        self.video_uploader.setStyleSheet("color: #666;")
        meta_layout.addWidget(self.video_uploader)

        meta_layout.addStretch()
        info_layout.addLayout(meta_layout)

        self.video_size = CaptionLabel("")
        self.video_size.setStyleSheet("color: #666;")
        info_layout.addWidget(self.video_size)

        layout.addLayout(info_layout)
        layout.addStretch()

        return card

    def create_settings_card(self) -> QWidget:
        """创建设置卡片"""
        card = SimpleCardWidget()
        card.setBorderRadius(8)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title = StrongBodyLabel("下载设置")
        title.setStyleSheet("font-size: 16px;")
        layout.addWidget(title)

        # 输出目录
        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(8)

        dir_label = BodyLabel("输出目录:")
        dir_label.setFixedWidth(80)
        dir_layout.addWidget(dir_label)

        self.output_dir_input = LineEdit()
        self.output_dir_input.setPlaceholderText("选择输出目录")
        self.output_dir_input.setReadOnly(True)
        dir_layout.addWidget(self.output_dir_input)

        browse_btn = ToolButton(FIF.FOLDER)
        browse_btn.setToolTip("浏览目录")
        browse_btn.clicked.connect(self.browse_output_dir)
        dir_layout.addWidget(browse_btn)

        layout.addLayout(dir_layout)

        # 格式选择
        format_layout = QHBoxLayout()
        format_layout.setSpacing(8)

        format_label = BodyLabel("视频格式:")
        format_label.setFixedWidth(80)
        format_layout.addWidget(format_label)

        self.format_combo = ComboBox()
        self.format_combo.setPlaceholderText("请先分析视频")
        self.format_combo.setEnabled(False)
        self.format_combo.currentIndexChanged.connect(self.on_format_selected)
        format_layout.addWidget(self.format_combo, 1)

        self.select_format_btn = PushButton("详细选择...")
        self.select_format_btn.clicked.connect(self.show_format_dialog)
        self.select_format_btn.setEnabled(False)
        format_layout.addWidget(self.select_format_btn)

        layout.addLayout(format_layout)

        # 自动转换
        self.auto_convert_check = CheckBox("下载后自动转换为MP4格式")
        self.auto_convert_check.setChecked(True)
        layout.addWidget(self.auto_convert_check)

        return card

    def create_tasks_panel(self) -> QWidget:
        """创建任务面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 标题栏
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        title = StrongBodyLabel("下载任务")
        title.setStyleSheet("font-size: 16px;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # 统计信息
        self.task_count_label = CaptionLabel("0 个任务")
        self.task_count_label.setStyleSheet("color: #666;")
        header_layout.addWidget(self.task_count_label)

        # 清除按钮
        clear_btn = ToolButton(FIF.DELETE)
        clear_btn.setToolTip("清除已完成任务")
        clear_btn.clicked.connect(self.clear_completed_tasks)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # 任务列表滚动区域
        scroll = ScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_layout.setSpacing(8)
        self.tasks_layout.addStretch()

        scroll.setWidget(self.tasks_container)
        layout.addWidget(scroll)

        return widget

    def set_url(self, url: str):
        """设置URL"""
        self.url_input.setText(url)
        self.on_url_changed(url)

    def analyze(self):
        """分析视频（外部调用）"""
        self.analyze_video()

    def paste_url(self):
        """粘贴URL"""
        try:
            clipboard = QApplication.clipboard()
            url = clipboard.text().strip()
            if url:
                self.url_input.setText(url)
                self.on_url_changed(url)
                QTimer.singleShot(100, self.analyze_video)
        except Exception as e:
            InfoBar.error("粘贴失败", str(e), parent=self)

    def on_url_changed(self, text: str):
        """URL变化处理"""
        text = text.strip()
        self.analyze_btn.setEnabled(bool(text) and is_supported_url(text))
        self.video_info = None
        self.available_formats = []
        self.formatted_formats = []
        self.selected_format_id = None
        self.info_card.hide()
        self.format_combo.clear()
        self.format_combo.setEnabled(False)
        self.select_format_btn.setEnabled(False)
        self.update_download_button()

    def browse_output_dir(self):
        """浏览输出目录"""
        current_dir = self.output_dir_input.text() or "output"
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录", current_dir)
        if dir_path:
            self.output_dir_input.setText(dir_path)
            self.save_settings()
            self.update_download_button()

    def update_download_button(self):
        """更新下载按钮状态"""
        has_url = bool(self.url_input.text().strip())
        has_output = bool(self.output_dir_input.text())
        has_format = self.selected_format_id is not None
        self.download_btn.setEnabled(has_url and has_output and has_format)

    def on_format_selected(self, index: int):
        """格式选择变化"""
        if 0 <= index < len(self.formatted_formats):
            fmt_data = self.formatted_formats[index]
            if fmt_data['type'] != self.FORMAT_TYPE_SEPARATOR:
                self.selected_format_id = fmt_data['id']
        self.update_download_button()

    def analyze_video(self):
        """分析视频"""
        url = self.url_input.text().strip()
        if not url:
            InfoBar.warning("提示", "请输入视频链接", parent=self)
            return

        if not is_supported_url(url):
            InfoBar.warning("提示", "不支持的网站，请检查链接", parent=self)
            return

        # 更新UI状态
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setText("分析中...")
        self.format_combo.setPlaceholderText("正在获取格式列表...")
        self.select_format_btn.setEnabled(False)
        self.info_card.hide()

        # 创建工作线程
        self.info_thread = QThread()
        self.info_worker = VideoInfoWorker(url)
        self.info_worker.moveToThread(self.info_thread)

        self.info_worker.finished.connect(self.on_video_info_ready)
        self.info_worker.error.connect(self.on_video_info_error)
        self.info_worker.finished.connect(self.info_thread.quit)
        self.info_worker.error.connect(self.info_thread.quit)
        self.info_worker.finished.connect(self.info_worker.deleteLater)
        self.info_worker.error.connect(self.info_worker.deleteLater)
        self.info_thread.finished.connect(self.info_thread.deleteLater)

        self.info_thread.started.connect(self.info_worker.run)
        self.info_thread.start()

    def on_video_info_ready(self, info: Dict):
        """视频信息获取完成"""
        self.video_info = info
        self.available_formats = info.get('formats', [])

        # 更新视频信息
        self.video_title.setText(f"📹 {info.get('title', '未知标题')}")

        duration = info.get('duration', 0)
        if duration:
            duration_str = str(timedelta(seconds=int(duration)))
            self.video_duration.setText(f"⏱️ {duration_str}")
        else:
            self.video_duration.setText("⏱️ 未知")

        uploader = info.get('uploader', info.get('site', '未知'))
        self.video_uploader.setText(f"👤 {uploader}")

        # 计算总大小
        total_size = 0
        for fmt in self.available_formats:
            size = fmt.get('filesize', 0)
            if size:
                total_size = max(total_size, size)
        if total_size:
            self.video_size.setText(f"💾 约 {format_file_size(total_size)}")

        # 下载缩略图
        thumbnail_url = info.get('thumbnail')
        if thumbnail_url:
            self.download_thumbnail(thumbnail_url)

        self.info_card.show()

        # 更新格式列表
        self.format_combo.clear()
        self.formatted_formats = []

        # 按类型分组
        best_formats = []
        video_formats = []
        audio_formats = []

        for fmt in self.available_formats:
            if fmt.get('is_best'):
                best_formats.append(fmt)
            elif fmt.get('format_type') in ['video+audio', 'combined']:
                video_formats.append(fmt)
            elif fmt.get('format_type') == 'audio':
                audio_formats.append(fmt)

        # 添加最佳格式
        for fmt in best_formats:
            text = fmt.get('format_name', fmt.get('format_id', '未知格式'))
            self.format_combo.addItem(text)
            self.formatted_formats.append({
                'id': fmt.get('format_id'),
                'type': self.FORMAT_TYPE_BEST,
                'data': fmt
            })

        # 添加视频格式
        if video_formats:
            self.format_combo.addItem("─── 视频格式 ───")
            self.formatted_formats.append({
                'id': None,
                'type': self.FORMAT_TYPE_SEPARATOR,
                'data': None
            })
            
            # 按分辨率排序
            video_formats.sort(key=lambda x: x.get('height', 0) or 0, reverse=True)
            for fmt in video_formats:
                text = fmt.get('format_name', fmt.get('format_id', '未知格式'))
                self.format_combo.addItem(text)
                self.formatted_formats.append({
                    'id': fmt.get('format_id'),
                    'type': self.FORMAT_TYPE_VIDEO,
                    'data': fmt
                })

        # 添加音频格式
        if audio_formats:
            self.format_combo.addItem("─── 音频格式 ───")
            self.formatted_formats.append({
                'id': None,
                'type': self.FORMAT_TYPE_SEPARATOR,
                'data': None
            })
            
            for fmt in audio_formats:
                text = fmt.get('format_name', fmt.get('format_id', '未知格式'))
                self.format_combo.addItem(text)
                self.formatted_formats.append({
                    'id': fmt.get('format_id'),
                    'type': self.FORMAT_TYPE_AUDIO,
                    'data': fmt
                })

        self.format_combo.setEnabled(True)
        self.select_format_btn.setEnabled(True)

        if self.formatted_formats:
            # 默认选择第一个非分隔符的格式
            for i, fmt in enumerate(self.formatted_formats):
                if fmt['type'] != self.FORMAT_TYPE_SEPARATOR:
                    self.format_combo.setCurrentIndex(i)
                    self.selected_format_id = fmt['id']
                    break

        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("分析")
        self.update_download_button()

        valid_count = len([f for f in self.available_formats if f.get('format_id')])
        InfoBar.success("分析完成", f"找到 {valid_count} 种格式", parent=self)

    def on_video_info_error(self, error_msg: str):
        """视频信息获取失败"""
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("分析")
        self.format_combo.setPlaceholderText("分析失败")
        InfoBar.error("分析失败", error_msg, parent=self)

    def download_thumbnail(self, url: str):
        """下载缩略图"""
        request = QNetworkRequest(QUrl(url))
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self.on_thumbnail_downloaded(reply))

    def on_thumbnail_downloaded(self, reply: QNetworkReply):
        """缩略图下载完成"""
        if reply.error() == QNetworkReply.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                scaled = pixmap.scaled(160, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.thumbnail_label.setPixmap(scaled)
                self.thumbnail_label.setText("")
        reply.deleteLater()

    def show_format_dialog(self):
        """显示格式选择对话框"""
        if not self.available_formats:
            InfoBar.warning("提示", "没有可用格式", parent=self)
            return

        dialog_formats = []
        for fmt in self.available_formats:
            if fmt.get('format_id'):
                dialog_formats.append({
                    'id': fmt.get('format_id'),
                    'quality': fmt.get('quality', '未知'),
                    'video_profile': fmt.get('vcodec', ''),
                    'audio_profile': fmt.get('acodec', ''),
                    'size': fmt.get('filesize', 0),
                    'container': fmt.get('ext', '')
                })

        dialog = FormatSelectDialog(dialog_formats, self)
        if dialog.exec():
            selected_id = dialog.get_selected_format()
            if selected_id:
                # 在格式列表中查找对应的索引
                for i, fmt in enumerate(self.formatted_formats):
                    if fmt['id'] == selected_id:
                        self.format_combo.setCurrentIndex(i)
                        self.selected_format_id = selected_id
                        break

    def get_selected_format_data(self) -> Optional[Dict]:
        """获取选中的格式数据"""
        if self.selected_format_id is None:
            return None
        
        for fmt in self.available_formats:
            if fmt.get('format_id') == self.selected_format_id:
                return fmt
        return None

    def start_download(self):
        """开始下载"""
        url = self.url_input.text().strip()
        output_dir = self.output_dir_input.text()

        if not url or not output_dir:
            return

        selected_format = self.get_selected_format_data()
        if not selected_format:
            InfoBar.warning("提示", "请选择视频格式", parent=self)
            return

        format_id = selected_format.get('format_id')
        format_type = selected_format.get('format_type', 'combined')
        title = self.video_info.get('title', '未知视频') if self.video_info else '未知视频'

        # 创建下载卡片
        card = DownloadCard(url, sanitize_filename(title))
        self.tasks_layout.insertWidget(self.tasks_layout.count() - 1, card)

        # 创建工作线程
        worker = DownloadWorker(
            url=url,
            output_dir=output_dir,
            format_id=format_id,
            auto_convert=self.auto_convert_check.isChecked(),
            convert_to="mp4" if format_type != 'audio' else "mp3",
            audio_bitrate="192k"
        )

        thread = QThread()
        worker.moveToThread(thread)

        # 连接信号
        worker.progress_signal.connect(card.update_progress)
        worker.log_signal.connect(self.on_download_log)
        worker.finished_signal.connect(
            lambda success, path, msg: self.on_download_finished(card, success, path, msg)
        )
        worker.finished_signal.connect(lambda: self.cleanup_worker(worker, thread))

        thread.started.connect(worker.run)
        thread.start()

        self.download_workers.append(worker)
        self.download_threads.append(thread)

        if self.parent_window:
            self.parent_window.download_count += 1

        self.update_task_count()
        InfoBar.info("开始下载", f"已开始下载: {title}", parent=self)

    def on_download_log(self, message: str):
        """下载日志"""
        print(f"[下载] {message}")

    def on_download_finished(self, card: DownloadCard, success: bool, path: str, message: str):
        """下载完成"""
        if success:
            card.update_progress(100, "下载完成")
            InfoBar.success("下载完成", message, parent=self)
        else:
            card.update_progress(0, f"失败: {message}")
            InfoBar.error("下载失败", message, parent=self)
        self.update_task_count()

    def cleanup_worker(self, worker, thread):
        """清理工作线程"""
        if worker in self.download_workers:
            self.download_workers.remove(worker)
        if thread in self.download_threads:
            self.download_threads.remove(thread)
            thread.quit()
            thread.wait()

    def update_task_count(self):
        """更新任务计数"""
        count = len(self.download_workers)
        self.task_count_label.setText(f"{count} 个任务")

    def clear_completed_tasks(self):
        """清除已完成的任务"""
        removed = 0
        for i in range(self.tasks_layout.count() - 1, -1, -1):
            item = self.tasks_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'status') and widget.status in ['已完成', '失败', '已取消']:
                    widget.deleteLater()
                    self.tasks_layout.removeItem(item)
                    removed += 1

        if removed > 0:
            InfoBar.success("清理完成", f"已清除 {removed} 个任务", parent=self)

    def load_settings(self):
        """加载设置"""
        try:
            settings_file = Path("output/settings.json")
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    output_dir = settings.get('download_dir', 'output')
                    self.output_dir_input.setText(output_dir)
            else:
                self.output_dir_input.setText("output")
        except Exception:
            self.output_dir_input.setText("output")

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

            settings['download_dir'] = self.output_dir_input.text() or 'output'

            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置失败: {e}")