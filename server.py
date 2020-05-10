"""Сервер Telegram бота, запускаемый непосредственно"""
import os
import re
from _multiprocessing import send

import telebot
import exceptions
import expenses
from categories import Categories
from telebot import types

API_TOKEN = '1173771659:AAHY3aJR8xeOHgfFtDm6_Xk1c2JYpY1kyPo'

ACCESS_ID = os.getenv("TELEGRAM_ACCESS_ID")

bot = telebot.TeleBot(API_TOKEN)

user_id = ""
user_name = ""
user_limit = ""


@bot.message_handler(commands=['start'])
def one_step(message):
    global user_id
    user_id = message.chat.id
    look = expenses.get_user(user_id)
    if look == 'a':
        bot.send_message(message.chat.id, "Привет " + str(user_id) + ". Как тебя зовут?")
        bot.register_next_step_handler(message, second_step)
    else:

        bot.send_message(message.chat.id, "Ты уже зареган!")


def second_step(message):
    global user_name
    user_name = message.text
    bot.send_message(message.chat.id, "ОК! " + user_name + "! Введи сумму на день?!")
    bot.register_next_step_handler(message, last_step)


def last_step(message):
    global user_limit
    user_limit = message.text
    expenses.add_user(user_id, user_name, user_limit)
    bot.send_message(message.chat.id, user_name + ". Вводи сумму и выбери категорию!\n\n"
                                                  "Для помощи: /help")


@bot.message_handler(commands=['help'])
def send_welcome(message):
    """Отправляет приветственное сообщение и помощь по боту"""
    bot.send_message(message.chat.id,
                     "\U0001F4B0\U0001F4B2Бот для учёта расходов:\n\n"
                     "\U00002795Добавить расход: 250 + выбор категории\n"
                     "\U0000231BСегодняшняя статистика: /today\n"
                     "\U00002049За текущий месяц: /month\n"
                     "\U00002702Последние внесённые расходы: /expenses")
                     #"Категории трат: /categories")


@bot.message_handler(commands=['categories'])
def categories_list(message):
    """Отправляет список категорий расходов"""
    categories = Categories().get_all_categories()
    answer_message = "Категории трат:\n\n* " + \
                     ("\n* ".join([c.name + ' (' + ", ".join(c.aliases) + ')' for c in categories]))
    bot.send_message(message.chat.id, answer_message)


@bot.message_handler(commands=['today'])
def today_statistics(message):
    global user_id
    user_id = message.chat.id
    look = expenses.get_user(user_id)
    if look == 'a':
        bot.send_message(message.chat.id, "/start - регистрация")
    else:
        """Отправляет сегодняшнюю статистику трат"""
        answer_message = expenses.get_today_statistics(user_id)
        bot.send_message(message.chat.id, answer_message)


@bot.message_handler(commands=['month'])
def month_statistics(message):
    global user_id
    user_id = message.chat.id
    look = expenses.get_user(user_id)
    if look == 'a':
        bot.send_message(message.chat.id, "/start - регистрация")
    else:
        """Отправляет статистику трат текущего месяца"""
        answer_message = expenses.get_month_statistics(user_id)
        bot.send_message(message.chat.id, answer_message)


@bot.message_handler(commands=['expenses'])
def list_expenses(message):
    """Отправляет последние несколько записей о расходах"""
    global user_id
    user_id = message.chat.id
    look = expenses.get_user(user_id)
    if look == 'a':
        bot.send_message(message.chat.id, "/start - регистрация")
    else:
        last_expenses = expenses.last(user_id)
        if not last_expenses:
            bot.send_message(message.chat.id, "Расходы ещё не заведены")
            return

        last_expenses_rows = [
            f"{expense.amount} гр. на {expense.category_name} — нажми "
            f"/del{expense.id} для удаления"
            for expense in last_expenses]
        answer_message = "Последние сохранённые траты:\n\n* " + "\n\n* " \
            .join(last_expenses_rows)
        bot.send_message(message.chat.id, answer_message)


a = ''
b = ''


@bot.message_handler(content_types=['text'])
def add_sum(message):
    global a
    global user_id
    user_id = message.chat.id
    look = expenses.get_user(user_id)
    if look == 'a':
        bot.send_message(message.chat.id, "/start - регистрация")
    else:
        if re.match('/del\d{1,2}', message.text):
            """Удаляет одну запись о расходе по её идентификатору"""
            row_id = int(message.text[4:])
            expenses.delete_expense(row_id)
            answer_message = "Удалил"
            bot.send_message(message.chat.id, answer_message)
        elif message.text.isdigit():
            a = message.text
            markup = types.ReplyKeyboardMarkup()
            markup.row('\U0001F37B\U0001F379\U0001F370Кафе', '\U0001F34C\U0001F34D\U0001F357Продукты')
            markup.row('\U0001F457\U0001F454\U0001F45FДругое')
            bot.send_message(message.chat.id, "Выберите категорию", reply_markup=markup)
            bot.register_next_step_handler(message, add_expense)
        else:
            bot.send_message(message.chat.id, "Введи цифру долбоеб")


def add_expense(message):
    global b

    b = message.text
    c = a + ' ' + b
    try:
        expense = expenses.add_expense(c, user_id)
    except exceptions.NotCorrectMessage as e:
        bot.send_message(message.chat.id, str(e))
    answer_message = (
        f"Добавлены траты {expense.amount}  грн. на {expense.category_name}.\n\n"
        f"{expenses.get_today_statistics(user_id)}")
    bot.send_message(message.chat.id, answer_message)
    return


if __name__ == '__main__':
    bot.polling(none_stop=True)
