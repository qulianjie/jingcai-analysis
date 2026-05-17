from PIL import Image, ImageEnhance, ImageFilter
import subprocess
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 读取图片
img_path = r'C:\Users\lianjie\.openclaw\workspace\media\inbound\openclaw-media-1778496784527-8qj12r.jpg'
img = Image.open(img_path)
print(f"图片尺寸: {img.size}")

# 先保存整个图片的放大版
img_big = img.resize((img.width * 4, img.height * 4), Image.LANCZOS)
img_big.save(r'c:\temp\full_006_010.png')

# 裁剪比分列（右侧约75%-95%）
left = int(img.width * 0.75)
right = int(img.width * 0.95)
top = int(img.height * 0.10)
bottom = int(img.height * 0.92)

score_col = img.crop((left, top, right, bottom))
score_col = score_col.resize((score_col.width * 6, score_col.height * 6), Image.LANCZOS)
score_col = score_col.convert('L')
enhancer = ImageEnhance.Contrast(score_col)
score_col = enhancer.enhance(5.0)
score_col = score_col.filter(ImageFilter.SHARPEN)
score_col = score_col.point(lambda x: 0 if x < 100 else 255)
score_col.save(r'c:\temp\score_col_006_010.png')

# 裁剪中间列（球队名，约30%-65%）
left2 = int(img.width * 0.30)
right2 = int(img.width * 0.65)

team_col = img.crop((left2, top, right2, bottom))
team_col = team_col.resize((team_col.width * 6, team_col.height * 6), Image.LANCZOS)
team_col = team_col.convert('L')
team_col = ImageEnhance.Contrast(team_col).enhance(5.0)
team_col = team_col.filter(ImageFilter.SHARPEN)
team_col = team_col.point(lambda x: 0 if x < 100 else 255)
team_col.save(r'c:\temp\team_col_006_010.png')

# 裁剪左侧列（编号+联赛，约5%-25%）
left3 = int(img.width * 0.05)
right3 = int(img.width * 0.25)

left_col = img.crop((left3, top, right3, bottom))
left_col = left_col.resize((left_col.width * 6, left_col.height * 6), Image.LANCZOS)
left_col = left_col.convert('L')
left_col = ImageEnhance.Contrast(left_col).enhance(5.0)
left_col = left_col.filter(ImageFilter.SHARPEN)
left_col = left_col.point(lambda x: 0 if x < 100 else 255)
left_col.save(r'c:\temp\left_col_006_010.png')

# OCR每列
for name, path in [('编号', 'c:\\temp\\left_col_006_010.png'), ('球队', 'c:\\temp\\team_col_006_010.png'), ('比分', 'c:\\temp\\score_col_006_010.png')]:
    result = subprocess.run(
        ['tesseract', path, 'stdout', '--psm', '6', '-l', 'eng'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    text = result.stdout.decode('utf-8', errors='replace').strip()
    print(f"\n=== {name}列 ===")
    print(text.encode('ascii', 'replace').decode('ascii'))
