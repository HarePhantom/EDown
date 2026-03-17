# -*- coding: utf-8 -*-

"""
转换页面 - 视频/音频格式转换
===========================

作者: GraceFox
用户名: HarePhantom
创建日期: 2026-03-14

功能:
- 文件选择
- 格式转换参数设置
- 批量转换任务管理
"""

import os
import json
from pathlib import Path
from typing import List, Dict

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QGroupBox
)

from qfluentwidgets import (
    CardWidget, PushButton, PrimaryPushButton, ToolButton,
    BodyLabel, StrongBodyLabel, TitleLabel, CaptionLabel,
    InfoBar, FluentIcon as FIF,
    ComboBox, CheckBox, LineEdit, ScrollArea,
    TableWidget, Slider
)

from src.core.converter import ConverterWorker
from src.core.utils import (
    format_file_size, sanitize_filename, get_ffmpeg_path,
    get_video_format_options, get_audio_format_options
)


class ConvertPage(QWidget):
    """
    转换页面 - 完整版
    
    属性:
        convert_workers: 转换工作线程列表
        file_list: 待转换文件列表
    """

    def __init__(self, parent=None):
        """初始化转换页面"""
        super().__init__(parent)
        self.setObjectName("convert_page")
        
        self.parent_window = parent
        self.convert_workers = []
        self.convert_threads = []
        self.file_list = []

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title = TitleLabel("格式转换")
        title.setStyleSheet("font-size: 24px; font-weight: 600;")
        layout.addWidget(title)

        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background-color: #e0e0e0; }")
        layout.addWidget(splitter)

        # 上半部分：控制面板
        control_widget = self.create_control_panel()
        splitter.addWidget(control_widget)

        # 下半部分：任务列表
        tasks_widget = self.create_tasks_panel()
        splitter.addWidget(tasks_widget)

        splitter.setSizes([500, 250])

    def create_control_panel(self) -> QWidget:
        """创建控制面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 文件选择卡片
        file_card = CardWidget()
        file_card.setBorderRadius(8)
        file_layout = QVBoxLayout(file_card)
        file_layout.setContentsMargins(16, 12, 16, 12)
        file_layout.setSpacing(8)

        # 文件列表
        self.file_table = TableWidget()
        self.file_table.setColumnCount(3)
        self.file_table.setHorizontalHeaderLabels(["文件名", "大小", "状态"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.file_table.setColumnWidth(1, 100)
        self.file_table.setColumnWidth(2, 100)
        self.file_table.setMaximumHeight(200)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        file_layout.addWidget(self.file_table)

        # 文件操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        add_file_btn = PushButton(FIF.ADD, "添加文件")
        add_file_btn.clicked.connect(self.add_files)
        btn_layout.addWidget(add_file_btn)

        add_folder_btn = PushButton(FIF.FOLDER, "添加文件夹")
        add_folder_btn.clicked.connect(self.add_folder)
        btn_layout.addWidget(add_folder_btn)

        clear_btn = PushButton(FIF.DELETE, "清空列表")
        clear_btn.clicked.connect(self.clear_file_list)
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        file_layout.addLayout(btn_layout)

        layout.addWidget(file_card)

        # 设置卡片
        settings_card = CardWidget()
        settings_card.setBorderRadius(8)
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setContentsMargins(16, 12, 16, 12)
        settings_layout.setSpacing(12)

        # 输出格式
        format_layout = QHBoxLayout()
        format_layout.addWidget(BodyLabel("输出格式:"), 0)
        self.output_format_combo = ComboBox()
        video_formats = list(get_video_format_options().keys())
        audio_formats = list(get_audio_format_options().keys())
        # 只添加字符串
        for fmt in video_formats + audio_formats:
            self.output_format_combo.addItem(fmt)
        self.output_format_combo.setCurrentText("mp4")
        self.output_format_combo.currentTextChanged.connect(self.on_format_changed)
        format_layout.addWidget(self.output_format_combo, 1)
        settings_layout.addLayout(format_layout)

        # 输出目录
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(BodyLabel("输出目录:"), 0)
        self.output_dir_input = LineEdit()
        self.output_dir_input.setReadOnly(True)
        dir_layout.addWidget(self.output_dir_input, 1)
        browse_btn = ToolButton(FIF.FOLDER)
        browse_btn.clicked.connect(self.browse_output_dir)
        dir_layout.addWidget(browse_btn)
        settings_layout.addLayout(dir_layout)

        # 视频质量设置
        video_group = QGroupBox("视频质量设置")
        video_layout = QVBoxLayout(video_group)
        video_layout.setSpacing(8)

        # 分辨率
        res_layout = QHBoxLayout()
        res_layout.addWidget(BodyLabel("分辨率:"))
        self.video_quality_combo = ComboBox()
        qualities = ["原质量", "1080p", "720p", "480p", "360p"]
        for q in qualities:
            self.video_quality_combo.addItem(q)
        self.video_quality_combo.setCurrentText("原质量")
        res_layout.addWidget(self.video_quality_combo)
        video_layout.addLayout(res_layout)

        # CRF 质量滑块
        crf_layout = QVBoxLayout()
        crf_layout.setSpacing(4)
        
        crf_header = QHBoxLayout()
        crf_header.addWidget(BodyLabel("CRF 质量参数:"))
        self.crf_value_label = BodyLabel("23 (标准质量)")
        self.crf_value_label.setStyleSheet("color: #666;")
        crf_header.addStretch()
        crf_header.addWidget(self.crf_value_label)
        crf_layout.addLayout(crf_header)

        self.crf_slider = Slider(Qt.Horizontal)
        self.crf_slider.setRange(0, 51)
        self.crf_slider.setValue(23)
        self.crf_slider.valueChanged.connect(self.on_crf_changed)
        crf_layout.addWidget(self.crf_slider)

        # CRF 说明
        crf_info = CaptionLabel(
            "CRF值越小质量越高，文件越大\n"
            "• 0-18: 视觉无损\n"
            "• 19-22: 高质量\n"
            "• 23-28: 标准质量\n"
            "• 29-35: 低质量"
        )
        crf_info.setStyleSheet("color: #888; padding: 4px;")
        crf_info.setWordWrap(True)
        crf_layout.addWidget(crf_info)

        video_layout.addLayout(crf_layout)

        settings_layout.addWidget(video_group)

        # 音频设置
        self.audio_group = QGroupBox("音频设置")
        audio_layout = QVBoxLayout(self.audio_group)
        audio_layout.setSpacing(8)

        # 比特率
        bitrate_layout = QHBoxLayout()
        bitrate_layout.addWidget(BodyLabel("比特率:"))
        self.audio_bitrate_combo = ComboBox()
        bitrates = ["64k", "128k", "192k", "256k", "320k"]
        for br in bitrates:
            self.audio_bitrate_combo.addItem(br)
        self.audio_bitrate_combo.setCurrentText("192k")
        bitrate_layout.addWidget(self.audio_bitrate_combo)
        audio_layout.addLayout(bitrate_layout)

        # 采样率
        sample_layout = QHBoxLayout()
        sample_layout.addWidget(BodyLabel("采样率:"))
        self.audio_sample_combo = ComboBox()
        samples = ["44100", "48000", "96000"]
        for s in samples:
            self.audio_sample_combo.addItem(s)
        self.audio_sample_combo.setCurrentText("44100")
        sample_layout.addWidget(self.audio_sample_combo)
        audio_layout.addLayout(sample_layout)

        settings_layout.addWidget(self.audio_group)
        self.audio_group.setVisible(False)

        # 选项
        self.keep_original_check = CheckBox("保留原文件")
        self.keep_original_check.setChecked(True)
        settings_layout.addWidget(self.keep_original_check)

        layout.addWidget(settings_card)

        # FFmpeg状态和转换按钮
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)

        self.ffmpeg_status = BodyLabel("")
        self.ffmpeg_status.setStyleSheet("padding: 4px 8px; border-radius: 4px;")
        bottom_layout.addWidget(self.ffmpeg_status)

        check_ffmpeg_btn = ToolButton(FIF.SYNC)
        check_ffmpeg_btn.setToolTip("重新检查FFmpeg")
        check_ffmpeg_btn.clicked.connect(self.check_ffmpeg)
        bottom_layout.addWidget(check_ffmpeg_btn)

        bottom_layout.addStretch()

        self.convert_btn = PrimaryPushButton(FIF.PLAY, "开始转换")
        self.convert_btn.setFixedWidth(120)
        self.convert_btn.clicked.connect(self.start_convert)
        self.convert_btn.setEnabled(False)
        bottom_layout.addWidget(self.convert_btn)

        layout.addLayout(bottom_layout)

        self.check_ffmpeg()
        return widget

    def create_tasks_panel(self) -> QWidget:
        """创建任务面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.addWidget(StrongBodyLabel("转换任务"))
        header.addStretch()
        
        self.task_stats = CaptionLabel("0 个任务")
        self.task_stats.setStyleSheet("color: #666;")
        header.addWidget(self.task_stats)

        clear_done_btn = ToolButton(FIF.DELETE)
        clear_done_btn.setToolTip("清除已完成任务")
        clear_done_btn.clicked.connect(self.clear_completed_tasks)
        header.addWidget(clear_done_btn)

        layout.addLayout(header)

        scroll = ScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_layout.setSpacing(4)
        self.tasks_layout.addStretch()
        
        scroll.setWidget(self.tasks_container)
        layout.addWidget(scroll)

        return widget

    def on_crf_changed(self, value: int):
        """CRF值变化"""
        if value <= 18:
            quality = "视觉无损"
        elif value <= 22:
            quality = "高质量"
        elif value <= 28:
            quality = "标准质量"
        else:
            quality = "低质量"
        self.crf_value_label.setText(f"{value} ({quality})")

    def add_files(self):
        """添加文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择要转换的文件",
            "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm);;"
            "音频文件 (*.mp3 *.aac *.flac *.wav *.ogg);;"
            "所有文件 (*.*)"
        )
        if files:
            for f in files:
                if f not in [x['path'] for x in self.file_list]:
                    self.file_list.append({
                        'path': f,
                        'name': os.path.basename(f),
                        'size': os.path.getsize(f),
                        'status': '等待中',
                        'progress': 0
                    })
            self.update_file_table()
            self.update_convert_button()

    def add_folder(self):
        """添加文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            exts = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
                   '.mp3', '.aac', '.flac', '.wav', '.ogg']
            for root, _, files in os.walk(folder):
                for f in files:
                    if any(f.lower().endswith(e) for e in exts):
                        path = os.path.join(root, f)
                        if path not in [x['path'] for x in self.file_list]:
                            self.file_list.append({
                                'path': path,
                                'name': os.path.basename(path),
                                'size': os.path.getsize(path),
                                'status': '等待中',
                                'progress': 0
                            })
            self.update_file_table()
            self.update_convert_button()
            InfoBar.success("添加成功", f"已添加 {len(self.file_list)} 个文件", parent=self)

    def update_file_table(self):
        """更新文件表格"""
        self.file_table.setRowCount(len(self.file_list))
        for row, info in enumerate(self.file_list):
            name_item = QTableWidgetItem(info['name'])
            name_item.setToolTip(info['path'])
            self.file_table.setItem(row, 0, name_item)
            
            self.file_table.setItem(row, 1, QTableWidgetItem(format_file_size(info['size'])))
            
            status = info['status']
            if info['progress'] > 0 and info['progress'] < 100:
                status = f"{info['progress']}%"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.file_table.setItem(row, 2, status_item)

    def clear_file_list(self):
        """清空列表"""
        for w in self.convert_workers:
            w.stop()
        self.file_list.clear()
        self.convert_workers.clear()
        self.convert_threads.clear()
        self.update_file_table()
        self.update_convert_button()

    def check_ffmpeg(self) -> bool:
        """检查FFmpeg"""
        path = get_ffmpeg_path()
        if path:
            try:
                import subprocess
                result = subprocess.run([path, '-version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version = result.stdout.split('\n')[0][:40]
                    self.ffmpeg_status.setText(f"✅ {version}")
                    self.ffmpeg_status.setStyleSheet("color: #28a745;")
                    return True
            except Exception:
                pass
        self.ffmpeg_status.setText("❌ FFmpeg 未找到")
        self.ffmpeg_status.setStyleSheet("color: #dc3545;")
        return False

    def on_format_changed(self, fmt: str):
        """格式变化"""
        is_audio = fmt in ['mp3', 'aac', 'flac', 'wav', 'ogg', 'm4a']
        self.audio_group.setVisible(is_audio)

    def browse_output_dir(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录", 
                                                   self.output_dir_input.text() or "output")
        if dir_path:
            self.output_dir_input.setText(dir_path)
            self.save_settings()
            self.update_convert_button()

    def update_convert_button(self):
        """更新按钮状态"""
        enabled = (len(self.file_list) > 0 and 
                  bool(self.output_dir_input.text()) and 
                  self.check_ffmpeg())
        self.convert_btn.setEnabled(enabled)

    def start_convert(self):
        """开始转换"""
        if not self.file_list:
            InfoBar.warning("提示", "请先添加文件", parent=self)
            return

        output_dir = self.output_dir_input.text()
        if not output_dir:
            InfoBar.warning("提示", "请选择输出目录", parent=self)
            return

        os.makedirs(output_dir, exist_ok=True)

        # 重置计数
        self.convert_workers.clear()
        self.convert_threads.clear()

        for info in self.file_list:
            if info['status'] == '等待中':
                self.create_convert_task(info, output_dir)

        self.update_task_stats()
        if self.convert_workers:
            InfoBar.success("开始转换", f"已开始转换 {len(self.convert_workers)} 个文件", parent=self)

    def create_convert_task(self, info: Dict, output_dir: str):
        """创建转换任务"""
        name = os.path.splitext(info['name'])[0]
        safe_name = sanitize_filename(name)
        out_path = os.path.join(output_dir, f"{safe_name}.{self.output_format_combo.currentText()}")

        counter = 1
        while os.path.exists(out_path):
            out_path = os.path.join(output_dir, f"{safe_name}_{counter}.{self.output_format_combo.currentText()}")
            counter += 1

        info['status'] = '转换中'
        info['output'] = out_path
        self.update_file_table()

        worker = ConverterWorker(
            info['path'], out_path,
            self.output_format_combo.currentText(),
            self.video_quality_combo.currentText(),
            self.audio_bitrate_combo.currentText(),
            self.audio_sample_combo.currentText(),
            self.keep_original_check.isChecked(),
            self.crf_slider.value()
        )

        thread = QThread()
        worker.moveToThread(thread)

        worker.progress_signal.connect(lambda v, m: self.on_progress(info, v))
        worker.log_signal.connect(lambda m: print(f"[转换] {m}"))
        worker.finished_signal.connect(lambda s, p, m: self.on_finished(info, s, m))
        worker.finished_signal.connect(lambda: self.cleanup(worker, thread))

        thread.started.connect(worker.run)
        thread.start()

        self.convert_workers.append(worker)
        self.convert_threads.append(thread)

    def on_progress(self, info: Dict, value: int):
        """进度更新"""
        info['progress'] = value
        self.update_file_table()

    def on_finished(self, info: Dict, success: bool, msg: str):
        """完成回调"""
        info['status'] = '完成' if success else '失败'
        info['progress'] = 100 if success else 0
        self.update_file_table()
        self.update_task_stats()
        
        if success:
            InfoBar.success("转换完成", f"{info['name']} 转换成功", parent=self)
        else:
            InfoBar.error("转换失败", msg, parent=self)

    def cleanup(self, worker, thread):
        """清理线程"""
        if worker in self.convert_workers:
            self.convert_workers.remove(worker)
        if thread in self.convert_threads:
            self.convert_threads.remove(thread)
            thread.quit()
            thread.wait()

    def update_task_stats(self):
        """更新统计"""
        total = len(self.file_list)
        done = sum(1 for f in self.file_list if f['status'] == '完成')
        self.task_stats.setText(f"{done}/{total} 完成")

    def clear_completed_tasks(self):
        """清除已完成任务"""
        before = len(self.file_list)
        self.file_list = [f for f in self.file_list if f['status'] not in ['完成', '失败']]
        after = len(self.file_list)
        self.update_file_table()
        self.update_task_stats()
        if before - after > 0:
            InfoBar.info("清理完成", f"已清除 {before - after} 个已完成任务", parent=self)

    def load_settings(self):
        """加载设置"""
        try:
            f = Path("output/settings.json")
            if f.exists():
                with open(f) as fp:
                    s = json.load(fp)
                    self.output_dir_input.setText(s.get('convert_dir', 'output/converted'))
                    if 'crf_value' in s:
                        self.crf_slider.setValue(s['crf_value'])
        except Exception:
            self.output_dir_input.setText("output/converted")

    def save_settings(self):
        """保存设置"""
        try:
            Path("output").mkdir(exist_ok=True)
            with open("output/settings.json", 'r+') as f:
                s = json.load(f)
                s['convert_dir'] = self.output_dir_input.text()
                s['crf_value'] = self.crf_slider.value()
                f.seek(0)
                json.dump(s, f, indent=2)
        except Exception:
            pass