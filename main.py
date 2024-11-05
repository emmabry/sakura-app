from dotenv import load_dotenv
import os
from googletrans import Translator
from gtts import gTTS
import pytesseract
from PIL import Image
from flask import Flask, render_template, request

load_dotenv()

VOICE_ID = 'j210dv0vWm7fCknyQpbA'
XI_API_KEY = os.getenv('XI_API_KEY')
TESSDATA_PREFIX = os.getenv('TESSDATA_PREFIX')

os.environ['TESSDATA_PREFIX'] = TESSDATA_PREFIX


translator = Translator()
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST', 'GET'])
def convert_image():
    if request.method == 'POST':
        file = request.files['file']
        file_path = 'static/to_translate.png'
        file.save(file_path)
        japanese_text = img_to_text().replace(" ", "")
        translated_text = translate(japanese_text)
        audio = get_speech(japanese_text)
        return render_template('tospeech.html', translation=translated_text, image=file_path, audio=audio)
    return render_template('tospeech.html')


def get_speech(requested_text):
    tts = gTTS(requested_text, lang='ja')
    with open('static/speech.mp3', 'wb') as f:
        tts.write_to_fp(f)
    return tts


def img_to_text():
    image = Image.open('static/to_translate.png')
    text = pytesseract.image_to_string(image, lang='jpn')
    return text


def translate(img_txt):
    result = translator.translate(text=img_txt, src="ja", dest="en")
    return result.text


if __name__ == '__main__':
    app.run(debug=True)
