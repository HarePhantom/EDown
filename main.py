#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
易下(EDown) - 视频下载工具主入口
=================================

作者: GraceFox
用户名: HarePhantom
创建日期: 2026-03-14
联系方式: 948743980@qq.com
哔哩哔哩: https://space.bilibili.com/3546644268190339

版本: 0.1.0
描述: 基于Fluent Design的多平台视频下载、转换和音频提取工具
"""

import sys
import os

# 启用高DPI支持
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

# 设置高DPI支持，确保界面在高分辨率屏幕上正确显示
QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

# 添加项目根目录到Python路径，确保模块导入正常
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.gui.main_window import FluentVideoDownloaderApp


def main():
    """
    应用程序主函数
    - 初始化QApplication
    - 设置应用元信息
    - 加载应用图标
    - 创建并显示主窗口
    """
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("易下(EDown)")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("GraceFox")
    app.setOrganizationDomain("edown.gracefox.com")
    
    # 设置默认应用图标
    icon_paths = [
        "resources/icons/logo.ico",
        "resources/icons/logo.png",
        "resources/icons/logo.svg",
    ]
    
    for path in icon_paths:
        if os.path.exists(path):
            icon = QIcon(path)
            if not icon.isNull():
                app.setWindowIcon(icon)
                break
    
    # 创建并显示主窗口
    window = FluentVideoDownloaderApp()
    window.show()
    
    # 进入事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()