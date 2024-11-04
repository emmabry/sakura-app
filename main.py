from dotenv import load_dotenv
import os
import deepl
from elevenlabs.client import ElevenLabs
import pytesseract
from PIL import Image
from flask import Flask, render_template, request, redirect, url_for

# Setting up program, global variables
load_dotenv()

VOICE_ID = 'j210dv0vWm7fCknyQpbA'
XI_API_KEY = os.getenv('XI_API_KEY')
TESSDATA_PREFIX = os.getenv('TESSDATA_PREFIX')

os.environ['TESSDATA_PREFIX'] = TESSDATA_PREFIX

client = ElevenLabs(api_key=XI_API_KEY)

translator = deepl.Translator(os.getenv('DEEPL_API_KEY'))
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
        japanese_text = img_to_text()
        translated_text = translate(japanese_text)
        audio = get_speech(japanese_text)
        audio_path = 'static/speech.mp3'
        with open(audio_path, 'wb') as f:
            f.write(audio)
        return render_template('tospeech.html', translation=translated_text, image=file_path, audio=audio_path)
    return render_template('tospeech.html')


# Uses ElevenLabs API to convert text to speech
def get_speech(requested_text):
    audio = client.generate(
        text=requested_text,
        voice=VOICE_ID,
        model="eleven_multilingual_v2"
    )
    audio_data = b''.join(list(audio))
    print(f"Audio data type: {type(audio_data)}, size: {len(audio_data)} bytes")
    return audio_data


# Uses pytesseract to convert image to text
def img_to_text():
    image = Image.open('static/to_translate.png')
    text = pytesseract.image_to_string(image, lang='jpn')
    print(f"img text: {text}")
    return text


def translate(img_txt):
    result = translator.translate_text(text=img_txt, target_lang='EN-US')
    print(result.text)
    return result.text


# japanese_text = img_to_text()
# get_speech(japanese_text)

if __name__ == '__main__':
    app.run(debug=True)
