import subprocess
from PIL import Image, ImageFilter, ImageEnhance
import sys
import os

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# 6张截图路径
img_paths = [
    r"C:\Users\lianjie\.openclaw\workspace\media\inbound\openclaw-media-1778492205889-csuexh.jpg",  # 001-005
    r"C:\Users\lianjie\.openclaw\workspace\media\inbound\openclaw-media-1778492212488-6g6y1x.jpg",  # 006-010
    r"C:\Users\lianjie\.openclaw\workspace\media\inbound\openclaw-media-1778492222198-kyb7dh.jpg",  # 011-015
    r"C:\Users\lianjie\.openclaw\workspace\media\inbound\openclaw-media-1778492230780-ciwqmk.jpg",  # 016-020
    r"C:\Users\lianjie\.openclaw\workspace\media\inbound\openclaw-media-1778492237969-9qy3g2.jpg",  # 021-025
    r"C:\Users\lianjie\.openclaw\workspace\media\inbound\openclaw-media-1778492246851-ztybql.jpg",  # 026-030
]

# Tesseract用英文模式（比分都是数字）
for idx, img_path in enumerate(img_paths):
    if not os.path.exists(img_path):
        print(f"[{idx+1}] 文件不存在: {img_path}")
        continue
    
    img = Image.open(img_path)
    orig_size = img.size
    
    # 比分列在截图右侧约75%-90%区域
    # 根据之前AI识别，比分列在图像右侧
    left = int(img.width * 0.70)
    right = int(img.width * 0.95)
    top = int(img.height * 0.15)  # 跳过顶部标题
    bottom = int(img.height * 0.95)  # 跳过底部
    
    # 裁剪比分列
    cropped = img.crop((left, top, right, bottom))
    
    # 放大3倍
    cropped = cropped.resize((cropped.width * 3, cropped.height * 3), Image.LANCZOS)
    
    # 转灰度
    cropped = cropped.convert('L')
    
    # 增强对比度
    enhancer = ImageEnhance.Contrast(cropped)
    cropped = enhancer.enhance(4.0)
    
    # 二值化
    cropped = cropped.point(lambda x: 0 if x < 100 else 255)
    
    # 保存
    out_path = rf"c:\temp\ocr_zhou{idx+1}.png"
    cropped.save(out_path)
    
    # Tesseract OCR（只识别英文数字）
    result = subprocess.run(
        ['tesseract', out_path, 'stdout', '--psm', '6', '-l', 'eng'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding='utf-8', errors='replace'
    )
    
    print(f"=== 第{idx+1}张（周日00{idx*5+1}-0{idx*5+5}）比分列 ===")
    print(result.stdout)
