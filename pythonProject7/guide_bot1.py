import telebot
import random
import configparser

import sqlalchemy as sq

from sqlalchemy.orm import declarative_base, sessionmaker, relationship

config = configparser.ConfigParser()
config.read('settings.ini')
DSN = config['token']['dsn']
Base = declarative_base()

engine = sq.create_engine(DSN)

Session = sessionmaker(bind=engine)
session = Session()


class User(Base):
    """
    Класс таблица пользователей
    """

    __tablename__ = "user"

    id = sq.Column(sq.Integer, primary_key=True)
    cid = sq.Column(sq.Integer, unique=True)
    words = relationship("User_Word", backref='user')


class Word(Base):
    """
    Класс таблица слов
    """

    __tablename__ = "word"

    id = sq.Column(sq.Integer, primary_key=True)
    target_word = sq.Column(sq.String(length=20), unique=True)
    translate = sq.Column(sq.String(length=20), unique=True)
    user = relationship("User_Word", backref='word')


class User_Word(Base):
    """
    Класс таблица-связка уникальных ключей
    """

    __tablename__ = "user_word"

    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey("user.id"))
    word_id = sq.Column(sq.Integer, sq.ForeignKey("word.id"))


def create_tables(engine):
    """
    Создание таблиц
    :param engine:
    :return:
    """

    Base.metadata.create_all(engine)


def insert_tables():
    """
    Заполнение таблиц данными
    :return:
    """

    words = session.query(Word.id).all()
    if len(words) < 1:
        word1 = Word(id=101, translate='красный', target_word='red')
        word2 = Word(id=102, translate='зелёный', target_word='green')
        word3 = Word(id=103, translate='голубой', target_word='blue')
        word4 = Word(id=104, translate='жёлтый', target_word='yellow')
        word5 = Word(id=105, translate='яблоко', target_word='apple')
        word6 = Word(id=106, translate='абрикос', target_word='apricot')
        word7 = Word(id=107, translate='слива', target_word='plum')
        word8 = Word(id=108, translate='груша', target_word='pear')
        word9 = Word(id=109, translate='самолёт', target_word='plane')
        word10 = Word(id=110, translate='поезд', target_word='train')
        word11 = Word(id=111, translate='машина', target_word='car')
        word12 = Word(id=112, translate='корабль', target_word='ship')
        session.add_all([word1, word2, word3, word4, word5, word6, word7, word8, word9, word10, word11, word12])
        session.commit()


def add_user(cid):
    """
    Добавляет пользователя
    :param cid:
    :return:
    """

    user = User(cid=cid)
    session.add(user)
    session.commit()
    user_id = get_user(cid)
    insert_firstWord(user_id)


def insert_firstWord(user_id):
    """  присваивания начальной базы слов

    :param user_id:
    :return:
    """
    for el in range(101, 112):
        user_words = User_Word(user_id=user_id, word_id=el)
        session.add(user_words)
        session.commit()


def data_random(cid):
    """ получает рандомно слова с переводом и список слов для клавиш
         для конкретного пользователя

    :param cid:
    :return:
    """
    data = {}
    user_id = get_user(cid)
    res = session.query(Word)\
        .with_entities(Word.target_word, Word.translate) \
        .join(User_Word, User_Word.word_id == Word.id) \
        .filter(User_Word.user_id == user_id)
    for d in res.all():
        data.update({d[0]: d[1]})
    list_words = list(data.keys())
    data_r = random.choices(list_words)
    list_words.remove(data_r[0])
    random.shuffle(list_words)
    list_words = list_words[:4]
    return data_r[0], data[data_r[0]], list_words


def get_user(cid):
    """ вспомогательная функция для определения id юзера

    :param cid:
    :return:
    """
    user_id = session.query(User.id).filter(User.cid == cid)
    return user_id.first()[0]


def known_users():
    """формирует список юзеров из таблицы user

    :return: list(users)
    """
    users = []
    for user in session.query(User.cid).all():
        users += user
    return users


def add_word(cid, word, translate):
    """функция проверяет наличие слова в базе и в случае отстутствия заносит его с переводом в базу даннх
      а также закрепляет его за юзером
      выводит результат

    :param cid: уникальный id юзера (telebot)
    :param word: новое слово от юзера
    :param translate: перевод нового слова
    :return: f строка с результатом
    """
    list_words = []
    v = []
    user_id = get_user(cid)
    words = session.query(Word.target_word).all()
    for er in words:
        list_words += er
    if [word] not in list_words:
        session.add(Word(target_word=word, translate=translate))
        word_id = session.query(Word.id).filter(Word.target_word == word).first()[0]
        session.add(User_Word(user_id=user_id, word_id=word_id))
        result_last = count_words(user_id, word, translate)
    else:
        word_id = session.query(Word.id).filter(Word.target_word == word).first()[0]
        word_user_id = session.query(User_Word.word_id).filter(User_Word.user_id == user_id).all()
        for ed in word_user_id:
            v += ed
        if [word_id] not in v:
            session.add(User_Word(user_id=user_id, word_id=word_id))
            result_last = count_words(user_id, word, translate)
        else:
            result_last = f'слово {word} уже есть в вашей базе'
    session.commit()
    return result_last


def count_words(user_id, word, translate):
    """ Количество слов для данного пользователя

    :param user_id:
    :param word:
    :param translate:
    :return:
    """
    count_w = session.query(User_Word.word_id).filter(User_Word.user_id == user_id).count()
    result = (f'Добавлено слово -"{word}" и его перевод - "{translate}" \n '
              f'Общее количество слов в твоей базе - {count_w}')
    return result


def delete_word(cid, word):

    """функция удаляет слово, принимаемое от юзера из его базы (при его наличии)
         Выводит результат

    :param cid:
    :param word:
    :return:
    """
    list_words = []
    w = []
    user_id = get_user(cid)
    result = f'Слово "{word}" удалить нельзя. Слово отсутствует или находится в "базовом списке"'
    words = session.query(Word.target_word).filter(Word.id < 101).all()
    for el in words:
        list_words += el
    if [word] in list_words:
        word_id = session.query(Word.id).filter(Word.target_word == word).first()[0]
        word_user_id = session.query(User_Word.word_id).filter(User_Word.user_id == user_id).all()
        for ek in word_user_id:
            w += ek
        if [word_id] in w:
            session.query(User_Word).filter(User_Word.user_id == user_id, User_Word.word_id == word_id).delete()
            session.commit()
            result_last = f'слово "{word}" успешно удалено из вашего списка'
        else:
            result_last = result
    else:
        result_last = result
    return result_last


config.read('settings.ini')
TOKEN = config['token']['token']
bot = telebot.TeleBot(TOKEN)


#
#
# YANDEX_TOKEN = 'YANDEX_TOKEN'
# HOST_YANDEX_DISK = 'https://cloud-api.yandex.net:443'
#
#
# @bot.message_handler(commands=['create_folder'])
# def create_folder_handler(message):
#     chat_id = message.chat.id
#     msg = bot.send_message(chat_id, 'Введите название папки')
#     bot.register_next_step_handler(msg, create_folder)
#
#
# def create_folder(message):
#     path = message.text
#     headers = {'Authorization': 'OAuth %s' % YANDEX_TOKEN}
#     request_url = HOST_YANDEX_DISK + '/v1/disk/resources?path=%s' % path
#     response = requests.put(url=request_url, headers=headers)
#     if response.status_code == 201:
#         bot.reply_to(message, "Я создал папку %s" % path)
#     else:
#         bot.reply_to(message, '\n'.join(["Произошла ошибка. Текст ошибки", response.text]))
#
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет. Я учебный бот Нетологии")


@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.reply_to(message, "Вы вызвали команду help. Но я ещё ничего не умею")


if __name__ == '__main__':
    print('Бот запущен...')
    print('Для завершения нажмите Ctrl+Z')
    bot.polling()
