#pip install easyocr

import easyocr
reader = easyocr.Reader(['ch_sim','en'])
result = reader.readtext('4.jpg', detail=0)
print(result)