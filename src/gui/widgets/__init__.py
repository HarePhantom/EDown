# -*- coding: utf-8 -*-

"""
易下(EDown) - 自定义控件模块
============================

包含应用程序的自定义控件：
- 下载任务卡片
- 统计卡片
"""

from .download_card import DownloadCard
from .statistic_card import StatisticCard

__all__ = ['DownloadCard', 'StatisticCard']