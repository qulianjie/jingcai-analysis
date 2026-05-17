import os
import re
import json
import requests
import sys

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# 使用 pytesseract 或 easyocr 做 OCR
# 先检查是否安装了 tesseract
from PIL import Image
import subprocess

# Try tesseract
try:
    result = subprocess.run(['tesseract', '--version'], capture_output=True, timeout=5)
    print('Tesseract available:', result.stdout.decode().strip())
except:
    print('Tesseract not available')

# Try easyocr
try:
    import easyocr
    print('EasyOCR available')
except:
    print('EasyOCR not available')

# Try paddleocr
try:
    from paddleocr import PaddleOCR
    print('PaddleOCR available')
except:
    print('PaddleOCR not available')

# List available tools
print('\nAvailable OCR tools check complete')
