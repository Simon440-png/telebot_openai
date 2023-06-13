import telebot
import os
import sqlite3
import logging
from telebot import types

import config

API_TOKEN = config.panel_token

bot = telebot.TeleBot(API_TOKEN)
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

usr_id = {}
promocode = {}

logging.basicConfig(level=logging.INFO, filename="py_log1.log")
logging.debug("A DEBUG Message")
logging.info("An INFO")
logging.warning("A WARNING")
logging.error("An ERROR")
logging.critical("A message of CRITICAL severity")


def get_access_status(user_id):
    cursor.execute("SELECT * FROM auth WHERE id = ?", (str(user_id),))
    return bool(cursor.fetchone())


# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def start(message):
    if get_access_status(message.from_user.id):
        repkey = types.ReplyKeyboardMarkup(row_width=1)
        dobav = types.KeyboardButton('Add➕')
        udal = types.KeyboardButton('Delete❌')
        promo = types.KeyboardButton('Information about promo codeℹ️')
        repkey.add(dobav, udal, promo)
        bot.send_message(message.chat.id, "Hi, this is our bot control panel!", reply_markup=repkey)


def add(message):
    if get_access_status(message.from_user.id):
        keyboard = types.ReplyKeyboardMarkup(row_width=1)
        dobav = types.KeyboardButton('Back🔙')
        keyboard.add(dobav)
        data = bot.send_message(message.chat.id, "Enter ID to add", reply_markup=keyboard)
        bot.register_next_step_handler(data, add1)


def add1(message):
    usr_id[message.chat.id] = message.text
    if usr_id[message.chat.id] == 'Back🔙':
        start(message)
        return
    keyboard = types.ReplyKeyboardMarkup(row_width=1)
    promo = types.KeyboardButton('Yes✅')
    net = types.KeyboardButton('No❌')
    keyboard.add(promo, net)
    data = bot.send_message(message.chat.id, "Does the client have a promo code?", reply_markup=keyboard)
    bot.register_next_step_handler(data, add2)


def add2(message):
    data = message.text
    if data == 'No❌':
        try:
            cursor.execute("INSERT INTO users (id, promo) VALUES (?, 'None')", (str(usr_id[message.chat.id]),))
            conn.commit()
        except:
            bot.send_message(message.chat.id, "An error has occurred in sqlite3. Most likely you are trying to add an ID already in the database")
        else:
            bot.send_message(message.chat.id, "The user has been added to the database! To save changes enter /restart")
        start(message)
        return
    elif data == 'Yes✅':
        data2 = bot.send_message(message.chat.id, "Enter promo code. Attention! Before sending a promo code, thoroughly check the correctness of its spelling!")
        bot.register_next_step_handler(data2, add3)


def add3(message):
    promocode[message.chat.id] = message.text
    try:
        cursor.execute("INSERT INTO users (id, promo) VALUES (?, ?)", (str(usr_id[message.chat.id]),
                                                                       str(promocode[message.chat.id])))
        conn.commit()
    except:
        bot.send_message(message.chat.id, "An error has occurred in sqlite3. Most likely you are trying to add an ID already in the database")
    else:
        bot.send_message(message.chat.id, "The user has been added to the database! To save changes enter /restart")
    start(message)


def delete(message):
    if get_access_status(message.from_user.id):
        keyboard = types.ReplyKeyboardMarkup(row_width=1)
        dobav = types.KeyboardButton('Back🔙')
        keyboard.add(dobav)
        data = bot.send_message(message.chat.id, "Enter ID to delete", reply_markup=keyboard)
        bot.register_next_step_handler(data, delete1)


def delete1(message):
    data = message.text
    if data == 'Back🔙':
        start(message)
        return
    try:
        cursor.execute("DELETE FROM users WHERE id=?", (str(data),))
        conn.commit()
    except:
        bot.send_message(message.chat.id, "An error has occurred in sqlite3!")
    finally:
        bot.send_message(message.chat.id, "The user is deleted from the database, if the changes are over, then restart the bot with the command /restart")
    start(message)


def promo(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=1)
    dobav = types.KeyboardButton('Back🔙')
    keyboard.add(dobav)
    data = bot.send_message(message.chat.id, "Enter promo code", reply_markup=keyboard)
    bot.register_next_step_handler(data, promo1)
    
    
def promo1(message):
    codik = message.text
    if codik == 'Back🔙':
        start(message)
        return
    cursor.execute("SELECT COUNT(*) FROM users WHERE promo = ?", (str(codik),))
    use = cursor.fetchone()[0]
    bot.send_message(message.chat.id, f"*Promo code has been used* {use} *times*", parse_mode="Markdown")
    start(message)
    

@bot.message_handler(commands=['restart'])
def restart(message):
    if get_access_status(message.from_user.id):
        msg = bot.send_message(message.chat.id, "The bot will now restart...")
        msg_id = msg.message_id
        os.system("systemctl restart telegram-bot.service")
        bot.delete_message(message.chat.id, message_id=msg_id)
        bot.send_message(message.chat.id, "Bot restarted! All changes made")
        os.system("systemctl restart panel-bot.service")


@bot.message_handler(func=lambda call: True)
def echo_all(message):
    if get_access_status(message.from_user.id):
        if message.text == 'Add➕':
            add(message)
        elif message.text == 'Delete❌':
            delete(message)
        elif message.text == 'Information about promo codeℹ️':
            promo(message)


bot.infinity_polling()
