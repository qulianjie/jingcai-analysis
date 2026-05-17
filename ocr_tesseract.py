import subprocess
from PIL import Image, ImageFilter, ImageEnhance
import sys
import os

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# 第四张截图最清晰，先试这张
img_path = r"C:\Users\lianjie\.openclaw\workspace\media\inbound\openclaw-media-1778492222198-kyb7dh.jpg"

if not os.path.exists(img_path):
    print(f"文件不存在: {img_path}")
    sys.exit(1)

# 图像预处理
img = Image.open(img_path)
print(f"原图尺寸: {img.size}")

# 放大3倍
img = img.resize((img.width * 3, img.height * 3), Image.LANCZOS)
print(f"放大后: {img.size}")

# 转灰度
img = img.convert('L')

# 增强对比度
enhancer = ImageEnhance.Contrast(img)
img = enhancer.enhance(3.0)

# 二值化
img = img.point(lambda x: 0 if x < 128 else 255)

# 保存预处理后的图片
preprocessed_path = r"c:\temp\preprocessed_zhou4.png"
img.save(preprocessed_path)
print(f"预处理图片保存: {preprocessed_path}")

# 用tesseract OCR
result = subprocess.run(
    ['tesseract', preprocessed_path, 'stdout', '--psm', '6', '-l', 'eng+chi_sim'],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    encoding='utf-8', errors='replace'
)

print("=== Tesseract OCR 结果 ===")
print(result.stdout)
print("\n=== stderr ===")
print(result.stderr if hasattr(result, 'stderr') and result.stderr else '(none)')
