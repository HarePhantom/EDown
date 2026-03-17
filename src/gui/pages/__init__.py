# -*- coding: utf-8 -*-

"""
易下(EDown) - 页面模块
======================

包含应用程序的所有页面：
- 首页
- 下载页
- 转换页
- 音频提取页
- 设置页
"""

from .home_page import HomePage
from .download_page import DownloadPage
from .convert_page import ConvertPage
from .audio_page import AudioPage
from .settings_page import SettingsPage

__all__ = ['HomePage', 'DownloadPage', 'ConvertPage', 'AudioPage', 'SettingsPage']