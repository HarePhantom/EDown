# -*- coding: utf-8 -*-

"""
转换器模块 - 视频/音频格式转换
==============================

作者: GraceFox
用户名: HarePhantom
创建日期: 2026-03-14

功能:
- 视频格式转换
- 音频提取
- 进度监控
- 取消/暂停功能
"""

import os
import re
import time
import subprocess
from pathlib import Path
from typing import Optional, Dict
from PySide6.QtCore import QObject, Signal, QMutex, QMutexLocker

from src.core.utils import get_ffmpeg_path, sanitize_filename, format_file_size


class ConverterWorker(QObject):
    """
    视频/音频转换工作线程
    
    信号:
        progress_signal: 进度更新信号 (进度百分比, 状态信息)
        log_signal: 日志信息信号 (日志文本)
        finished_signal: 完成信号 (成功标志, 输出路径, 消息)
    """
    
    progress_signal = Signal(int, str)  # 进度百分比，状态信息
    log_signal = Signal(str)  # 日志信息
    finished_signal = Signal(bool, str, str)  # success, output_path, message

    def __init__(self, input_file: str, output_file: str,
                 output_format: str = "mp4", video_quality: str = "原质量",
                 audio_bitrate: str = "192k", audio_sample_rate: str = "44100",
                 keep_original: bool = True, crf: int = 23):
        """
        初始化转换工作线程
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            output_format: 输出格式
            video_quality: 视频质量
            audio_bitrate: 音频比特率
            audio_sample_rate: 音频采样率
            keep_original: 是否保留原文件
            crf: CRF质量参数（值越小质量越高）
        """
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.output_format = output_format
        self.video_quality = video_quality
        self.audio_bitrate = audio_bitrate
        self.audio_sample_rate = audio_sample_rate
        self.keep_original = keep_original
        self.crf = crf
        
        # 线程控制
        self._stop_flag = False
        self._mutex = QMutex()
        self.total_duration = 0
        self.process = None

    def stop(self):
        """停止转换任务"""
        with QMutexLocker(self._mutex):
            self._stop_flag = True
            if self.process:
                try:
                    self.process.terminate()
                except Exception:
                    pass

    def _should_stop(self) -> bool:
        """检查是否应该停止"""
        with QMutexLocker(self._mutex):
            return self._stop_flag

    def _get_media_duration(self, ffmpeg_path: str) -> float:
        """
        获取媒体文件时长（秒）
        
        Args:
            ffmpeg_path: FFmpeg可执行文件路径
            
        Returns:
            float: 媒体时长（秒），失败返回0
        """
        try:
            cmd = [ffmpeg_path, "-i", self.input_file]
            result = subprocess.run(cmd, capture_output=True, text=True, stderr=subprocess.PIPE, timeout=30)
            
            # 匹配时长格式：01:23:45.67 或 123.45
            duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d+)', result.stderr)
            if duration_match:
                hours, minutes, seconds = duration_match.groups()
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            
            # 尝试另一种格式
            duration_match = re.search(r'Duration: (\d+):(\d{2}):(\d{2}\.\d+)', result.stderr)
            if duration_match:
                hours, minutes, seconds = duration_match.groups()
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        except Exception:
            pass
        return 0

    def run(self):
        """执行转换任务"""
        try:
            if self._should_stop():
                self.finished_signal.emit(False, "", "转换已取消")
                return

            self.log_signal.emit(f"开始转换: {os.path.basename(self.input_file)}")
            self.log_signal.emit(f"输出文件: {self.output_file}")

            # 获取FFmpeg路径
            ffmpeg_path = get_ffmpeg_path()
            if not ffmpeg_path:
                raise Exception("未找到FFmpeg，请确保FFmpeg已安装")

            # 检查输入文件
            if not os.path.exists(self.input_file):
                raise Exception(f"输入文件不存在: {self.input_file}")

            # 获取总时长
            self.total_duration = self._get_media_duration(ffmpeg_path)
            if self.total_duration > 0:
                self.log_signal.emit(f"媒体总时长: {self._format_duration(self.total_duration)}")

            # 构建FFmpeg命令
            cmd = [ffmpeg_path, "-i", self.input_file]

            # 根据输出格式设置参数
            audio_formats = ["mp3", "aac", "flac", "wav", "ogg", "m4a"]
            
            if self.output_format in audio_formats:
                # 音频转换
                cmd.extend(["-vn"])  # 移除视频流
                cmd.extend(["-ab", self.audio_bitrate])  # 音频比特率
                cmd.extend(["-ar", self.audio_sample_rate])  # 采样率
                
                # 设置音频编码器
                codec_map = {
                    "mp3": "libmp3lame",
                    "aac": "aac",
                    "flac": "flac",
                    "wav": "pcm_s16le",
                    "ogg": "libvorbis",
                    "m4a": "aac"
                }
                codec = codec_map.get(self.output_format, "aac")
                cmd.extend(["-c:a", codec])
                
                # 格式特定参数
                if self.output_format == "flac":
                    cmd.extend(["-compression_level", "8"])  # FLAC最高压缩
                elif self.output_format == "ogg":
                    cmd.extend(["-q:a", "6"])  # OGG质量
                elif self.output_format == "wav":
                    cmd.extend(["-f", "wav"])
            else:
                # 视频转换
                # 视频编码设置
                cmd.extend(["-c:v", "libx264"])
                cmd.extend(["-preset", "medium"])
                cmd.extend(["-crf", str(self.crf)])  # 质量参数，值越小质量越高
                
                # 分辨率调整
                if self.video_quality != "原质量":
                    # 获取分辨率数值
                    resolution = re.search(r'(\d+)p', self.video_quality)
                    if resolution:
                        height = resolution.group(1)
                        # 保持宽高比，宽度自动计算
                        cmd.extend(["-vf", f"scale=-2:{height}"])
                
                # 音频设置
                cmd.extend(["-c:a", "aac"])
                cmd.extend(["-b:a", self.audio_bitrate])

            # 输出文件（-y 覆盖已存在的文件）
            cmd.extend(["-y", self.output_file])

            self.log_signal.emit(f"执行命令: {' '.join(cmd)}")

            # 执行转换
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore',
                bufsize=1
            )

            # 监控进度
            last_progress = 0
            last_time = 0
            
            while True:
                if self._should_stop():
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                    self.finished_signal.emit(False, "", "转换已取消")
                    return

                # 检查进程是否结束
                if self.process.poll() is not None:
                    break

                # 读取输出
                line = self.process.stderr.readline()
                if line:
                    # 解析FFmpeg进度信息
                    if self.total_duration > 0:
                        # 匹配时间
                        time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2}\.\d+)', line)
                        if time_match:
                            hours, minutes, seconds = time_match.groups()
                            current_time = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                            
                            # 避免除以零
                            if self.total_duration > 0:
                                progress = min(99, int((current_time / self.total_duration) * 100))
                                
                                # 避免重复发送相同进度
                                if progress != last_progress and abs(current_time - last_time) > 0.5:
                                    last_progress = progress
                                    last_time = current_time
                                    self.progress_signal.emit(progress, f"转换中... {progress}%")

                time.sleep(0.1)

            # 获取最终返回码
            return_code = self.process.wait()

            # 检查结果
            if return_code == 0:
                if os.path.exists(self.output_file) and os.path.getsize(self.output_file) > 0:
                    file_size = os.path.getsize(self.output_file)
                    self.progress_signal.emit(100, "转换完成")
                    
                    # 如果不保留原文件，删除原文件
                    if not self.keep_original and os.path.exists(self.input_file):
                        try:
                            os.remove(self.input_file)
                            self.log_signal.emit(f"已删除原文件: {os.path.basename(self.input_file)}")
                        except Exception as e:
                            self.log_signal.emit(f"删除原文件失败: {e}")
                    
                    self.finished_signal.emit(True, self.output_file, 
                                             f"转换成功，大小: {format_file_size(file_size)}")
                else:
                    self.finished_signal.emit(False, "", "输出文件未生成或文件大小为0")
            else:
                error_output = self.process.stderr.read()
                error_msg = error_output[:500] if error_output else f"转换失败，返回码: {return_code}"
                self.finished_signal.emit(False, "", f"转换失败: {error_msg}")

        except Exception as e:
            self.log_signal.emit(f"转换错误: {e}")
            self.finished_signal.emit(False, "", str(e))

    def _format_duration(self, seconds: float) -> str:
        """格式化时长（秒 -> HH:MM:SS 或 MM:SS）"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"


class AudioExtractorWorker(QObject):
    """
    音频提取工作线程 - 专门用于从视频中提取音频
    
    信号:
        progress_signal: 进度更新信号
        log_signal: 日志信息信号
        finished_signal: 完成信号
    """
    
    progress_signal = Signal(int, str)
    log_signal = Signal(str)
    finished_signal = Signal(bool, str, str)  # success, output_path, message

    def __init__(self, input_file: str, output_file: str,
                 audio_format: str = "mp3", audio_bitrate: str = "192k",
                 audio_sample_rate: str = "44100", normalize_audio: bool = False,
                 keep_original: bool = True):
        """
        初始化音频提取工作线程
        
        Args:
            input_file: 输入视频文件路径
            output_file: 输出音频文件路径
            audio_format: 音频格式
            audio_bitrate: 音频比特率
            audio_sample_rate: 音频采样率
            normalize_audio: 是否进行音频标准化
            keep_original: 是否保留原视频文件
        """
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.audio_format = audio_format
        self.audio_bitrate = audio_bitrate
        self.audio_sample_rate = audio_sample_rate
        self.normalize_audio = normalize_audio
        self.keep_original = keep_original
        
        # 线程控制
        self._stop_flag = False
        self._mutex = QMutex()
        self.total_duration = 0
        self.process = None

    def stop(self):
        """停止提取任务"""
        with QMutexLocker(self._mutex):
            self._stop_flag = True
            if self.process:
                try:
                    self.process.terminate()
                except Exception:
                    pass

    def _should_stop(self) -> bool:
        """检查是否应该停止"""
        with QMutexLocker(self._mutex):
            return self._stop_flag

    def _get_media_duration(self, ffmpeg_path: str) -> float:
        """获取媒体文件时长"""
        try:
            cmd = [ffmpeg_path, "-i", self.input_file]
            result = subprocess.run(cmd, capture_output=True, text=True, stderr=subprocess.PIPE, timeout=30)
            
            duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d+)', result.stderr)
            if duration_match:
                hours, minutes, seconds = duration_match.groups()
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        except Exception:
            pass
        return 0

    def run(self):
        """执行音频提取"""
        try:
            if self._should_stop():
                self.finished_signal.emit(False, "", "提取已取消")
                return

            self.log_signal.emit(f"开始提取音频: {os.path.basename(self.input_file)}")
            self.log_signal.emit(f"输出文件: {self.output_file}")

            # 获取FFmpeg路径
            ffmpeg_path = get_ffmpeg_path()
            if not ffmpeg_path:
                raise Exception("未找到FFmpeg，请确保FFmpeg已安装")

            # 检查输入文件
            if not os.path.exists(self.input_file):
                raise Exception(f"输入文件不存在: {self.input_file}")

            # 获取总时长
            self.total_duration = self._get_media_duration(ffmpeg_path)

            # 构建FFmpeg命令
            cmd = [ffmpeg_path, "-i", self.input_file]

            # 音频提取参数
            cmd.extend(["-vn"])  # 移除视频流
            cmd.extend(["-ab", self.audio_bitrate])  # 音频比特率
            cmd.extend(["-ar", self.audio_sample_rate])  # 采样率

            # 根据格式设置编码器
            codec_map = {
                "mp3": "libmp3lame",
                "aac": "aac",
                "flac": "flac",
                "wav": "pcm_s16le",
                "ogg": "libvorbis",
                "m4a": "aac"
            }
            
            codec = codec_map.get(self.audio_format, "aac")
            cmd.extend(["-c:a", codec])

            # 根据格式设置特殊参数
            if self.audio_format == "flac":
                cmd.extend(["-compression_level", "8"])  # FLAC最高压缩
            elif self.audio_format == "ogg":
                cmd.extend(["-q:a", "6"])  # OGG质量
            elif self.audio_format == "wav":
                cmd.extend(["-f", "wav"])

            # 音频标准化（调整音量）
            if self.normalize_audio:
                cmd.extend(["-af", "loudnorm=I=-16:TP=-1.5:LRA=11"])

            # 输出文件
            cmd.extend(["-y", self.output_file])

            self.log_signal.emit(f"执行命令: {' '.join(cmd)}")

            # 执行提取
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore',
                bufsize=1
            )

            # 监控进度
            last_progress = 0
            last_time = 0
            
            while True:
                if self._should_stop():
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                    self.finished_signal.emit(False, "", "提取已取消")
                    return

                # 检查进程是否结束
                if self.process.poll() is not None:
                    break

                # 读取输出
                line = self.process.stderr.readline()
                if line and self.total_duration > 0:
                    time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2}\.\d+)', line)
                    if time_match:
                        hours, minutes, seconds = time_match.groups()
                        current_time = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                        
                        # 避免除以零
                        if self.total_duration > 0:
                            progress = min(99, int((current_time / self.total_duration) * 100))
                            
                            # 避免重复发送相同进度
                            if progress != last_progress and abs(current_time - last_time) > 0.5:
                                last_progress = progress
                                last_time = current_time
                                self.progress_signal.emit(progress, f"提取中... {progress}%")

                time.sleep(0.1)

            # 获取最终返回码
            return_code = self.process.wait()

            # 检查结果
            if return_code == 0:
                if os.path.exists(self.output_file) and os.path.getsize(self.output_file) > 0:
                    file_size = os.path.getsize(self.output_file)
                    self.progress_signal.emit(100, "提取完成")
                    
                    # 如果不保留原文件，删除原文件
                    if not self.keep_original and os.path.exists(self.input_file):
                        try:
                            os.remove(self.input_file)
                            self.log_signal.emit(f"已删除原文件: {os.path.basename(self.input_file)}")
                        except Exception as e:
                            self.log_signal.emit(f"删除原文件失败: {e}")
                    
                    self.finished_signal.emit(True, self.output_file, 
                                             f"提取成功，大小: {format_file_size(file_size)}")
                else:
                    self.finished_signal.emit(False, "", "输出文件未生成或文件大小为0")
            else:
                error_output = self.process.stderr.read()
                error_msg = error_output[:500] if error_output else f"提取失败，返回码: {return_code}"
                self.finished_signal.emit(False, "", f"提取失败: {error_msg}")

        except Exception as e:
            self.log_signal.emit(f"提取错误: {e}")
            self.finished_signal.emit(False, "", str(e))