from flask import Flask, Response
from flask import request
from flask import render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
import requests
import json
import random
import datetime

app = Flask(__name__)
Base = declarative_base()
engine = create_engine('postgres://wphkpkhwxuonpf:08efef3047b7e1e7295cc925260d7ef36db5b19b4c36cec78f3fc60eb585c138@ec2-54-247-94-127.eu-west-1.compute.amazonaws.com:5432/d3om4ibbro5t6f',echo=True)


Base.metadata.bind = engine
Session = sessionmaker(bind=engine)
session = Session()

TOKEN = "866710099:AAFzTiZ2UCkxNJpseteRry5w39VB1J4JlMI"
URL = f"https://api.telegram.org/bot{TOKEN}"
getUpdates = URL + "/getUpdates"

with open('english_words.json', 'r', encoding='utf-8') as j:
    words = json.load(j)

with open("keyboard.json", 'r', encoding='utf-8') as kf:
    reply_markup = json.load(kf)

random.seed(version=2)
questions = []


class Settings(Base):
    __tablename__ = 'Settings'
    id = Column(Integer, primary_key=True)
    time = Column(Integer, nullable=True)
    count = Column(Integer, nullable=True)
    right = Column(Integer, nullable=True)



class Users(Base):
    __tablename__ = 'Users'
    User_id = Column(Integer, primary_key=True)
    Name = Column(String(50), nullable=False)
    last_ans = Column(String(50), nullable=True)
    last_ans_count = Column(Integer, nullable=True)
    last_position = Column(Integer, nullable=True)
    last_try_count = Column(Integer, nullable=True)
    last_word = Column(String(50), nullable=True)
    mutex = Column(Integer, nullable=True)

    def Create(self, User_id, Name, last_ans=None, last_ans_count=None, last_position=-1, last_try_count=0, last_word='', mutex=0):
        session = Session()
        user = Users(User_id=User_id, Name=Name, last_ans=last_ans, last_ans_count=last_ans_count,
                     last_position=last_position, last_try_count=last_try_count,last_word=last_word, mutex=mutex)
        session.add(user)
        session.commit()
        session.close()

    def Find(self,User_id):
        session = Session()
        FindUser = session.query(Users).filter_by(User_id=User_id).first()
        session.close()
        return FindUser

    def Update(self,User_id, last_ans=None, last_ans_count=None, last_position=None, last_try_count=None, last_word=None, mutex=None):
        session = Session()
        FindUser = session.query(Users).filter_by(User_id=User_id).first()
        if FindUser is not None:
            if last_ans is not None:
                FindUser.last_ans = last_ans
            if last_ans_count is not None:
                FindUser.last_ans_count = last_ans_count
            if last_position is not None:
                FindUser.last_position = last_position
            if last_try_count is not None:
                FindUser.last_try_count = last_try_count
            if last_word is not None:
                FindUser.last_word = last_word
            if mutex is not None:
                FindUser.mutex = mutex
            session.add(FindUser)
            session.commit()  
        session.close()

class Learning(Base):
    __tablename__ = 'Learning'
    ID_learning = Column(Integer, primary_key=True)
    User_id = Column(Integer, ForeignKey('Users.User_id'))
    word = Column(String(50), nullable=True)
    count_ = Column(Integer, nullable=True)
    last_ans = Column(String(50), nullable=True)
    user_id = relationship(Users)

    def Create(self, User_id, word, count_, last_ans):
        session = Session()
        learn = Learning(User_id=User_id, word=word, count_=count_, last_ans=last_ans)
        session.add(learn)
        session.commit()
        session.close()

    def Find(self, User_id, word):
        session = Session()
        FindLearn = session.query(Learning).filter_by(User_id=User_id, word=word).first()
        session.close()
        return FindLearn

    def Update(self, User_id, word, count_=None, last_ans=None):
        session = Session()
        FindLearn = session.query(Learning).filter_by(User_id=User_id, word=word).first()
        if FindLearn is not None:
            if count_ is not None:
                FindLearn.count_ = count_
            if last_ans is not None:
                FindLearn.last_ans = last_ans
            session.add(FindLearn)
            session.commit()
        session.close()

Base.metadata.create_all(engine)
    
UsersDB = Users()
LearningDB = Learning()

@app.route('/incoming', methods=['POST', 'GET'])
def incoming():
    if request.method == 'POST':
        result = request.json
    massage = result["message"]
    chat = massage["chat"]
    chatID = chat["id"]
    text = massage["text"]
    FName = chat["first_name"]
    LName = chat["last_name"]
    params = {
        "chat_id": chatID,
        "text": ''
    }
    session = Session()
    stgs = session.query(Settings).first()
    session.close()
    IsFind = False
    FindUser = ''
    FindUser = UsersDB.Find(User_id = chatID)
    if not FindUser:
        UsersDB.Create(User_id=chatID,Name= FName)
        FindUser = UsersDB.Find(User_id = chatID)
    if FindUser.mutex != 0:
        return "end"
    else:
        UsersDB.Update(chatID,mutex=1)
        FindUser = UsersDB.Find(User_id = chatID)
    go_button = {"keyboard": [["Начать игру"],["Просмотр прогресса"]], "resize_keyboard": True}
    if text == '/start' and FindUser.last_position == -1:
        params["text"] = f'Привет {FName}, я бот который поможет тебе выучить английский ' \
                         f'Это просто. Нажми "Начать игру" и выбирай правильный перевод слов   ' \
                         f'из предложенных вариантов. Не бойся я скажу если ты где то ошибся. ' \
                         f'Слов в раунде будет {stgs.count}. Ну что поехали ? '
        params['reply_markup'] = json.dumps(go_button)
        requests.get(URL + "/sendMessage", params=params)
    if text == '/start' and FindUser.last_position != -1:
        UsersDB.Update(chatID, mutex=0)
        FindUser = UsersDB.Find(User_id = chatID)
        return Response(status=200)
    print(text)
    if text == "Отложить":
        UsersDB.Update(chatID, mutex=0)
        FindUser = UsersDB.Find(User_id = chatID)
        return "end"
    if text == "Начать игру" and FindUser.last_position == -1:
        UsersDB.Update(User_id=FindUser.User_id,last_ans_count= 0,last_try_count=FindUser.last_try_count +1 ,last_position= 0)
        FindUser = UsersDB.Find(User_id = chatID)
    if text == "Начать игру" and FindUser.last_position > 0:
        UsersDB.Update(chatID, mutex=0)
        FindUser = UsersDB.Find(User_id = chatID)
        return Response(status=200)

    if FindUser.last_word != '' and FindUser.last_word is not None:
        word = ""
        for item in words:
            if item['word'] == FindUser.last_word:
                word = item
                break
        if text == "привести пример":
            params['text'] = random.choice(word['examples'])
            requests.get(URL + "/sendMessage", params=params)
            UsersDB.Update(chatID, mutex=0)
            FindUser = UsersDB.Find(User_id = chatID)
            return 'end'
        else:
            if text== word['translation']:
                params['text'] = 'Хей молодец это правильный ответ '
                requests.get(URL + "/sendMessage", params=params)
                UsersDB.Update(User_id=FindUser.User_id,
                               last_ans_count=(FindUser.last_ans_count+1),
                               last_ans = str(datetime.datetime.now()))
                FindUser = UsersDB.Find(User_id = chatID)
                count = LearningDB.Find(User_id= chatID,word = word['word'])
                if not count:
                    LearningDB.Create(User_id= chatID,word=word['word'],count_=1,last_ans=str(datetime.datetime.now()))
                else:
                    LearningDB.Update(User_id=chatID,word = word['word'],count_=count.count_+1,last_ans=str(datetime.datetime.now()) )
            else:
                params['text'] = f'Упс... ошибочка ' \
                                 f'Правильный ответ : {word["translation"]}'
                requests.get(URL + "/sendMessage", params=params)
                UsersDB.Update(User_id= chatID,last_ans= str(datetime.datetime.now()))
                FindUser = UsersDB.Find(User_id = chatID)

    if FindUser.last_position in range(0, stgs.count):
        isFind = False
        while not isFind:
            word = random.choice(words)
            count = LearningDB.Find(User_id= chatID,word = word['word'])
            if count and count.count_ < FindUser.last_ans_count-1 and count.count_ <= stgs.right:
                isFind = True
            if not count:
                isFind = True

        ansvers = []
        ansvers.append(word["translation"])
        n = 1
        while n < 4:
            wordIsFind = False
            get = random.choice(words)
            for var in ansvers:
                if var == get["translation"]:
                    wordIsFind = True
            if not wordIsFind:
                ansvers.append(get["translation"])
                n += 1
        random.shuffle(ansvers)
        reply_markup["keyboard"][0][0] = ansvers[0]
        reply_markup["keyboard"][0][1] = ansvers[1]
        reply_markup["keyboard"][1][0] = ansvers[2]
        reply_markup["keyboard"][1][1] = ansvers[3]
        params['reply_markup'] = json.dumps(reply_markup)
        params['text'] = word['word']

        UsersDB.Update(User_id=chatID,last_word=word['word'], last_position=FindUser.last_position+1)
        FindUser = UsersDB.Find(User_id = chatID)
        requests.get(URL + "/sendMessage", params=params)
        UsersDB.Update(chatID, mutex=0)
        FindUser = UsersDB.Find(User_id = chatID)
        return "end"
    if FindUser.last_position >= stgs.count:

        params["text"] = f'Молодец,{FName}, игра окончена, ты правильно перевел(а) {FindUser.last_ans_count} слов  из {stgs.count}. ' \
                         f'Попробуем еще раз ?'
        params['reply_markup'] = json.dumps(go_button)
        requests.get(URL + "/sendMessage", params=params)
        UsersDB.Update(User_id=chatID, last_word='', last_position=-1, last_ans_count=0)
        UsersDB.Update(chatID, mutex=0)
        FindUser = UsersDB.Find(User_id = chatID)
        return "end"

    if text == "Посмотреть прогресс":
        session = Session()
        learned_words = session.query(Learning).filter(Learning.count_ >= stgs.right).all()
        learning_words = session.query(Learning).filter(Learning.count_ < stgs.right).all()
        last_ans = FindUser.last_ans
        count_learned_words = len(learned_words)
        count_learning_words = len(learning_words)
        params['text'] = f'{FName},  это твой прогресс \n' \
                         f'Слов выучено: {count_learned_words} \n' \
                         f'Слов изучается: {count_learning_words} \n' \
                         f'Последнее время прохождения теста: \n' \
                         f'{last_ans}'
        session.close()
        requests.get(URL + "/sendMessage", params=params)
    UsersDB.Update(chatID, mutex=0)
    FindUser = UsersDB.Find(User_id = chatID)
    return "end"

@app.route('/', methods=['GET'])
def index():
    return render_template("index.html")


@app.route('/settings')
def settings():
    session = Session()
    stgs = session.query(Settings).first()
    session.close()
    if stgs is not None: 
        return render_template("settings.html", time=stgs.time,count=stgs.count,right=stgs.right)
    else:
        return render_template("settings.html", time=2,count=2,right=2)

@app.route('/setup', methods=['POST'])
def setup():
    session = Session()
    time = int(request.form.get('time'))
    count = int(request.form.get('count'))
    right = int(request.form.get('right'))
    stgs = session.query(Settings).first()
    if stgs is not None:
        stgs.time=time
        stgs.count=count
        stgs.right=right
        session.add(stgs)
        session.commit()
    else:
        stgsCr = Settings(id=1, time=time, count=count, right=right)
        session.add(stgsCr)
        session.commit()
    session.close()
    return render_template("index.html")

if __name__ == '__main__':
    app.run()
