from PIL import Image
import re

# Read image 1 (wide screenshot)
img1 = Image.open(r'C:\Users\lianjie\.openclaw\workspace\media\inbound\openclaw-media-1778488366402-w3yznm.png')
print(f'Image 1 size: {img1.size}')

# Read image 2 (tall screenshot)
img2 = Image.open(r'C:\Users\lianjie\.openclaw\workspace\media\inbound\openclaw-media-1778488417172-rjn7jk.png')
print(f'Image 2 size: {img2.size}')

# Image 2 is 2366x762 - let's crop and look at specific regions
# The table has columns: match number, time, home, score, away
# Let's try to find the score regions

# First, let's just print some basic info
print(f'Image 1 mode: {img1.mode}')
print(f'Image 2 mode: {img2.mode}')

# Try to find text regions by looking at pixel differences
# For image 2, the table is likely in the middle portion
# Let's crop to the table area
w, h = img2.size
print(f'Image 2: {w}x{h}')

# Look at the bottom portion for matches 023+
bottom = img2.crop((0, h*3//4, w, h))
bottom.save(r'C:\Users\lianjie\.openclaw\workspace\jingcai\img2_bottom.png')
print('Saved bottom portion to img2_bottom.png')

# For image 1, look at specific regions
w1, h1 = img1.size
print(f'Image 1: {w1}x{h1}')

# The table in image 1 shows matches 001-030
# Let's try to find the score column
# Based on the layout, scores are likely in a column around x=800-1000
