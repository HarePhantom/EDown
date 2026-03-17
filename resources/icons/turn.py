import os
import sys
import numpy as np
from PIL import Image
import subprocess
import base64
from io import BytesIO

class ImageConverter:
    """图片格式转换工具类"""
    
    @staticmethod
    def to_ico(png_path, ico_path=None, sizes=None):
        """PNG转ICO"""
        if sizes is None:
            sizes = [16, 32, 48, 64, 128, 256]
        if ico_path is None:
            ico_path = os.path.splitext(png_path)[0] + '.ico'
            
        try:
            # 打开PNG图片
            img = Image.open(png_path)
            
            # 转换为RGBA模式（保留透明度）
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # 准备多个尺寸的图片
            icon_images = []
            for size in sizes:
                # 调整图片大小，使用高质量的缩放算法
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                icon_images.append(resized)
            
            # 保存为ICO（可以包含多个尺寸）
            icon_images[0].save(
                ico_path,
                format='ICO',
                sizes=[(size, size) for size in sizes],
                append_images=icon_images[1:]
            )
            
            print(f"✅ ICO转换成功：{ico_path}")
            print(f"   包含尺寸：{sizes}")
            return True
            
        except Exception as e:
            print(f"❌ ICO转换失败：{e}")
            return False
    
    @staticmethod
    def to_svg_vtracer(png_path, svg_path=None):
        """
        使用vtracer将PNG转换为SVG矢量图（修复版）
        """
        try:
            import vtracer
        except ImportError:
            print("❌ 请先安装vtracer：pip install vtracer")
            return False
            
        if svg_path is None:
            svg_path = os.path.splitext(png_path)[0] + '.svg'
        
        try:
            # 打开图片
            img = Image.open(png_path)
            
            # 转换为numpy数组
            # vtracer新版本使用不同的API
            img_array = np.array(img)
            
            # 检查vtracer版本并适配
            # 方法1: 尝试使用convert_pil_to_svg（新版本）
            try:
                # 新版本vtracer可能有这个方法
                if hasattr(vtracer, 'convert_pil_to_svg'):
                    svg_str = vtracer.convert_pil_to_svg(img)
                    with open(svg_path, 'w', encoding='utf-8') as f:
                        f.write(svg_str)
                # 方法2: 使用convert_to_svg（旧版本）
                elif hasattr(vtracer, 'convert_to_svg'):
                    # 旧版本API
                    svg_bytes = vtracer.convert_to_svg(
                        img_array,
                        colormode='color',
                        hierarchical='stacked',
                        mode='spline',
                        filter_speckle=4
                    )
                    with open(svg_path, 'wb') as f:
                        f.write(svg_bytes)
                else:
                    # 方法3: 使用命令行方式（备用）
                    return ImageConverter._to_svg_fallback(png_path, svg_path)
                    
            except AttributeError:
                # 方法3: 尝试使用命令行
                return ImageConverter._to_svg_fallback(png_path, svg_path)
            
            print(f"✅ SVG转换成功：{svg_path}")
            return True
            
        except Exception as e:
            print(f"❌ SVG转换失败：{e}")
            print("尝试使用备用方法...")
            return ImageConverter._to_svg_fallback(png_path, svg_path)
    
    @staticmethod
    def _to_svg_fallback(png_path, svg_path):
        """
        备用方法：使用嵌入方式将PNG转为SVG（当vtracer失败时）
        """
        try:
            # 读取图片
            img = Image.open(png_path)
            width, height = img.size
            
            # 将图片转换为base64编码
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # 创建SVG内容
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <image width="{width}" height="{height}" xlink:href="data:image/png;base64,{img_base64}"/>
</svg>'''
            
            # 保存SVG文件
            with open(svg_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            print(f"✅ SVG转换成功（嵌入模式）：{svg_path}")
            print(f"   注意：这是嵌入型SVG，放大后仍然是像素图")
            return True
            
        except Exception as e:
            print(f"❌ 备用SVG转换失败：{e}")
            return False
    
    @staticmethod
    def to_svg_contour(png_path, svg_path=None):
        """
        使用轮廓追踪将PNG转换为SVG（黑白线条图）
        """
        try:
            from skimage import measure
        except ImportError:
            print("❌ 请先安装scikit-image：pip install scikit-image")
            return False
            
        if svg_path is None:
            svg_path = os.path.splitext(png_path)[0] + '_contour.svg'
        
        try:
            # 读取图片
            img = Image.open(png_path)
            
            # 转换为灰度图
            if img.mode == 'RGBA':
                # 处理透明度：创建白色背景
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3])
                img = bg.convert('L')
            else:
                img = img.convert('L')
            
            # 转换为numpy数组并二值化
            img_array = np.array(img)
            binary = img_array < 128  # 阈值128
            
            # 查找轮廓
            contours = measure.find_contours(binary, 0.5)
            
            # 创建SVG内容
            svg_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
            svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {img.width} {img.height}">')
            
            # 添加轮廓到SVG
            for contour in contours:
                if len(contour) > 2:
                    # 转换坐标并生成路径
                    points = []
                    for y, x in contour:
                        points.append(f"{x:.2f},{y:.2f}")
                    
                    if points:
                        path_data = "M " + " L ".join(points)
                        svg_lines.append(f'  <path d="{path_data}" fill="none" stroke="black" stroke-width="1"/>')
            
            svg_lines.append('</svg>')
            
            # 保存SVG文件
            with open(svg_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(svg_lines))
            
            print(f"✅ SVG转换成功（轮廓模式）：{svg_path}")
            return True
            
        except Exception as e:
            print(f"❌ 轮廓SVG转换失败：{e}")
            return False
    
    @staticmethod
    def convert_all(png_path, output_dir=None):
        """
        自动转换所有格式（ICO + 多种SVG）
        """
        if not os.path.exists(png_path):
            print(f"❌ 文件不存在：{png_path}")
            return False
        
        # 确定输出目录
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            base_name = os.path.basename(os.path.splitext(png_path)[0])
        else:
            output_dir = os.path.dirname(png_path) or '.'
            base_name = os.path.splitext(os.path.basename(png_path))[0]
        
        print(f"\n🔄 开始转换：{png_path}")
        print("=" * 50)
        
        # 1. 转换ICO
        ico_path = os.path.join(output_dir, f"{base_name}.ico")
        ico_result = ImageConverter.to_ico(png_path, ico_path)
        
        # 2. 尝试vtracer SVG（最佳质量）
        svg_vtracer_path = os.path.join(output_dir, f"{base_name}.svg")
        svg_result = ImageConverter.to_svg_vtracer(png_path, svg_vtracer_path)
        
        # 3. 如果vtracer失败，尝试轮廓SVG
        if not svg_result:
            svg_contour_path = os.path.join(output_dir, f"{base_name}_contour.svg")
            svg_result = ImageConverter.to_svg_contour(png_path, svg_contour_path)
        
        print("=" * 50)
        if ico_result and svg_result:
            print("✅ 所有转换完成！")
            print(f"   📁 ICO: {ico_path}")
            print(f"   📁 SVG: {svg_vtracer_path if svg_result else svg_contour_path}")
            return True
        else:
            print("⚠️ 部分转换失败，请查看上面的错误信息")
            return False

def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法：")
        print("  python turn.py <PNG文件路径> [输出目录]")
        print("  python turn.py <PNG文件路径> --ico     # 只转ICO")
        print("  python turn.py <PNG文件路径> --svg     # 只转SVG")
        print("  python turn.py <PNG文件路径> --all     # 转换所有格式（默认）")
        print("\n示例：")
        print("  python turn.py logo.png")
        print("  python turn.py logo.png --ico")
        print("  python turn.py logo.png output_folder")
        return
    
    # 解析参数
    png_path = sys.argv[1]
    
    mode = 'all'
    output_dir = None
    
    if len(sys.argv) >= 3:
        if sys.argv[2] in ['--ico', '--svg', '--all']:
            mode = sys.argv[2][2:]  # 去掉'--'
        else:
            output_dir = sys.argv[2]
    
    if len(sys.argv) >= 4:
        if sys.argv[3] in ['--ico', '--svg', '--all']:
            mode = sys.argv[3][2:]
    
    # 执行转换
    converter = ImageConverter()
    
    if mode == 'ico':
        converter.to_ico(png_path)
    elif mode == 'svg':
        # 尝试vtracer，失败则用轮廓
        if not converter.to_svg_vtracer(png_path):
            converter.to_svg_contour(png_path)
    else:  # all
        converter.convert_all(png_path, output_dir)

if __name__ == "__main__":
    # 直接使用示例（修改这里的文件路径即可）
    # ImageConverter.convert_all("logo.png")  # 自动转换所有格式
    
    # 或者使用命令行参数
    main()