import subprocess
from PIL import Image, ImageFilter, ImageEnhance
import sys
import os

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# 只处理第4张（最清晰，周日016-020）
img_path = r"C:\Users\lianjie\.openclaw\workspace\media\inbound\openclaw-media-1778492230780-ciwqmk.jpg"

img = Image.open(img_path)
print(f"原图尺寸: {img.size}")

# 比分列在右侧约80%-95%区域
# 根据截图，比分列在"完场"文字后面
# 裁剪比分列区域
left = int(img.width * 0.78)
right = int(img.width * 0.98)
top = int(img.height * 0.05)
bottom = int(img.height * 0.95)

cropped = img.crop((left, top, right, bottom))
print(f"裁剪后: {cropped.size}")

# 放大5倍
cropped = cropped.resize((cropped.width * 5, cropped.height * 5), Image.LANCZOS)
print(f"放大5倍: {cropped.size}")

# 转灰度
cropped = cropped.convert('L')

# 增强对比度
enhancer = ImageEnhance.Contrast(cropped)
cropped = enhancer.enhance(5.0)

# 锐化
cropped = cropped.filter(ImageFilter.SHARPEN)

# 二值化（阈值调整）
cropped = cropped.point(lambda x: 0 if x < 80 else 255)

out_path = r"c:\temp\ocr_zhou4_enhanced.png"
cropped.save(out_path)
print(f"保存: {out_path}")

# 尝试多种Tesseract配置
configs = [
    ('--psm 6 -l eng', '英文模式'),
    ('--psm 7 -l eng', '单行模式'),
    ('--psm 13 -l eng', '原始文本模式'),
    ('--psm 6 -l eng digits', '数字模式'),
]

for config, desc in configs:
    result = subprocess.run(
        ['tesseract', out_path, 'stdout'] + config.split(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding='utf-8', errors='replace'
    )
    text = result.stdout.strip()
    print(f"\n=== {desc} ===")
    # 只提取数字和冒号
    import re
    scores = re.findall(r'\d+[:\-]\d+', text)
    if scores:
        print(f"识别到比分: {scores}")
    else:
        print(f"原始输出: {text[:200]}")
