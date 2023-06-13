import openai
import telebot
import logging
from telebot import types
import config
import sqlite3
import time

task = {}
count = {}
text = {}
completion = {}
fhoto = {}
use = {}
sent = {}

openai.api_key = config.openai_token
token = config.telebot_token
bot = telebot.TeleBot(token)
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()


logging.basicConfig(level=logging.INFO, filename="py_log.log")
logging.debug("A DEBUG Message")
logging.info("An INFO")
logging.warning("A WARNING")
logging.error("An ERROR")
logging.critical("A message of CRITICAL severity")


def get_access_status(user_id):
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return bool(cursor.fetchone())


def get_access_status_admin(user_id):
    cursor.execute("SELECT * FROM auth WHERE id = ?", (user_id,))
    return bool(cursor.fetchone())


def trial_add(user_id):
    cursor.execute("SELECT * FROM trial where id=?", (str(user_id),))
    result = cursor.fetchone()
    if result:
        return False
    join_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO trial (id, join_time) VALUES (?, ?)", (str(user_id), str(join_time),))
    conn.commit()
    return True


def trial_check(user_id):
    cursor.execute("SELECT * FROM trial where id=?", (str(user_id),))
    result = cursor.fetchone()
    if result:
        join_time = datetime.strptime(result[1], '%Y-%m-%d %H:%M:%S')
        current_time = datetime.now()
        trial_period = timedelta(hours=int(config.trial))
        if current_time - join_time >= trial_period:
            return False
        else:
            return True
    else:
        return False


@bot.message_handler(commands=["start"])
def start(message):
    if get_access_status(message.from_user.id):
        repkey = types.ReplyKeyboardMarkup(row_width=1)
        gen = types.KeyboardButton('Select AI🤖')
        rate = types.KeyboardButton('Feedback🌟')
        support = types.KeyboardButton('Support👥')
        ref = types.KeyboardButton('Referral program💵')
        repkey.add(gen, rate, support, ref)
        bot.send_message(message.chat.id, "Hey, this is a bot that does most, if not all of the OpenAI products. If you have any questions about using the bot, then look at the /help command or write to support. You can also check out our channel, where information about those is laid out. works and updates: @dalle_channel", reply_markup=repkey)
    # else: keyboard = types.InlineKeyboardMarkup() button1 = types.InlineKeyboardButton(text="Подробнее",
    # callback_data="podr") keyboard.add(button1) bot.send_message(message.chat.id, 'У вас не приобретён доступ!'
    # 'Чтобы купить его нажмите на кнопку "Подробнее"', reply_markup=keyboard)
    else:
        keyboard = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton(text="Trial period", callback_data="trial")
        keyboard.add(button1)
        bot.send_message(message.chat.id, "You have not purchased access to our bot, you can purchase it by writing @Karlet_y or take a trial period of 3 days",
                         reply_markup=keyboard)


def podr(message):
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text="Pay", callback_data="oplat", url="")
    keyboard.add(button1)
    bot.send_message(message.chat.id, f"You can purchase access to the bot for {config.dostup_cost} rubles. To pay, click on the Pay button, if you have any problems with payment, you can contact support: @sloniko")


@bot.message_handler(commands=['rate'])
def rate(message):
    if get_access_status(message.from_user.id):
        bot.send_message(message.chat.id, "In the form below, you can leave a review about our bot for further transfer to its developers: https://forms.gle/AQi1jYNCUkYVVjmX9")
    else:
        keyboard = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton(text="Trial period", callback_data="trial")
        keyboard.add(button1)
        bot.send_message(message.chat.id, "You have not purchased access to our bot, you can purchase it by writing @Karlet_y or take a trial period of 3 days",
                         reply_markup=keyboard)

@bot.message_handler(commands=["send"])
def send(message):
    if get_access_status_admin(message.from_user.id):
        data = bot.send_message(message.chat.id, "Enter text to send")
        bot.register_next_step_handler(data, send1)


def send1(message):
    sent[message.chat.id] = message.text
    cursor.execute("SELECT id FROM users")
    results = cursor.fetchall()
    for i in range(len(results)):
        try:
            time.sleep(1)
            bot.send_message(results[i][0], sent[message.chat.id])
        except:
            continue


@bot.message_handler(commands=["help"])
def helpme(message):
    if get_access_status(message.from_user.id):
        bot.send_message(message.chat.id, "This bot uses the official openAI API. This bot is developed by one person and does not serve commercial purposes.\nBot commands:\n/rate - leave feedback about the bot\n/help - display this message\n/start - display a welcome message or start the bot")
    else:
        keyboard = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton(text="Trial period", callback_data="trial")
        keyboard.add(button1)
        bot.send_message(message.chat.id, "You have not purchased access to our bot, you can purchase it by writing @Karlet_y or take a trial period of 3 days",
                         reply_markup=keyboard)

def startgpt(message):
    data = bot.send_message(message.chat.id, 'Hi, I am ChatGPT by OpenAI. You can ask me a question or just talk.\nExamples:\n"Write a Telegram bot"\n"Which is better, Western Digital or Kingston?"')
    bot.register_next_step_handler(data, chatgpt2)


def chatgpt(message):
    repkey = types.ReplyKeyboardMarkup(row_width=1)
    stop = types.KeyboardButton('Stop ChatGPT⛔')
    repkey.add(stop)
    bot.delete_message(message.chat.id, message_id=msg_id)
    data = bot.send_message(message.chat.id, completion[message.chat.id]['choices'][0]['message']['content'],
                            reply_markup=repkey)
    bot.register_next_step_handler(data, chatgpt2)


def chatgpt2(message):
    global completion
    text[message.chat.id] = message.text
    if text[message.chat.id] == 'Stop ChatGPT⛔':
        start(message)
        return
    else:
        pass
    try:
        msg = bot.send_message(message.chat.id, "ChatGPT typing...")
        global msg_id
        msg_id = msg.message_id
        completion[message.chat.id] = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": text[message.chat.id]}]
        )
    except openai.error.RateLimitError:
        bot.send_message(message.chat.id, "There are problems with the API, please try again later. To return to the menu, enter "
                                          "/start")
    chatgpt(message)


def prompt(message):
    data = bot.send_message(message.chat.id, "Enter your request to generate an image")
    bot.register_next_step_handler(data, number)


def number(message):
    task[message.chat.id] = message.text
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text="1️⃣", callback_data="1")
    button2 = types.InlineKeyboardButton(text="2️⃣", callback_data="2")
    button3 = types.InlineKeyboardButton(text="3️⃣", callback_data="3")
    button4 = types.InlineKeyboardButton(text="4️⃣", callback_data="4")
    keyboard.add(button1, button2)
    keyboard.add(button3, button4)

    bot.send_message(message.chat.id, "Choose the number of photos to generate", reply_markup=keyboard)


def send_photo(message):
    global response
    for i in range(count[message.chat.id]):
        msg = bot.send_message(message.chat.id, "Image generating...")
        msg_id = msg.message_id
        try:
            response = openai.Image.create(
                prompt=task[message.chat.id],
                n=1,
                size="1024x1024"
            )
        except:
            bot.send_message(message.chat.id, "Oops... Invalid request. The request may not comply with the OpenAI security policy. To return to the menu, enter /start")
        image_url = response['data'][0]['url']
        bot.delete_message(message.chat.id, message_id=msg_id)
        bot.send_photo(message.chat.id, image_url)
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text="Yes✅", callback_data="dalle")
    button2 = types.InlineKeyboardButton(text="No❌", callback_data="start")
    keyboard.add(button1, button2)
    bot.send_message(message.chat.id, "Ready! Generate more?", reply_markup=keyboard)


def faq(message):
    bot.send_message(message.chat.id, "*• What is an OpenAI bot?* This is a bot that combines various neural networks, such as DALL-E-2 and chatGPT.\n*• What is DALL-E-2?* This is a neural network that allows you to generate various images from from your request.\n*• What is chatGPT?* This is a neural network that can work with text, this neural network has the most extensive capabilities, ranging from a simple dialogue to writing code.", parse_mode="Markdown")


def referal(message):
    bot.send_message(message.chat.id, "*• What is a referral program?* This is a program that allows you to earn on participants invited by your promo code.\n*• How can I earn on a referral program?* With your promo code, a person buys access to the bot, from his purchase to your the account is deducted 10 rubles, as soon as your account becomes 50 rubles or more, you can withdraw them in any way convenient for you by contacting the support service.\n*• What are the guarantees that this is not a scam?* Our small bot keeps on trust and word of mouth in this situation, the last thing we want is a loss of customer trust.", parse_mode="Markdown")
    cursor.execute("SELECT COUNT(*) FROM users WHERE promo = ?", (str(f"#{message.chat.id}"),))
    use[message.chat.id] = cursor.fetchone()[0]
    bot.send_message(message.chat.id, f"*Your promo code:* #{message.chat.id}\n*Promo code has been used* "
                                      f"{use[message.chat.id]} *times*\n*On your account *{use[message.chat.id]}0 "
                                      f"*rubles*\n*The cost of access to the bot* {config.dostup_cost} *rubles*",
                                      parse_mode="Markdown")


def trial_per(message):
    if trial_add(message.chat.id):
        bot.send_message(message.chat.id, f"Super! Your trial period is activated! You will be able to use our bot for 3 days, after which you will need to purchase access for further use of the bot")
        os.system("systemctl restart main-beta.service")
        bot.send_message(message.chat.id, "Enter /start for further use")
    else:
        bot.send_message(message.chat.id, "You already have a trial period activated!")


@bot.message_handler(func=lambda call: True)
def echo_all(message):
    if get_access_status(message.from_user.id):
        if message.text == 'Select AI🤖':
            keyboard = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton(text="DALL-E-2", callback_data="dalle")
            button2 = types.InlineKeyboardButton(text="ChatGPT", callback_data="gpt")
            button4 = types.InlineKeyboardButton(text="F.A.Q.❓", callback_data="faq")
            keyboard.add(button1, button2)
            keyboard.add(button4)
            bot.send_message(message.chat.id, "Select AI", reply_markup=keyboard)
        elif message.text == 'Feedback🌟':
            rate(message)
        elif message.text == 'Support👥':
            bot.send_message(message.chat.id, "In case of problems with the bot, you can unsubscribe to the developer @sloniko")
        elif message.text == 'Referral program💵':
            referal(message)

    else:
        keyboard = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton(text="Trial period", callback_data="trial")
        keyboard.add(button1)
        bot.send_message(message.chat.id, "You have not purchased access to our bot, you can purchase it by writing @Karlet_y or take a trial period of 3 days",
                         reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # Обработать нажатие на кнопку
    if call.data == "1":
        bot.answer_callback_query(callback_query_id=call.id, text="You have selected 1 picture")
        count[call.message.chat.id] = 1
        send_photo(call.message)
    elif call.data == "2":
        bot.answer_callback_query(callback_query_id=call.id, text="You have selected 2 pictures")
        count[call.message.chat.id] = 2
        send_photo(call.message)
    elif call.data == "3":
        bot.answer_callback_query(callback_query_id=call.id, text="You have selected 3 pictures")
        count[call.message.chat.id] = 3
        send_photo(call.message)
    elif call.data == "4":
        bot.answer_callback_query(callback_query_id=call.id, text="You have selected 4 pictures")
        count[call.message.chat.id] = 4
        send_photo(call.message)
    elif call.data == "dalle":
        bot.answer_callback_query(callback_query_id=call.id, text="DALL-E-2 launch...")
        prompt(call.message)
    elif call.data == "gpt":
        bot.answer_callback_query(callback_query_id=call.id, text="ChatGPT launch...")
        startgpt(call.message)
    elif call.data == "podr":
        podr(call.message)
    elif call.data == "start":
        bot.send_message(call.message.chat.id, "Okay, the bot is suspended. To select AI enter /start")
    elif call.data == "faq":
        faq(call.message)


if __name__ == '__main__':
    bot.infinity_polling()

