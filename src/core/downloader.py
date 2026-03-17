# -*- coding: utf-8 -*-

"""
下载器模块 - 视频下载和批量转换
==============================

作者: GraceFox
用户名: HarePhantom
创建日期: 2026-03-14

功能:
- 多平台视频下载
- 批量格式转换
- 进度监控
- 取消/暂停功能
"""

import os
import re
import time
import json
import signal
import subprocess
import platform
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from PySide6.QtCore import QObject, Signal, QMutex, QMutexLocker

from src.core.utils import (
    get_ffmpeg_path, sanitize_filename, format_file_size,
    get_formats_for_url, is_youtube_url, is_bilibili_url
)


class DownloadWorker(QObject):
    """
    视频下载工作线程
    
    信号:
        progress_signal: 进度更新信号 (进度百分比, 状态信息)
        log_signal: 日志信息信号 (日志文本)
        finished_signal: 完成信号 (成功标志, 文件路径, 消息)
        file_downloaded_signal: 文件下载完成信号 (文件路径, 文件类型)
        formats_ready_signal: 格式列表就绪信号 (格式列表)
    """
    
    progress_signal = Signal(int, str)  # 进度百分比，状态信息
    log_signal = Signal(str)  # 日志信息
    finished_signal = Signal(bool, str, str)  # success, file_path, message
    file_downloaded_signal = Signal(str, str)  # file_path, file_type
    formats_ready_signal = Signal(list)  # 格式列表

    def __init__(self, url: str, output_dir: str,
                 quality: str = None, auto_convert: bool = False,
                 convert_to: str = "mp4", audio_bitrate: str = "192k",
                 format_id: str = None):
        """
        初始化下载工作线程
        
        Args:
            url: 视频URL
            output_dir: 输出目录
            quality: 视频质量
            auto_convert: 是否自动转换
            convert_to: 转换格式
            audio_bitrate: 音频比特率
            format_id: 指定格式ID
        """
        super().__init__()
        self.url = url
        self.output_dir = output_dir
        self.quality = quality
        self.auto_convert = auto_convert
        self.convert_to = convert_to
        self.audio_bitrate = audio_bitrate
        self.format_id = format_id
        
        # 线程控制
        self._stop_flag = False
        self._pause_flag = False
        self._mutex = QMutex()
        self.process = None
        self.downloaded_file_path = None
        
        # URL类型判断
        self.is_youtube = is_youtube_url(url)
        self.is_bilibili = is_bilibili_url(url)

    def stop(self):
        """停止下载任务"""
        with QMutexLocker(self._mutex):
            self._stop_flag = True
            if self.process:
                try:
                    if platform.system() == "Windows":
                        self.process.terminate()
                    else:
                        self.process.send_signal(signal.SIGINT)
                except Exception:
                    pass

    def pause(self):
        """暂停下载任务"""
        with QMutexLocker(self._mutex):
            self._pause_flag = True

    def resume(self):
        """恢复下载任务"""
        with QMutexLocker(self._mutex):
            self._pause_flag = False

    def _should_stop(self) -> bool:
        """检查是否应该停止"""
        with QMutexLocker(self._mutex):
            return self._stop_flag

    def _should_pause(self) -> bool:
        """检查是否应该暂停"""
        with QMutexLocker(self._mutex):
            return self._pause_flag

    def get_available_formats(self):
        """获取可用格式列表"""
        try:
            formats = get_formats_for_url(self.url)
            if formats and 'formats' in formats:
                self.formats_ready_signal.emit(formats['formats'])
            else:
                self.formats_ready_signal.emit([])
        except Exception as e:
            self.log_signal.emit(f"获取格式列表失败: {e}")
            self.formats_ready_signal.emit([])

    def _clean_url(self, url: str) -> str:
        """
        清理URL，移除追踪参数
        
        Args:
            url: 原始URL
            
        Returns:
            str: 清理后的URL
        """
        try:
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(url)
            cleaned = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
            return cleaned
        except Exception:
            return url

    def _get_bilibili_default_format(self) -> Optional[str]:
        """获取B站免登录可用的默认格式"""
        try:
            cmd = ["you-get", "--json", self.url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding='utf-8')
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if 'streams' in data and data['streams']:
                    preferred_formats = ['dash-flv480-AVC', 'flv480', 'flv360']
                    streams = list(data['streams'].keys())
                    
                    for fmt in preferred_formats:
                        if fmt in streams:
                            return fmt
                    
                    return streams[0]
        except Exception:
            pass
        return None

    def _is_media_file(self, filename: str) -> bool:
        """
        判断是否为媒体文件（视频或音频）
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 如果是媒体文件返回True
        """
        media_exts = [
            '.mp4', '.flv', '.webm', '.mkv', '.avi', '.mov', '.wmv', '.m4v', '.mpg', '.mpeg',
            '.mp3', '.aac', '.flac', '.wav', '.ogg', '.m4a', '.opus'
        ]
        ext = os.path.splitext(filename)[1].lower()
        return ext in media_exts

    def _decode_output(self, data: bytes) -> str:
        """
        解码子进程输出，处理中文编码问题
        
        Args:
            data: 原始字节数据
            
        Returns:
            str: 解码后的字符串
        """
        try:
            # 首先尝试 UTF-8
            return data.decode('utf-8')
        except UnicodeDecodeError:
            try:
                # 如果 UTF-8 失败，尝试 GBK
                return data.decode('gbk')
            except UnicodeDecodeError:
                try:
                    # 尝试忽略错误的编码
                    return data.decode('utf-8', errors='ignore')
                except Exception:
                    # 最后尝试 GBK 忽略错误
                    return data.decode('gbk', errors='ignore')

    def run(self):
        """执行下载任务"""
        try:
            if self._should_stop():
                self.finished_signal.emit(False, "", "下载已取消")
                return

            # 清理URL
            self.url = self._clean_url(self.url)
            
            self.log_signal.emit(f"🎬 开始下载: {self.url}")

            # 创建输出目录
            abs_output_dir = os.path.abspath(self.output_dir)
            os.makedirs(abs_output_dir, exist_ok=True)

            # 构建命令
            cmd_str = ""
            
            if self.is_bilibili:
                default_format = self._get_bilibili_default_format()
                if default_format:
                    cmd_str = f'you-get --format {default_format} --output-dir "{abs_output_dir}" "{self.url}"'
                    self.log_signal.emit(f"📺 B站视频 - 格式: {default_format}")
                else:
                    cmd_str = f'you-get --output-dir "{abs_output_dir}" "{self.url}"'
                    self.log_signal.emit("📺 B站视频")
                
            elif self.is_youtube:
                output_template = os.path.join(abs_output_dir, "%(title)s.%(ext)s")
                if self.format_id:
                    cmd_str = f'yt-dlp -f {self.format_id} -o "{output_template}" "{self.url}"'
                else:
                    cmd_str = f'yt-dlp -f "best[ext=mp4]/best" -o "{output_template}" "{self.url}"'
                self.log_signal.emit("📺 YouTube视频")
                
            else:
                if self.format_id:
                    cmd_str = f'you-get --format {self.format_id} --output-dir "{abs_output_dir}" "{self.url}"'
                elif self.quality and self.quality != "自动":
                    cmd_str = f'you-get --format {self.quality.lower()} --output-dir "{abs_output_dir}" "{self.url}"'
                else:
                    cmd_str = f'you-get --output-dir "{abs_output_dir}" "{self.url}"'
                self.log_signal.emit("📺 视频下载")

            # 启动进程 - 使用文本模式
            self.process = subprocess.Popen(
                cmd_str,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,  # 启用文本模式
                encoding='utf-8',  # 指定 UTF-8 编码
                errors='replace',  # 替换无法解码的字符
                bufsize=1,  # 行缓冲
                shell=True,
                env=os.environ.copy()
            )

            file_saved_path = None
            last_progress = 0

            # 读取输出
            for line in iter(self.process.stdout.readline, ''):
                if self._should_stop():
                    self.process.terminate()
                    self.finished_signal.emit(False, "", "下载已取消")
                    return

                while self._should_pause() and not self._should_stop():
                    time.sleep(0.1)

                if self._should_stop():
                    self.process.terminate()
                    self.finished_signal.emit(False, "", "下载已取消")
                    return

                line = line.strip()
                
                # 解析进度
                progress_match = re.search(r'(\d+(\.\d+)?)%', line)
                if progress_match:
                    try:
                        percent = float(progress_match.group(1))
                        if percent <= 100 and int(percent) != last_progress:
                            last_progress = int(percent)
                            self.progress_signal.emit(last_progress, f"下载中 {last_progress}%")
                    except Exception:
                        pass

                # 检测文件名
                file_patterns = [
                    # 匹配引号内的文件名
                    r'"(.*?\.(mp4|flv|webm|mkv|avi|mov|wmv|m4v|mpg|mpeg|mp3|aac|flac|wav|ogg|m4a))"',
                    # 匹配 "Saved" 后面的文件名
                    r'Saved\s+(.+?\.(mp4|flv|webm|mkv|avi|mov|wmv|m4v|mpg|mpeg|mp3|aac|flac|wav|ogg|m4a))',
                    # 匹配 "Destination" 后面的文件名 (yt-dlp)
                    r'Destination:\s*(.+?\.(mp4|flv|webm|mkv|avi|mov|wmv|m4v|mpg|mpeg|mp3|aac|flac|wav|ogg|m4a))',
                    # 匹配 "Merging" 后面的文件名
                    r'Merging\s+(.+?\.(mp4|flv|webm|mkv|avi|mov|wmv|m4v|mpg|mpeg|mp3|aac|flac|wav|ogg|m4a))',
                    # 匹配 "Downloading" 后面的文件名
                    r'Downloading\s+(.+?\.(mp4|flv|webm|mkv|avi|mov|wmv|m4v|mpg|mpeg|mp3|aac|flac|wav|ogg|m4a))',
                    # 匹配箭头后面的文件名
                    r'→\s+(.+?\.(mp4|flv|webm|mkv|avi|mov|wmv|m4v|mpg|mpeg|mp3|aac|flac|wav|ogg|m4a))',
                    # 匹配一般的文件路径
                    r'([^\\/:*?"<>|\r\n]+\.(mp4|flv|webm|mkv|avi|mov|wmv|m4v|mpg|mpeg|mp3|aac|flac|wav|ogg|m4a))',
                ]

                for pattern in file_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        filename = match.group(1).strip(' "\'')
                        # 清理文件名中的路径分隔符
                        filename = os.path.basename(filename)
                        if self._is_media_file(filename):
                            safe_filename = sanitize_filename(filename)
                            file_saved_path = os.path.join(abs_output_dir, safe_filename)
                            self.downloaded_file_path = file_saved_path
                            self.log_signal.emit(f"📁 检测到文件: {safe_filename}")
                        break

            # 等待进程结束
            return_code = self.process.wait()

            if return_code == 0:
                self.progress_signal.emit(100, "下载完成")
                self.log_signal.emit("✅ 下载完成")

                # 查找下载的文件
                if not file_saved_path or not os.path.exists(file_saved_path):
                    self.log_signal.emit("🔍 正在查找下载的文件...")
                    file_saved_path = self._find_media_file(abs_output_dir)

                if file_saved_path and os.path.exists(file_saved_path):
                    file_size = os.path.getsize(file_saved_path)
                    file_name = os.path.basename(file_saved_path)
                    self.log_signal.emit(f"📁 文件: {file_name} ({format_file_size(file_size)})")

                    file_ext = os.path.splitext(file_saved_path)[1].lower()
                    self.file_downloaded_signal.emit(file_saved_path, file_ext)

                    # 自动转换
                    if self.auto_convert and self._is_media_file(file_saved_path):
                        if self.convert_to == "mp4" and file_ext not in ['.mp4', '.mkv']:
                            self.log_signal.emit("🔄 正在转换格式...")
                            success, converted_file = self._convert_to_mp4(file_saved_path)
                            if success:
                                self.finished_signal.emit(True, converted_file, "下载并转换完成")
                            else:
                                self.finished_signal.emit(True, file_saved_path, "下载完成，但转换失败")
                        elif self.convert_to in ["mp3", "aac", "flac", "wav", "ogg", "m4a"]:
                            self.log_signal.emit("🔄 正在提取音频...")
                            success, converted_file = self._extract_audio(file_saved_path, self.convert_to)
                            if success:
                                self.finished_signal.emit(True, converted_file, "下载并转换完成")
                            else:
                                self.finished_signal.emit(True, file_saved_path, "下载完成，但转换失败")
                        else:
                            self.finished_signal.emit(True, file_saved_path, "下载完成")
                    else:
                        self.finished_signal.emit(True, file_saved_path, "下载完成")
                else:
                    # 列出目录内容以便调试
                    self.log_signal.emit("⚠️ 下载完成但未找到媒体文件")
                    try:
                        files = os.listdir(abs_output_dir)
                        self.log_signal.emit(f"📂 目录中的文件: {', '.join(files[:5])}")
                    except Exception:
                        pass
                    self.finished_signal.emit(True, "", "下载完成")
            else:
                self.log_signal.emit("❌ 下载失败")
                self.finished_signal.emit(False, "", "下载失败")

        except Exception as e:
            self.log_signal.emit(f"❌ 错误: {str(e)}")
            self.finished_signal.emit(False, "", f"错误: {str(e)}")

    def _find_media_file(self, search_dir: str) -> Optional[str]:
        """
        查找下载的媒体文件
        
        Args:
            search_dir: 搜索目录
            
        Returns:
            Optional[str]: 找到的文件路径，未找到返回None
        """
        try:
            media_exts = [
                '.mp4', '.flv', '.webm', '.mkv', '.avi', '.mov', '.wmv', '.m4v', '.mpg', '.mpeg',
                '.mp3', '.aac', '.flac', '.wav', '.ogg', '.m4a', '.opus'
            ]

            latest_file = None
            latest_time = 0
            current_time = time.time()

            self.log_signal.emit(f"🔍 在目录中搜索媒体文件: {search_dir}")
            
            for file in os.listdir(search_dir):
                file_lower = file.lower()
                # 排除弹幕文件和临时文件
                if (any(file_lower.endswith(ext) for ext in media_exts) and 
                    not file_lower.endswith('.cmt.xml') and
                    not file_lower.endswith('.part') and
                    not file_lower.endswith('.tmp')):
                    
                    file_path = os.path.join(search_dir, file)
                    try:
                        mtime = os.path.getmtime(file_path)
                        # 放宽时间限制到1分钟
                        if mtime > latest_time and (current_time - mtime) < 60:
                            latest_time = mtime
                            latest_file = file_path
                            self.log_signal.emit(f"📁 找到候选文件: {file}")
                    except Exception:
                        continue

            return latest_file
        except Exception as e:
            self.log_signal.emit(f"查找文件失败: {e}")
            return None

    def _convert_to_mp4(self, input_file: str) -> Tuple[bool, str]:
        """
        转换为MP4格式
        
        Args:
            input_file: 输入文件路径
            
        Returns:
            Tuple[bool, str]: (成功标志, 输出文件路径)
        """
        if not os.path.exists(input_file):
            return False, input_file

        try:
            ffmpeg_path = get_ffmpeg_path()
            if not ffmpeg_path:
                return False, input_file

            input_path = Path(input_file)
            safe_stem = sanitize_filename(input_path.stem)
            output_file = str(input_path.parent / f"{safe_stem}.mp4")

            counter = 1
            while os.path.exists(output_file):
                output_file = str(input_path.parent / f"{safe_stem}_{counter}.mp4")
                counter += 1

            cmd = [
                ffmpeg_path,
                "-i", input_file,
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", self.audio_bitrate,
                "-movflags", "+faststart",
                "-y",
                output_file
            ]

            # 使用文本模式处理FFmpeg输出
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )

            # 读取并忽略FFmpeg的输出
            for _ in process.stdout:
                pass

            process.wait()

            if process.returncode == 0 and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                return True, output_file

            return False, input_file

        except Exception:
            return False, input_file

    def _extract_audio(self, input_file: str, format_type: str = "mp3") -> Tuple[bool, str]:
        """
        提取音频
        
        Args:
            input_file: 输入文件路径
            format_type: 音频格式
            
        Returns:
            Tuple[bool, str]: (成功标志, 输出文件路径)
        """
        if not os.path.exists(input_file):
            return False, input_file

        try:
            ffmpeg_path = get_ffmpeg_path()
            if not ffmpeg_path:
                return False, input_file

            input_path = Path(input_file)
            safe_stem = sanitize_filename(input_path.stem)

            format_extensions = {
                "mp3": ".mp3", "aac": ".aac", "flac": ".flac",
                "wav": ".wav", "ogg": ".ogg", "m4a": ".m4a"
            }
            codec_map = {
                "mp3": "libmp3lame",
                "aac": "aac",
                "flac": "flac",
                "wav": "pcm_s16le",
                "ogg": "libvorbis",
                "m4a": "aac"
            }

            extension = format_extensions.get(format_type, ".mp3")
            codec = codec_map.get(format_type, "aac")
            output_file = str(input_path.parent / f"{safe_stem}{extension}")

            counter = 1
            while os.path.exists(output_file):
                output_file = str(input_path.parent / f"{safe_stem}_{counter}{extension}")
                counter += 1

            cmd = [
                ffmpeg_path,
                "-i", input_file,
                "-vn",
                "-c:a", codec,
                "-b:a", self.audio_bitrate,
            ]

            if format_type == "flac":
                cmd.extend(["-compression_level", "8"])
            elif format_type == "ogg":
                cmd.extend(["-q:a", "6"])
            elif format_type == "wav":
                cmd.extend(["-f", "wav"])

            cmd.extend(["-y", output_file])

            # 使用文本模式处理FFmpeg输出
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )

            # 读取并忽略FFmpeg的输出
            for _ in process.stdout:
                pass

            process.wait()

            if process.returncode == 0 and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                return True, output_file

            return False, input_file

        except Exception:
            return False, input_file


class BatchConverterWorker(QObject):
    """
    批量转换工作线程
    
    信号:
        progress_signal: 总体进度信号
        file_progress_signal: 单个文件进度信号
        log_signal: 日志信号
        finished_signal: 完成信号
    """
    
    progress_signal = Signal(int, str)
    file_progress_signal = Signal(str, int, str)
    log_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, file_list: List[str], output_dir: str,
                 target_format: str = "mp4", quality: int = 23,
                 audio_bitrate: str = "192k", delete_original: bool = False):
        """
        初始化批量转换工作线程
        
        Args:
            file_list: 文件列表
            output_dir: 输出目录
            target_format: 目标格式
            quality: 质量参数
            audio_bitrate: 音频比特率
            delete_original: 是否删除原文件
        """
        super().__init__()
        self.file_list = file_list
        self.output_dir = output_dir
        self.target_format = target_format
        self.quality = quality
        self.audio_bitrate = audio_bitrate
        self.delete_original = delete_original
        
        # 线程控制
        self._stop_flag = False
        self.process = None

    def stop(self):
        """停止批量转换"""
        self._stop_flag = True
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass

    def run(self):
        """执行批量转换"""
        try:
            total_files = len(self.file_list)
            if total_files == 0:
                self.finished_signal.emit(False, "没有文件需要转换")
                return

            self.log_signal.emit(f"🔄 开始批量转换 {total_files} 个文件")

            ffmpeg_path = get_ffmpeg_path()
            if not ffmpeg_path:
                self.log_signal.emit("❌ FFmpeg不可用")
                self.finished_signal.emit(False, "FFmpeg不可用")
                return

            os.makedirs(self.output_dir, exist_ok=True)

            converted_count = 0
            failed_count = 0

            for i, input_file in enumerate(self.file_list, 1):
                if self._stop_flag:
                    self.log_signal.emit("转换已取消")
                    break

                if not os.path.exists(input_file):
                    failed_count += 1
                    continue

                overall_percent = int((i - 1) / total_files * 100)
                self.progress_signal.emit(overall_percent, f"处理文件 {i}/{total_files}")

                file_name = os.path.basename(input_file)
                self.file_progress_signal.emit(file_name, 0, "开始转换")

                success = False
                output_file = ""

                if self.target_format in ["mp3", "aac", "flac", "wav", "ogg", "m4a"]:
                    success, output_file = self._extract_audio_from_video(input_file, ffmpeg_path)
                else:
                    success, output_file = self._convert_video_file(input_file, ffmpeg_path)

                if success:
                    converted_count += 1
                    self.file_progress_signal.emit(file_name, 100, "转换完成")
                    if self.delete_original:
                        try:
                            os.remove(input_file)
                        except Exception:
                            pass
                else:
                    failed_count += 1
                    self.file_progress_signal.emit(file_name, 0, "转换失败")

            self.progress_signal.emit(100, "批量转换完成")
            self.log_signal.emit(f"✅ 完成: 成功 {converted_count}, 失败 {failed_count}")
            self.finished_signal.emit(converted_count > 0, f"成功 {converted_count}, 失败 {failed_count}")

        except Exception as e:
            self.log_signal.emit(f"❌ 错误: {str(e)}")
            self.finished_signal.emit(False, f"错误: {str(e)}")

    def _convert_video_file(self, input_file: str, ffmpeg_path: str) -> Tuple[bool, str]:
        """
        转换视频文件
        
        Args:
            input_file: 输入文件
            ffmpeg_path: FFmpeg路径
            
        Returns:
            Tuple[bool, str]: (成功标志, 输出文件路径)
        """
        try:
            input_path = Path(input_file)
            safe_stem = sanitize_filename(input_path.stem)
            output_file = os.path.join(self.output_dir, f"{safe_stem}.{self.target_format}")

            counter = 1
            while os.path.exists(output_file):
                output_file = os.path.join(self.output_dir, f"{safe_stem}_{counter}.{self.target_format}")
                counter += 1

            cmd = [
                ffmpeg_path,
                "-i", input_file,
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", str(self.quality),
                "-c:a", "aac",
                "-b:a", self.audio_bitrate,
                "-movflags", "+faststart",
                "-y",
                output_file
            ]

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )

            # 读取并忽略FFmpeg的输出
            for _ in self.process.stdout:
                pass

            self.process.wait(timeout=600)

            if self.process.returncode == 0 and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                return True, output_file

            return False, ""

        except Exception:
            return False, ""

    def _extract_audio_from_video(self, input_file: str, ffmpeg_path: str) -> Tuple[bool, str]:
        """
        从视频中提取音频
        
        Args:
            input_file: 输入文件
            ffmpeg_path: FFmpeg路径
            
        Returns:
            Tuple[bool, str]: (成功标志, 输出文件路径)
        """
        try:
            input_path = Path(input_file)
            safe_stem = sanitize_filename(input_path.stem)
            output_file = os.path.join(self.output_dir, f"{safe_stem}.{self.target_format}")

            counter = 1
            while os.path.exists(output_file):
                output_file = os.path.join(self.output_dir, f"{safe_stem}_{counter}.{self.target_format}")
                counter += 1

            codec_map = {
                "mp3": "libmp3lame",
                "aac": "aac",
                "flac": "flac",
                "wav": "pcm_s16le",
                "ogg": "libvorbis",
                "m4a": "aac",
            }

            codec = codec_map.get(self.target_format, "aac")

            cmd = [
                ffmpeg_path,
                "-i", input_file,
                "-vn",
            ]

            if self.target_format == "wav":
                cmd.extend(["-c:a", codec, "-f", "wav"])
            elif self.target_format == "flac":
                cmd.extend(["-c:a", codec, "-compression_level", "8"])
            elif self.target_format == "ogg":
                cmd.extend(["-c:a", codec, "-q:a", "6"])
            elif self.target_format in ["mp3", "aac", "m4a"]:
                cmd.extend(["-c:a", codec, "-b:a", self.audio_bitrate])

            cmd.extend(["-y", output_file])

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )

            # 读取并忽略FFmpeg的输出
            for _ in self.process.stdout:
                pass

            self.process.wait(timeout=300)

            if self.process.returncode == 0 and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                return True, output_file

            return False, ""

        except Exception:
            return False, ""