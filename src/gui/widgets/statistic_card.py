# -*- coding: utf-8 -*-

"""
统计卡片组件 - 显示统计数据
===========================

作者: GraceFox
用户名: HarePhantom
创建日期: 2026-03-14
"""

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout

from qfluentwidgets import (
    CardWidget, IconWidget, CaptionLabel, StrongBodyLabel
)


class StatisticCard(CardWidget):
    """
    统计卡片 - 现代化设计
    
    属性:
        title: 卡片标题
        value: 显示数值
        icon: 图标
    """

    def __init__(self, title: str, value: str, icon, parent=None):
        """
        初始化统计卡片
        
        Args:
            title: 标题
            value: 初始数值
            icon: 图标
            parent: 父窗口
        """
        super().__init__(parent)
        self.title = title
        self._value = value
        self.icon = icon

        self.init_ui()
        self.setup_animations()

    def init_ui(self):
        """初始化用户界面"""
        self.setBorderRadius(12)
        self.setFixedSize(200, 100)
        
        # 主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # 图标容器
        self.icon_widget = IconWidget(self.icon)
        self.icon_widget.setFixedSize(40, 40)
        self.icon_widget.setStyleSheet("""
            IconWidget {
                color: #0078d4;
                background-color: rgba(0, 120, 212, 0.1);
                border-radius: 20px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.icon_widget)

        # 文字区域
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        self.title_label = CaptionLabel(self.title)
        self.title_label.setStyleSheet("color: #666; font-size: 12px;")
        text_layout.addWidget(self.title_label)

        self.value_label = StrongBodyLabel(self._value)
        self.value_label.setStyleSheet("font-size: 28px; font-weight: 600; color: #333;")
        text_layout.addWidget(self.value_label)

        layout.addLayout(text_layout)
        layout.addStretch()

        # 设置悬停效果
        self.setStyleSheet("""
            StatisticCard {
                background-color: white;
                border: 1px solid #e0e0e0;
            }
            StatisticCard:hover {
                background-color: #f8f9fa;
                border-color: #0078d4;
            }
        """)

    def setup_animations(self):
        """设置动画效果"""
        self.hover_animation = QPropertyAnimation(self, b"pos")
        self.hover_animation.setDuration(200)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)

    def set_value(self, value: str, status: str = "normal"):
        """
        设置数值
        
        Args:
            value: 数值字符串
            status: 状态 (normal, success, warning, error)
        """
        self._value = value
        self.value_label.setText(value)
        
        # 根据状态设置颜色
        colors = {
            "normal": "#333",
            "success": "#28a745",
            "warning": "#ffc107",
            "error": "#dc3545"
        }
        color = colors.get(status, colors["normal"])
        self.value_label.setStyleSheet(f"font-size: 28px; font-weight: 600; color: {color};")

    def enterEvent(self, event):
        """鼠标进入事件"""
        self.icon_widget.setStyleSheet("""
            IconWidget {
                color: white;
                background-color: #0078d4;
                border-radius: 20px;
                padding: 8px;
            }
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.icon_widget.setStyleSheet("""
            IconWidget {
                color: #0078d4;
                background-color: rgba(0, 120, 212, 0.1);
                border-radius: 20px;
                padding: 8px;
            }
        """)
        super().leaveEvent(event)