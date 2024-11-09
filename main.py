from flask import Flask, render_template, request
from img_to_speech import get_speech, img_to_text, translate
from vocab import get_entries
from login import LoginForm, RegistrationForm, SECRET_KEY
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegistrationForm()
    return render_template('register.html', form=form)

@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    return render_template('login.html', form=form)

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


@app.route('/vocab', methods=['GET'])
def get_vocab():
    vocab_list = get_entries()
    return render_template('vocab.html', vocab_list=vocab_list)


if __name__ == '__main__':
    app.run(debug=True)
