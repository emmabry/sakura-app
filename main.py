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


class FlashcardSet(db.Model):
    __tablename__ = 'FlashcardSet'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(Text)
    associated_user_id = Column(Integer)

class Flashcard(db.Model):
    __tablename__ = 'Flashcard'
    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey('vocab.id'))
    set_id = Column(Integer, ForeignKey('FlashcardSet.id'))

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
    set = db.session.execute(db.select(FlashcardSet).where(FlashcardSet.id == set_id)).scalar()
    flashcard_set = {'title': set.title,
                     'description': set.description,
                     'data': {}}
    n = 1
    cards = db.session.execute(db.select(Flashcard).where(Flashcard.set_id == set.id).limit(20)).scalars().all()
    for card in cards:
        word = db.session.execute(db.select(Vocab).where(Vocab.id == card.word_id)).scalar()
        word_data = {
            'id': word.id,
            'kanji': word.word,
            'reading': word.reading,
            'meaning': word.meaning,
            'audio_file': f'vocab{n}.mp3'
        }
        flashcard_set['data'][n] = word_data
        get_speech(word.reading, f'static/vocab{n}.mp3')
        n += 1
    return render_template('set.html', flashcards=flashcard_set, logged_in=current_user.is_authenticated)

@app.route('/user_set/<set_id>', methods=['POST', 'GET'])
def get_user_set(set_id):
    query = db.session.execute(db.select(Set).where(Set.set == set_id).limit(20)).scalars().all()
    flashcard_set = {
        'title': set_id,
        'description': '',
        'data': {}
    }
    n = 1
    for entry in query:
        if not flashcard_set['description']:
            flashcard_set['description'] = entry.description
        vocab_entry = Vocab.query.filter_by(id=entry.word_id).first()
        if vocab_entry:
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
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('desc')
        kanji_list = request.form.getlist('kanji[]')
        reading_list = request.form.getlist('reading[]')
        definition_list = request.form.getlist('definition[]')
        # Create FlashcardSet
        set_entry = FlashcardSet(title=title, description=description, associated_user_id=current_user.id)
        db.session.add(set_entry)
        db.session.commit()
        # Get word from database if exists
        for kanji, reading, definition in zip(kanji_list, reading_list, definition_list):
            vocab_entry = Vocab.query.filter_by(reading=reading).first()
            if vocab_entry:
                word_id = vocab_entry.id
            else:
                new_vocab = Vocab(word=kanji, reading=reading, meaning=definition, level=current_user.jlpt_level)
                db.session.add(new_vocab)
                db.session.commit()
                word_id = new_vocab.id
            flashcard = Flashcard(set_id=set_entry.id, word_id=word_id)
            db.session.add(flashcard)
            db.session.commit()
            print(set_entry.id)
        return redirect(url_for('show_set', set_id=set_entry.id))
    return render_template('create.html', logged_in=current_user.is_authenticated)


@app.route('/check_database', methods=['GET'])
def check_database():
    reading = request.args.get('reading')
    vocab_entry = Vocab.query.filter_by(reading=reading).first()
    if vocab_entry:
        return {'definition': vocab_entry.meaning}
    else:
        return {'definition': None}


if __name__ == '__main__':
    app.run(debug=True)

