from img_to_speech import get_speech, img_to_text, translate
from login import LoginForm, RegistrationForm
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, Text, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy
import os

# App Config
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'data', 'sakura.db')}"

# Login Config
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# DB Config
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Vocab(db.Model):
    __tablename__ = 'vocab'
    id = Column(Integer, primary_key=True)
    word = Column(String)
    reading = Column(String)
    meaning = Column(Text)
    level = Column(String)


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(String)
    name = Column(String)
    email = Column(String)
    jlpt_level = Column(String)


class Set(db.Model):
    __tablename__ = 'flashcards'
    id = Column(Integer, primary_key=True)
    set = Column(String)
    word_id = Column(Integer, ForeignKey('vocab.id'))
    associated_user_id = Column(Integer)


@app.route('/')
def index():
    return render_template('index.html', logged_in=current_user.is_authenticated)


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        q = db.session.query(User.id).filter(User.email == form.email.data)
        AlreadyRegistered = db.session.query(q.exists()).scalar()
        if AlreadyRegistered:
            flash("Email already registered, login instead")
            return redirect(url_for('login'))
        else:
            hashed_password = generate_password_hash(form.password.data,
                                                     method='pbkdf2:sha256',
                                                     salt_length=8)
            new_user = User(email=form.email.data,
                            password=hashed_password,
                            username=form.username.data,
                            name=form.name.data,
                            jlpt_level=form.jlpt_level.data)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return render_template('loggedin.html', user=new_user, logged_in=current_user.is_authenticated)
    return render_template('register.html', form=form, logged_in=current_user.is_authenticated)


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        query = db.session.execute(db.select(User).where(User.username == form.username.data))
        user = query.scalar()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return render_template('loggedin.html', user=user, logged_in=current_user.is_authenticated)
        elif not user:
            flash('User does not exist.')
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, form.password.data):
            flash('Invalid password.')
            return redirect(url_for('login'))
    return render_template('login.html', form=form, logged_in=current_user.is_authenticated)


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/upload', methods=['POST', 'GET'])
def convert_image():
    if request.method == 'POST':
        file = request.files['file']
        file_path = 'static/to_translate.png'
        file.save(file_path)
        japanese_text = img_to_text().replace(" ", "")
        translated_text = translate(japanese_text)
        audio = get_speech(japanese_text, 'static/speech.mp3')
        return render_template('tospeech.html', translation=translated_text, image=file_path, audio=audio,
                               logged_in=current_user.is_authenticated)
    return render_template('tospeech.html', logged_in=current_user.is_authenticated)


@app.route('/vocab', methods=['GET'])
def get_vocab():
    if current_user.is_authenticated:
        jlpt_level = current_user.jlpt_level
    else:
        jlpt_level = 'N5'
    query = Vocab.query.filter_by(level=jlpt_level).order_by(func.random()).limit(3).all()
    entries = []
    n = 1
    for entry in query:
        mydict = {
            'id': entry.id,
            'kanji': entry.word,
            'reading': entry.reading,
            'meaning': entry.meaning,
            'audio_file': f'vocab{n}.mp3'
        }
        entries.append(mydict)
        get_speech(entry.reading, f'static/vocab{n}.mp3')
        n += 1
    return render_template('vocab.html', vocab_list=entries, logged_in=current_user.is_authenticated)


@app.route('/flashcards', methods=['POST', 'GET'])
def flashcards():
    return render_template('flashcards.html', logged_in=current_user.is_authenticated)


@app.route('/set/<set_id>', methods=['POST', 'GET'])
def show_set(set_id):
    query = db.session.execute(db.select(Set).where(Set.set == set_id).limit(20)).scalars().all()
    flashcard_set = {'title': f"{set_id} Flashcards",
                     'description': f'Here are the flashcards for JLPT level {set_id}.',
                     'data': {}}
    n = 1
    for entry in query:
        vocab_query = db.session.execute(db.select(Vocab).where(Vocab.id == entry.word_id)).scalars().all()
        for vocab_entry in vocab_query:
            mydict = {
                'id': vocab_entry.id,
                'kanji': vocab_entry.word,
                'reading': vocab_entry.reading,
                'meaning': vocab_entry.meaning,
                'audio_file': f'vocab{n}.mp3'
            }
            flashcard_set['data'][n] = mydict
            get_speech(vocab_entry.reading, f'static/vocab{n}.mp3')
            n += 1
    return render_template('set.html', flashcards=flashcard_set, logged_in=current_user.is_authenticated)

@app.route('/create', methods=['POST', 'GET'])
def create_deck():
    return render_template('create.html', logged_in=current_user.is_authenticated)


if __name__ == '__main__':
    app.run(debug=True)
