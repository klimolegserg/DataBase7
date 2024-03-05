import random
import configparser

from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

from guide_bot1 import add_user, data_random, known_users, add_word, delete_word


print('Start telegram bot...')

config = configparser.ConfigParser()
config.read('settings.ini')
TOKEN = config['token']['token']
state_storage = StateMemoryStorage()
bot = TeleBot(TOKEN, state_storage=state_storage)

known_users = known_users()
buttons = []


def show_hint(*lines):
    """
    Формирует строку сообщения
    :param lines:
    :return:
    """
    return '\n'.join(lines)


def show_target(data):
    """
    Формирует строку ответа
    :param data:
    :return:
    """
    return f"{data['target_word']} -> {data['translate_word']}"


class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()


@bot.message_handler(commands=['cards', 'start'])
def create_cards(message):
    """
    Приветсвие и запрос в базу данных
    :param message:
    :return:
    """
    cid = message.chat.id
    if cid not in known_users:
        known_users.append(cid)
        add_user(cid)
        bot.send_message(cid, "Привет, давай изучать английский...")
    markup = types.ReplyKeyboardMarkup(row_width=2)

    global buttons
    buttons = []
    random_words = data_random(cid)
    target_word = random_words[0]
    translate = random_words[1]
    target_word_btn = types.KeyboardButton(target_word)
    buttons.append(target_word_btn)
    others = random_words[2]
    other_words_btns = [types.KeyboardButton(word) for word in others]
    buttons.extend(other_words_btns)
    random.shuffle(buttons)
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([next_btn, add_word_btn, delete_word_btn])

    markup.add(*buttons)

    greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate
        data['other_words'] = others


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    """
    Отправка сообщения и перенапраление в следующую функцию
    :param message:
    :return:
    """
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Слово для удаления')
    bot.register_next_step_handler(message, del_word)


def del_word(message):
    """ Связь с БД для удаления слов

    :param message:
    :return:
    """
    word = message.text
    cid = message.chat.id
    message_to_user = delete_word(cid, word)
    bottons3(message, message_to_user)


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)  # обработчик комманды
def write_word(message):
    """Отправляет сообщение в  перенаправляет в следующую функцию

    :param message:
    :return:
    """
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Введите новое слово на английском и его перевод на русском через пробел')
    bot.register_next_step_handler(message, save_word)


def save_word(message):
    """Взаимодействует с БД для добавления слов и запрашивает данные (f строку, кнопки)
            для дальнейшей передачи в telebot

    :param message:
    :return:
    """
    word = message.text
    word = word.split()
    cid = message.chat.id
    message_to_user = add_word(cid, word[0], word[1])
    bottons3(message, message_to_user)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)


def bottons3(message, message_to_user):
    """ вспомогательная функция формирования клавиатуры и передачи сообщения в telebot

    :param message:
    :param message_to_user:
    :return:
    """
    buttons3 = []
    markup = types.ReplyKeyboardMarkup(row_width=3)
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons3.extend([next_btn, add_word_btn, delete_word_btn])
    markup.add(*buttons3)
    bot.send_message(message.chat.id, message_to_user, reply_markup=markup)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    """
    Проверяет правильность ответа, в случае ошибки меняет кнопки
    :param message:
    :return:
    """
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        if text == target_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤", hint]
            next_btn = types.KeyboardButton(Command.NEXT)
            add_word_btn = types.KeyboardButton(Command.ADD_WORD)
            delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
            buttons.extend([next_btn, add_word_btn, delete_word_btn])
            hint = show_hint(*hint_text)
        else:
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '❌'
                    break
            hint = show_hint("Допущена ошибка!",
                             f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}")
    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)


bot.add_custom_filter(custom_filters.StateFilter(bot))

bot.infinity_polling(skip_pending=True)
