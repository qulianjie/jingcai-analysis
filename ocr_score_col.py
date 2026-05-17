import subprocess
from PIL import Image, ImageEnhance, ImageFilter
import sys

# 读取图片
img = Image.open(r'C:\Users\lianjie\.openclaw\workspace\media\inbound\openclaw-media-1778496784527-8qj12r.jpg')
print(f"图片尺寸: {img.size}")

# 全屏截图，提取右侧比分区域
# 比分列在图像右侧，大约x从70%到95%
left = int(img.width * 0.72)
right = int(img.width * 0.95)
top = int(img.height * 0.12)
bottom = int(img.height * 0.92)

score_crop = img.crop((left, top, right, bottom))
print(f"比分列裁剪尺寸: {score_crop.size}")

# 放大6倍
score_crop = score_crop.resize((score_crop.width * 6, score_crop.height * 6), Image.LANCZOS)

# 转灰度
score_crop = score_crop.convert('L')

# 高对比度
enhancer = ImageEnhance.Contrast(score_crop)
score_crop = enhancer.enhance(6.0)

# 锐化
score_crop = score_crop.filter(ImageFilter.SHARPEN)

# 二值化
score_crop = score_crop.point(lambda x: 0 if x < 100 else 255)

# 保存
score_crop.save(r'c:\temp\score_col_006_010.png')
print(f"处理后尺寸: {score_crop.size}")
print("保存: c:\\temp\\score_col_006_010.png")

# 逐行分割比分区域
# 5场比赛，均匀分布
h = score_crop.height
row_h = h // 5

for i in range(5):
    y_start = row_h * i + row_h // 10  # 留一些margin
    y_end = row_h * (i + 1) - row_h // 10
    
    row = score_crop.crop((0, y_start, score_crop.width, y_end))
    row.save(rf'c:\temp\score_row_{i+1}_006_010.png')
    
    # OCR每行
    result = subprocess.run(
        ['tesseract', rf'c:\temp\score_row_{i+1}_006_010.png', 'stdout', '--psm', '7', '-l', 'eng'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    text = result.stdout.decode('utf-8', errors='replace').strip()
    print(f"第{i+1}行: '{text}'")
