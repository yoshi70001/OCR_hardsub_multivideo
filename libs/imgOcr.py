from rapidocr_onnxruntime import RapidOCR

engine = RapidOCR()

# img_path = 'tests/test_files/ch_en_num.jpg'
# result, elapse = engine(img_path)
# print(result)
# print(elapse)

def ocrImg(imagePath):
    return engine(imagePath)