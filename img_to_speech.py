from dotenv import load_dotenv
import os
from googletrans import Translator
from gtts import gTTS
import pytesseract
from PIL import Image

load_dotenv()

TESSDATA_PREFIX = os.getenv('TESSDATA_PREFIX')
os.environ['TESSDATA_PREFIX'] = TESSDATA_PREFIX
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

def get_speech(requested_text, filepath):
    tts = gTTS(requested_text, lang='ja')
    with open(filepath, 'wb') as f:
        tts.write_to_fp(f)
    return tts


def img_to_text():
    image = Image.open('static/to_translate.png')
    text = pytesseract.image_to_string(image, lang='jpn')
    return text

def translate(img_txt):
    translator = Translator()
    result = translator.translate(text=img_txt, src="ja", dest="en")
    return result.text
