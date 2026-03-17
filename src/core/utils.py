# -*- coding: utf-8 -*-

"""
工具函数模块 - 提供通用工具函数
===============================

作者: GraceFox
用户名: HarePhantom
创建日期: 2026-03-14

功能:
- 文件路径处理
- 文件名清理
- FFmpeg路径检测
- 视频格式获取
- URL类型判断
"""

import os
import sys
import json
import re
import subprocess
import unicodedata
import platform
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path


def is_frozen() -> bool:
    """
    检查程序是否在打包环境中运行
    
    Returns:
        bool: 如果在打包环境中返回True，否则返回False
    """
    return getattr(sys, 'frozen', False)


def get_resource_path(relative_path: str) -> str:
    """
    获取资源文件的绝对路径，支持打包环境
    
    Args:
        relative_path: 相对路径
        
    Returns:
        str: 资源的绝对路径
    """
    try:
        if is_frozen():
            # 在打包环境中，资源文件在 _MEIPASS 目录下
            base_path = sys._MEIPASS
        else:
            # 在开发环境中，资源文件在当前文件所在目录
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)
    except Exception:
        # 出错时返回原始路径
        return relative_path


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除或替换无效字符，确保文件名在Windows/Linux/macOS下都有效
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的安全文件名
    """
    if not filename:
        return "untitled"

    # 移除前后的空白字符和控制字符
    filename = filename.strip()
    
    # Windows文件名中的非法字符映射表
    replacements = {
        '<': '＜', '>': '＞', ':': '：', '"': '＂',
        '/': '／', '\\': '＼', '|': '｜', '?': '？',
        '*': '＊', '\n': ' ', '\r': ' ', '\t': ' ',
    }

    # 替换非法字符
    for old, new in replacements.items():
        filename = filename.replace(old, new)

    # 移除其他控制字符
    filename = ''.join(char for char in filename if ord(char) >= 32 or char == '\n' or char == '\r')
    
    # Unicode规范化（统一字符编码形式）
    filename = unicodedata.normalize('NFKC', filename)
    
    # 移除文件名末尾的点（Windows不允许）
    filename = filename.rstrip('.')

    # 确保文件名不为空
    if not filename or filename in ['.', '..']:
        filename = "untitled"

    # 限制文件名长度（Windows最大255字符，留出余量）
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        if len(ext) > 20:
            ext = ext[:20]
        filename = name[:200 - len(ext)] + ext

    return filename


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小，将字节转换为人类可读的格式
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        str: 格式化后的文件大小（如 "1.23 MB"）
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_ffmpeg_path() -> Optional[str]:
    """
    获取FFmpeg可执行文件的路径
    搜索顺序：
    1. 环境变量 FFMPEG_PATH
    2. 打包资源目录
    3. 项目目录下的 ffmpeg 文件夹
    4. 系统PATH
    
    Returns:
        Optional[str]: FFmpeg路径，如果未找到则返回None
    """
    # 检查环境变量
    if 'FFMPEG_PATH' in os.environ:
        env_path = os.environ['FFMPEG_PATH']
        if os.path.exists(env_path):
            return env_path

    # 可能的路径列表
    possible_paths = [
        # 打包后的资源路径
        get_resource_path("ffmpeg/ffmpeg.exe"),
        get_resource_path("ffmpeg/ffmpeg"),
        # 当前目录
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg", "ffmpeg.exe"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg", "ffmpeg"),
        # 项目根目录
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ffmpeg", "ffmpeg.exe"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ffmpeg", "ffmpeg"),
        # 当前工作目录
        os.path.join(os.getcwd(), "ffmpeg", "ffmpeg.exe"),
        os.path.join(os.getcwd(), "ffmpeg", "ffmpeg"),
        # 系统PATH
        "ffmpeg.exe",
        "ffmpeg",
    ]

    for path in possible_paths:
        try:
            if os.path.exists(path):
                # 验证是否为可执行文件
                if os.access(path, os.X_OK) or platform.system() == "Windows":
                    return path
        except Exception:
            continue

    # 在系统 PATH 中查找
    try:
        if platform.system() == "Windows":
            result = subprocess.run(["where", "ffmpeg"], capture_output=True, text=True, timeout=5, shell=True)
        else:
            result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            paths = result.stdout.strip().split('\n')
            if paths and paths[0]:
                return paths[0]
    except Exception:
        pass

    return None


def get_audio_bitrate_options() -> Dict[str, str]:
    """
    获取音频比特率选项
    
    Returns:
        Dict[str, str]: 比特率选项字典，键为比特率值，值为显示文本
    """
    return {
        "64k": "64 kbps (低质量)",
        "96k": "96 kbps (中等质量)",
        "128k": "128 kbps (标准质量)",
        "192k": "192 kbps (高质量)",
        "256k": "256 kbps (高保真)",
        "320k": "320 kbps (最佳质量)",
    }


def get_audio_format_options() -> Dict[str, str]:
    """
    获取音频格式选项
    
    Returns:
        Dict[str, str]: 音频格式选项字典，键为格式名，值为显示文本
    """
    return {
        "mp3": "MP3 (最兼容)",
        "aac": "AAC (高质量)",
        "flac": "FLAC (无损)",
        "wav": "WAV (无损)",
        "ogg": "OGG (开源)",
        "m4a": "M4A (苹果格式)",
    }


def get_video_format_options() -> Dict[str, str]:
    """
    获取视频格式选项
    
    Returns:
        Dict[str, str]: 视频格式选项字典，键为格式名，值为显示文本
    """
    return {
        "mp4": "MP4 (最兼容)",
        "avi": "AVI (经典格式)",
        "mkv": "MKV (多轨道)",
        "mov": "MOV (苹果格式)",
        "webm": "WebM (网页格式)",
        "flv": "FLV (Flash视频)",
    }


def get_ytdlp_formats(url: str) -> Optional[Dict[str, Any]]:
    """
    使用yt-dlp获取YouTube等网站的格式列表
    
    Args:
        url: 视频URL
        
    Returns:
        Optional[Dict]: 包含视频信息和格式列表的字典，失败返回None
    """
    try:
        cmd = [
            "yt-dlp",
            "-j",  # JSON输出
            "--no-warnings",
            "--no-playlist",
            url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                formats = []
                
                # 获取视频基本信息
                video_title = data.get('title', '未知标题')
                video_duration = data.get('duration', 0)
                video_uploader = data.get('uploader', '未知上传者')
                video_thumbnail = data.get('thumbnail', '')
                
                # 处理格式列表
                if 'formats' in data:
                    for fmt in data['formats']:
                        format_id = fmt.get('format_id', '')
                        ext = fmt.get('ext', '')
                        height = fmt.get('height', 0)
                        width = fmt.get('width', 0)
                        vcodec = fmt.get('vcodec', 'none')
                        acodec = fmt.get('acodec', 'none')
                        filesize = fmt.get('filesize', 0) or fmt.get('filesize_approx', 0)
                        tbr = fmt.get('tbr', 0)  # 总比特率
                        fps = fmt.get('fps', 0)
                        
                        # 构建格式描述
                        quality = "未知"
                        if height > 0:
                            quality = f"{height}p"
                            if fps > 30:
                                quality += f"{int(fps)}"
                        elif ext in ['mp3', 'm4a', 'aac']:
                            quality = "音频仅"
                        
                        # 构建格式名称
                        format_name = f"{format_id} - {quality}"
                        if ext:
                            format_name += f" [{ext}]"
                        if filesize:
                            format_name += f" [{format_file_size(filesize)}]"
                        
                        # 确定格式类型
                        format_type = "video"
                        if vcodec == 'none' and acodec != 'none':
                            format_type = "audio"
                        elif acodec == 'none' and vcodec != 'none':
                            format_type = "video_only"
                        else:
                            format_type = "video+audio"
                        
                        formats.append({
                            'id': format_id,
                            'format_id': format_id,
                            'ext': ext,
                            'height': height,
                            'width': width,
                            'fps': fps,
                            'vcodec': vcodec,
                            'acodec': acodec,
                            'filesize': filesize,
                            'tbr': tbr,
                            'quality': quality,
                            'format_name': format_name,
                            'format_type': format_type,
                            'note': fmt.get('format_note', '')
                        })
                
                # 添加最佳组合格式
                formats.append({
                    'id': 'best',
                    'format_id': 'best',
                    'ext': 'mp4',
                    'quality': '最佳质量',
                    'format_name': 'best - 最佳质量 [自动选择]',
                    'format_type': 'combined',
                    'is_best': True
                })
                
                formats.append({
                    'id': 'bestaudio',
                    'format_id': 'bestaudio',
                    'ext': 'm4a',
                    'quality': '最佳音频',
                    'format_name': 'bestaudio - 最佳音频 [音频仅]',
                    'format_type': 'audio',
                    'is_best': True
                })
                
                return {
                    'title': video_title,
                    'duration': video_duration,
                    'uploader': video_uploader,
                    'thumbnail': video_thumbnail,
                    'formats': formats
                }
            except json.JSONDecodeError:
                return None
    except Exception as e:
        print(f"yt-dlp格式获取错误: {e}")
        pass

    return None


def get_youget_formats(url: str) -> Optional[Dict[str, Any]]:
    """
    使用you-get获取哔哩哔哩等网站的格式列表
    
    Args:
        url: 视频URL
        
    Returns:
        Optional[Dict]: 包含视频信息和格式列表的字典，失败返回None
    """
    try:
        cmd = ["you-get", "--json", url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                formats = []
                
                video_title = data.get('title', '未知标题')
                video_duration = None
                video_uploader = data.get('site', '未知网站')
                video_thumbnail = None

                if 'streams' in data:
                    for stream_id, stream_info in data['streams'].items():
                        size = stream_info.get('size', 0)
                        container = stream_info.get('container', '')
                        quality = stream_info.get('quality', '未知')
                        video_profile = stream_info.get('video_profile', '')
                        audio_profile = stream_info.get('audio_profile', '')
                        
                        format_name = f"{stream_id} - {quality}"
                        if container:
                            format_name += f" [{container}]"
                        if size:
                            format_name += f" [{format_file_size(size)}]"
                        
                        formats.append({
                            'id': stream_id,
                            'format_id': stream_id,
                            'ext': container,
                            'quality': quality,
                            'filesize': size,
                            'format_name': format_name,
                            'video_profile': video_profile,
                            'audio_profile': audio_profile,
                            'format_type': 'combined'
                        })
                
                # 添加最佳质量选项
                formats.append({
                    'id': 'best',
                    'format_id': 'best',
                    'ext': 'mp4',
                    'quality': '最佳质量',
                    'format_name': 'best - 最佳质量 [自动选择]',
                    'format_type': 'combined',
                    'is_best': True
                })
                
                formats.append({
                    'id': 'bestaudio',
                    'format_id': 'bestaudio',
                    'ext': 'm4a',
                    'quality': '最佳音频',
                    'format_name': 'bestaudio - 最佳音频 [音频仅]',
                    'format_type': 'audio',
                    'is_best': True
                })
                
                return {
                    'title': video_title,
                    'duration': video_duration,
                    'uploader': video_uploader,
                    'thumbnail': video_thumbnail,
                    'formats': formats
                }
            except json.JSONDecodeError:
                return None
    except Exception as e:
        print(f"you-get格式获取错误: {e}")
        pass

    return None


def get_formats_for_url(url: str) -> Optional[Dict[str, Any]]:
    """
    根据URL类型选择合适的工具获取格式列表
    
    Args:
        url: 视频URL
        
    Returns:
        Optional[Dict]: 格式信息字典，失败返回None
    """
    # 先尝试yt-dlp（支持更多网站）
    result = get_ytdlp_formats(url)
    if result:
        return result
    
    # 再尝试you-get
    result = get_youget_formats(url)
    if result:
        return result
    
    return None


def is_youtube_url(url: str) -> bool:
    """
    检查是否为YouTube视频URL
    
    Args:
        url: 视频URL
        
    Returns:
        bool: 如果是YouTube URL返回True，否则返回False
    """
    youtube_patterns = [
        r'youtube\.com',
        r'youtu\.be',
        r'youtube\.com\.br',
        r'youtube\.ca',
        r'youtube\.co\.uk',
        r'youtube\.com\.au',
        r'youtube\.de',
        r'youtube\.es',
        r'youtube\.fr',
        r'youtube\.it',
        r'youtube\.nl',
        r'youtube\.pl',
        r'youtube\.ru',
    ]
    return any(re.search(pattern, url, re.IGNORECASE) for pattern in youtube_patterns)


def is_bilibili_url(url: str) -> bool:
    """
    检查是否为哔哩哔哩视频URL
    
    Args:
        url: 视频URL
        
    Returns:
        bool: 如果是B站URL返回True，否则返回False
    """
    return 'bilibili.com' in url or 'b23.tv' in url


def is_supported_url(url: str) -> bool:
    """
    检查是否为支持的视频网站URL
    
    Args:
        url: 视频URL
        
    Returns:
        bool: 如果是支持的网站URL返回True，否则返回False
    """
    # 常见视频网站域名列表
    supported_domains = [
        'youtube.com', 'youtu.be',
        'bilibili.com', 'b23.tv',
        'v.youku.com', 'v.qq.com', 'v.163.com',
        'iqiyi.com', 'letv.com', 'sohu.com',
        'tudou.com', 'ku6.com', 'acfun.cn',
        'dailymotion.com', 'vimeo.com',
        'twitch.tv', 'facebook.com',
        'twitter.com', 'instagram.com',
        'tiktok.com', 'douyin.com',
        'miaopai.com', 'weibo.com'
    ]
    
    url_lower = url.lower()
    return any(domain in url_lower for domain in supported_domains)