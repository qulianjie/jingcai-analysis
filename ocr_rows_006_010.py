from PIL import Image, ImageEnhance, ImageFilter
import subprocess
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

img_path = r'C:\Users\lianjie\.openclaw\workspace\media\inbound\openclaw-media-1778496784527-8qj12r.jpg'
img = Image.open(img_path)
print(f"图片尺寸: {img.size}")

# 比分列区域
left = int(img.width * 0.75)
right = int(img.width * 0.95)
top = int(img.height * 0.10)
bottom = int(img.height * 0.92)

score_col = img.crop((left, top, right, bottom))
score_col = score_col.resize((score_col.width * 6, score_col.height * 6), Image.LANCZOS)
score_col = score_col.convert('L')
score_col = ImageEnhance.Contrast(score_col).enhance(5.0)
score_col = score_col.filter(ImageFilter.SHARPEN)
score_col = score_col.point(lambda x: 0 if x < 100 else 255)

# 5场比赛，均匀分割
h = score_col.height
row_h = h // 5

for i in range(5):
    y_start = row_h * i + int(row_h * 0.15)
    y_end = row_h * (i + 1) - int(row_h * 0.15)
    
    row = score_col.crop((0, y_start, score_col.width, y_end))
    out = rf'c:\temp\row_{i+1}_006_010.png'
    row.save(out)
    
    # 尝试多种PSM
    for psm in ['6', '7', '13']:
        result = subprocess.run(
            ['tesseract', out, 'stdout', '--psm', psm, '-l', 'eng'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        text = result.stdout.decode('utf-8', errors='replace').strip()
        # 只提取数字和冒号/横线
        import re
        scores = re.findall(r'[\d]+[:\-][\d]+', text)
        if scores:
            print(f"第{i+1}场(PSM{psm}): {scores}")
            break
    else:
        # 没找到比分格式，输出原始文本
        result = subprocess.run(
            ['tesseract', out, 'stdout', '--psm', '7', '-l', 'eng'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        text = result.stdout.decode('utf-8', errors='replace').strip()
        print(f"第{i+1}场: '{text}'")
