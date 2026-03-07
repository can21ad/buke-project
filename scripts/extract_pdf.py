import fitz

doc = fitz.open(r'D:\爬虫\未命名1_加水印.pdf')
print(f"总页数: {len(doc)}")

for i, page in enumerate(doc):
    text = page.get_text("text")
    print(f"\n=== 第{i+1}页 ===")
    print(text)
    
    # 也尝试提取图片
    images = page.get_images()
    if images:
        print(f"\n发现 {len(images)} 张图片")
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            with open(f"pdf_image_p{i+1}_{img_index}.{image_ext}", "wb") as f:
                f.write(image_bytes)
            print(f"  保存图片: pdf_image_p{i+1}_{img_index}.{image_ext}")

doc.close()