# 易下(EDown) - 完整安装与使用指南

## 📋 项目简介

一个功能强大的视频下载和格式转换工具，采用现代化的 Fluent Design 界面，支持多平台视频下载、格式转换和音频提取。

---

## ⚠️ 重要：关于镜像源的说明

### 为什么必须使用官方源？

在安装本项目依赖的 `PySide6-Fluent-Widgets` 时，**强烈建议使用官方 PyPI 源 (`https://pypi.org/simple/`)**，而不是国内的镜像源。

### 镜像源可能导致的问题

| 问题类型 | 错误信息 | 原因 |
|---------|---------|------|
| 导入错误 | `ImportError: cannot import name 'TabWidget' from 'qfluentwidgets'` | 镜像源同步延迟，包版本不完整 |
| 导航栏崩溃 | `AttributeError: 'function' object has no attribute 'isNull'` | 旧版本存在已知 bug |
| 组件缺失 | `ImportError: cannot import name 'FluentIcon'` | 包版本过低或损坏 |

### 验证方法

```bash
# 查看当前使用的源
pip config list

# 检查已安装版本
pip show PySide6-Fluent-Widgets

# 测试关键组件
python -c "from qfluentwidgets import FluentWindow, FluentIcon, TabWidget; print('✅ 组件可用')"
```

---

## 🔧 环境配置（详细步骤）

### 1. 克隆项目

```bash
git clone [项目地址]
cd video-downloader
```

### 2. 创建虚拟环境

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 配置 pip 使用官方源（关键步骤）

**方法一：临时使用官方源安装**
```bash
pip install -r requirements.txt -i https://pypi.org/simple/
```

**方法二：永久配置官方源（推荐）**
```bash
# 设置全局默认源为官方源
pip config set global.index-url https://pypi.org/simple/

# 验证配置
pip config list
```

**方法三：仅安装核心包**
```bash
pip install PySide6-Fluent-Widgets[full]==1.6.3 -i https://pypi.org/simple/
pip install -r requirements.txt
```

### 4. 验证安装

```bash
# 查看所有已安装包
pip list

# 验证 Fluent Widgets 版本
pip show PySide6-Fluent-Widgets

# 测试导入
python -c "
from qfluentwidgets import FluentWindow, FluentIcon, TabWidget
from PySide6.QtCore import Qt
print('✅ 所有组件导入成功')
"
```

---

## 📦 requirements.txt 内容

```txt
# 核心依赖 - PySide6
PySide6==6.6.0
shiboken6==6.6.0

# Fluent Widgets - 必须从官方源安装
PySide6-Fluent-Widgets[full]==1.6.3

# 视频下载工具
yt-dlp==2024.12.13
you-get==0.4.1650

# 完整版 Fluent Widgets 的额外依赖
pillow>=10.0.0
scipy>=1.10.0
colorthief>=0.2.1

# 其他工具
requests>=2.31.0
tqdm>=4.66.0
```

---

## 🚀 运行程序

```bash
# 确保在虚拟环境中
python main.py
```

---

## 🎯 功能使用指南

### 1. 视频下载

1. 点击左侧导航栏的 **"下载"**
2. 粘贴视频链接（支持 YouTube、Bilibili 等）
3. 点击 **"分析视频"** 获取可用格式
4. 选择视频质量和格式
5. 点击 **"开始下载"**

### 2. 格式转换

1. 点击左侧导航栏的 **"转换"**
2. 拖拽或点击添加要转换的文件
3. 选择输出格式和质量
4. 点击 **"开始转换"**

### 3. 音频提取

1. 点击左侧导航栏的 **"音频"**
2. 添加视频文件
3. 选择音频格式和质量
4. 点击 **"开始提取"**

---

## 🔍 常见问题排查

### 问题1：安装时出现 SSL 错误

**错误信息**：
```
Could not fetch URL https://pypi.org/simple/...: There was a problem confirming the ssl certificate
```

**解决方案**：
```bash
# 临时忽略 SSL 验证（不推荐长期使用）
pip install -r requirements.txt -i https://pypi.org/simple/ --trusted-host pypi.org

# 或更新 SSL 证书
pip install --upgrade certifi
```

### 问题2：导入 TabWidget 失败

**错误信息**：
```python
ImportError: cannot import name 'TabWidget' from 'qfluentwidgets'
```

**解决方案**：
```bash
# 1. 卸载当前版本
pip uninstall PySide6-Fluent-Widgets -y

# 2. 清理缓存
pip cache purge

# 3. 从官方源重新安装指定版本
pip install PySide6-Fluent-Widgets[full]==1.11.1 -i https://pypi.org/simple/
```

### 问题3：导航栏点击崩溃

**错误信息**：
```python
AttributeError: 'function' object has no attribute 'isNull'
```

**解决方案**：
```bash
# 切换到官方源最新版本
pip install --upgrade PySide6-Fluent-Widgets[full] -i https://pypi.org/simple/
```

### 问题4：FFmpeg 未找到

**错误信息**：
```
未找到FFmpeg，请安装FFmpeg后重试
```

**解决方案**：

**Windows:**
- 下载 FFmpeg：https://ffmpeg.org/download.html
- 解压到项目根目录的 `ffmpeg` 文件夹
- 或添加到系统 PATH

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

### 问题5：虚拟环境激活失败

**Windows PowerShell 执行策略限制：**
```bash
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
# 然后重新激活
venv\Scripts\activate
```

---

## 💡 镜像源配置建议

### 日常开发的最佳实践

| 场景 | 推荐操作 |
|------|---------|
| **首次安装项目依赖** | 使用官方源 `-i https://pypi.org/simple/` |
| **日常安装其他包** | 可使用清华源（速度快） |
| **遇到导入错误** | 先用官方源更新 `PySide6-Fluent-Widgets` |
| **生产环境部署** | 固定版本号，用官方源安装 |

### 镜像源切换命令

```bash
# 切换到清华源
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 切换回官方源
pip config set global.index-url https://pypi.org/simple/

# 临时使用不同源安装单个包
pip install 包名 -i https://pypi.org/simple/
pip install 包名 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 查看当前配置

```bash
# 查看所有配置
pip config list

# 查看当前使用的源
pip config get global.index-url
```

---

## 📊 版本兼容性表

| 组件 | 推荐版本 | 最低版本 | 说明 |
|------|---------|---------|------|
| Python | 3.9 - 3.11 | 3.8 | 3.12+ 可能有兼容性问题 |
| PySide6 | 6.6.0 | 6.4.0 | 与 Fluent-Widgets 最兼容 |
| PySide6-Fluent-Widgets | 1.6.3 | 1.5.0 | 必须从官方源安装 |
| yt-dlp | 2024.12.13 | 2023.0.0 | 建议保持最新 |
| you-get | 0.4.1650 | 0.4.1500 | 用于 Bilibili 等网站 |

---

## 📝 常见命令速查

```bash
# 激活虚拟环境
venv\Scripts\activate                 # Windows
source venv/bin/activate               # macOS/Linux

# 安装依赖（官方源）
#可以其他包正常下载，但是PySide6-Fluent-Widgets必须是官方源！！！
pip install -r requirements.txt -i https://pypi.org/simple/

# 更新单个包
pip install --upgrade PySide6-Fluent-Widgets[full] -i https://pypi.org/simple/

# 查看包信息
pip show PySide6-Fluent-Widgets

# 导出当前环境
pip freeze > requirements.txt

# 退出虚拟环境
deactivate
```

---

## 🆘 获取帮助

如果遇到本指南未覆盖的问题：

1. 检查错误信息中的具体提示
2. 确认是否使用了官方源安装
3. 查看 [qfluentwidgets 官方文档](https://qfluentwidgets.com/)
4. 提交 Issue 时请包含：
   - 完整的错误信息
   - `pip list` 的输出
   - 使用的 Python 版本

---

## 🎉 结语

遵循本指南的步骤，特别是**使用官方源安装核心依赖**，应该能顺利运行本项目。如果还有问题，欢迎反馈！

**祝使用愉快！** 🚀