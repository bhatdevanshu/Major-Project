import cv2
import numpy
import os
from google.cloud import vision

from pdf2image import convert_from_path

images = convert_from_path('example3.pdf', poppler_path = r"C:\\Users\\bhatd\\Downloads\\Release-22.04.0-0\\poppler-22.04.0\\Library\\bin" )
data = ""
for i in range(len(images)):

    crop_img = cv2.cvtColor(numpy.array(images[i]), cv2.COLOR_RGB2BGR)
    os.environ['GOOGLE_APPLICATION_CREDENTIALS']="C:\\RomelMajorProject\\final-year-ocr-project-68938-34c2f7e4e5f6.json"

    img_str = cv2.imencode('.png', crop_img)[1].tostring()
    image = vision.Image(content=img_str)
    client = vision.ImageAnnotatorClient()
    response = client.text_detection(image=image, image_context={"language_hints": ["en"]})
    texts = response.full_text_annotation
    data += texts.text

print(data)



