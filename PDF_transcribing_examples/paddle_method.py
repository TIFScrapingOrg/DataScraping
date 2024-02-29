from paddleocr import PaddleOCR
import time
# Paddleocr supports Chinese, English, French, German, Korean and Japanese.
# You can set the parameter `lang` as `ch`, `en`, `fr`, `german`, `korean`, `japan`
# to switch the language model in order.

start_time = time.time()

ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False) # need to run only once to download and load model into memory
pdf_path = 'T_003_43rdDamenAR98.pdf'
result = ocr.ocr(pdf_path, cls=False, bin=True)


with open("paddle_text.txt", 'a', encoding='utf-8') as output:
    
	for idx in range(len(result)):
		res = result[idx]

		if res is None:
			continue

		for line in res:
			# print(line[1][0])
			output.write(line[1][0] + "\n")

print(f'Operation took {time.time() - start_time} seconds')