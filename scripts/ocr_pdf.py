from paddleocr import PaddleOCR
import os

# 初始化OCR
ocr = PaddleOCR(lang='ch')

# 图片路径
images = [
    'pdf_image_p1_0.png',
    'pdf_image_p1_1.jpeg', 
    'pdf_image_p1_2.png',
    'pdf_image_p1_3.jpeg'
]

print("开始OCR识别...\n")

for img_path in images:
    if os.path.exists(img_path):
        print(f"\n=== 识别图片: {img_path} ===")
        result = ocr.predict(img_path)
        
        if result:
            for line in result:
                if hasattr(line, 'rec_texts'):
                    for text in line.rec_texts:
                        print(f"  {text}")
                elif isinstance(line, dict) and 'rec_texts' in line:
                    for text in line['rec_texts']:
                        print(f"  {text}")
                else:
                    print(f"  {line}")
        else:
            print("  未识别到文字")