from sqlalchemy import create_engine, Column, Integer, String, Text, func
from sqlalchemy.orm import sessionmaker, declarative_base
from gtts import gTTS

engine = create_engine('sqlite:///data/jmdict.db')

# Define a base class for declarative class definitions
Base = declarative_base()


# Define a model for the `entry` table
class Entry(Base):
    __tablename__ = 'entry'
    id = Column(Integer, primary_key=True)
    kanji = Column(String)
    reading = Column(String)
    gloss = Column(Text)
    position = Column(String)


# Create a session
Session = sessionmaker(bind=engine)
session = Session()


def get_entries():
    query = session.query(Entry).order_by(func.random()).limit(3).all()
    entries = []
    n = 1
    for entry in query:
        mydict = {
            'id': entry.id,
            'kanji': entry.kanji,
            'reading': entry.reading,
            'meaning': entry.gloss,
            'audio_file': f'vocab{n}.mp3'
        }
        entries.append(mydict)
        tts = gTTS(entry.reading, lang='ja')
        with open(f'static/vocab{n}.mp3', 'wb') as f:
            tts.write_to_fp(f)
        n += 1
        print(n)
    return entries
