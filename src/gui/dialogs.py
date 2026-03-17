# -*- coding: utf-8 -*-

"""
对话框模块 - 格式选择对话框
==========================

作者: GraceFox
用户名: HarePhantom
创建日期: 2026-03-14
"""

from typing import List, Dict, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QPushButton, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


def format_size(size):
    """格式化文件大小"""
    if not size:
        return '未知'
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"


class FormatSelectDialog(QDialog):
    """
    格式选择对话框 - 用于选择视频下载格式
    
    属性:
        selected_format: 选中的格式ID
    """

    def __init__(self, formats: List[Dict], parent=None):
        """
        初始化格式选择对话框
        
        Args:
            formats: 格式列表，每个格式包含id、quality、video_profile等信息
            parent: 父窗口
        """
        super().__init__(parent)
        self.formats = formats
        self.selected_format = None
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("选择视频格式")
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title = QLabel("请选择要下载的格式：")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #333;")
        layout.addWidget(title)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["格式ID", "清晰度", "视频编码", "音频编码", "文件大小"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)

        # 设置表头样式
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: none;
                border-right: 1px solid #e0e0e0;
                font-weight: bold;
            }
        """)

        # 填充数据
        self.populate_table()

        layout.addWidget(self.table)

        # 提示信息
        info = QLabel(
            "💡 提示：\n"
            "• 通常选择清晰度最高的格式（如1080p、720p）\n"
            "• 格式ID为 'dash' 的是分段视频，下载工具会自动合并\n"
            "• 如果下载失败，可以尝试选择其他格式"
        )
        info.setStyleSheet("""
            QLabel {
                color: #666;
                background-color: #f8f9fa;
                padding: 12px;
                border-radius: 4px;
                font-size: 11px;
            }
        """)
        info.setWordWrap(True)
        layout.addWidget(info)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        button_layout.addStretch()

        self.select_btn = QPushButton("选择并下载")
        self.select_btn.clicked.connect(self.accept)
        self.select_btn.setFixedWidth(120)
        self.select_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        button_layout.addWidget(self.select_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setFixedWidth(80)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        # 默认选择第一行
        if self.table.rowCount() > 0:
            self.table.selectRow(0)

    def populate_table(self):
        """填充表格数据"""
        self.table.setRowCount(len(self.formats))

        for i, fmt in enumerate(self.formats):
            # 格式ID
            id_item = QTableWidgetItem(fmt.get('id', ''))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 0, id_item)

            # 清晰度
            quality_item = QTableWidgetItem(fmt.get('quality', '未知'))
            quality_item.setFlags(quality_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 1, quality_item)

            # 视频编码
            video_item = QTableWidgetItem(fmt.get('video_profile', ''))
            video_item.setFlags(video_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 2, video_item)

            # 音频编码
            audio_item = QTableWidgetItem(fmt.get('audio_profile', ''))
            audio_item.setFlags(audio_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 3, audio_item)

            # 文件大小
            size_item = QTableWidgetItem(format_size(fmt.get('size', 0)))
            size_item.setFlags(size_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 4, size_item)

        # 调整列宽
        self.table.resizeColumnsToContents()

    def get_selected_format(self) -> Optional[str]:
        """
        获取选中的格式ID
        
        Returns:
            Optional[str]: 选中的格式ID，如果没有选中则返回None
        """
        current_row = self.table.currentRow()
        if current_row >= 0:
            return self.table.item(current_row, 0).text()
        return None