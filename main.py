import openai
import telebot
from telebot import types
import config

task = {}
count = {}
text = {}
completion = {}

openai.api_key = config.openai_token
token = config.telebot_token
bot = telebot.TeleBot(token)


@bot.message_handler(commands=["start"])
def start(message):
    repkey = types.ReplyKeyboardMarkup(row_width=1)
    gen = types.KeyboardButton('Выбрать AI🤖')
    rate = types.KeyboardButton('Оставить отзыв о боте🌟')
    support = types.KeyboardButton('Тех. поддержка👥')
    repkey.add(gen, rate, support)
    bot.send_message(message.chat.id, "Привет, это бот выполняющий функции большинства, если не всех продуктов "
                                      "OpenAI. Если у вас возникли вопросы по использованию бота, то просмотрите "
                                      "команду /help или напишите в Тех. поддержку. Внимание! Бот находится на стадии "
                                      "бета-тестирования", reply_markup=repkey)


@bot.message_handler(commands=["help"])
def helpme(message):
    bot.send_message(message.chat.id, "Этот бот bспользует официальный API компании openAI"
                                      ". Данный бот разработан одним человеком и не приследует коммерческих "
                                      "целей.\nКоманды бота:\n/dalle - запустить "
                                      "нейросеть DALL-E\n/chatgpt - запустить нейросеть ChatGPT\n/help - вывести это "
                                      "сообщение")


@bot.message_handler(commands=['chatgpt'])
def startgpt(message):
    data = bot.send_message(message.chat.id, 'Привет, я ChatGPT от OpenAI. Ты можешь задать мне вопрос или просто '
                                             'поговорить.\nПримеры:\n"Напиши Telegram бота"\n"Что лучше, '
                                             'Western Digital или Kingston?"')
    bot.register_next_step_handler(data, chatgpt2)


def chatgpt(message):
    repkey = types.ReplyKeyboardMarkup(row_width=1)
    stop = types.KeyboardButton('Остановить ChatGPT⛔')
    repkey.add(stop)
    bot.delete_message(message.chat.id, message_id=msg_id)
    data = bot.send_message(message.chat.id, completion[message.chat.id]['choices'][0]['message']['content'],
                            reply_markup=repkey)
    bot.register_next_step_handler(data, chatgpt2)


def chatgpt2(message):
    global completion
    text[message.chat.id] = message.text
    if text[message.chat.id] == 'Остановить ChatGPT⛔':
        start(message)
        return
    else:
        pass
    try:
        msg = bot.send_message(message.chat.id, "ChatGPT печатает...")
        global msg_id
        msg_id = msg.message_id
        completion[message.chat.id] = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": text[message.chat.id]}]
        )
    except openai.error.RateLimitError:
        bot.send_message(message.chat.id, "Возникли проблемы с API, попробуйте позже")
    print(completion[message.chat.id])
    chatgpt(message)


@bot.message_handler(commands=['dalle'])
def prompt(message):
    data = bot.send_message(message.chat.id, "Введи свой запрос для генерации изображения")
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

    bot.send_message(message.chat.id, "Выберите количество фото для генерации", reply_markup=keyboard)


def send_photo(message):
    global response
    for i in range(count[message.chat.id]):
        msg = bot.send_message(message.chat.id, "Генерация изображения...")
        msg_id = msg.message_id
        try:
            response = openai.Image.create(
                prompt=task[message.chat.id],
                n=1,
                size="1024x1024"
            )
        except:
            bot.send_message(message.chat.id, "Ой... Невалидный запрос. Возможно запрос не соответствует политике "
                                              "безопасности OpenAI")
        image_url = response['data'][0]['url']
        bot.delete_message(message.chat.id, message_id=msg_id)
        bot.send_photo(message.chat.id, image_url)
    bot.send_message(message.chat.id, "Готово!")


@bot.message_handler(func=lambda call: True)
def echo_all(message):
    # Проверяем, на какую кнопку нажал пользователь
    if message.text == 'Выбрать AI🤖':
        keyboard = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton(text="DALL-E-2", callback_data="dalle")
        button2 = types.InlineKeyboardButton(text="ChatGPT", callback_data="gpt")
        keyboard.add(button1, button2)
        bot.send_message(message.chat.id, "Выбери AI", reply_markup=keyboard)
    elif message.text == 'Оставить отзыв о боте🌟':
        bot.send_message(message.chat.id, "По форме ниже ты можешь оставить отзыв о нашем боте для последующей "
                                          "передачи его разработчикам: https://forms.gle/AQi1jYNCUkYVVjmX9")
    elif message.text == 'Тех. поддержка👥':
        bot.send_message(message.chat.id, "В случае проблем с ботом ты можешь отписать разработчику @sloniko")


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # Обработать нажатие на кнопку
    if call.data == "1":
        bot.answer_callback_query(callback_query_id=call.id, text="Вы выбрали 1 картинку")
        count[call.message.chat.id] = 1
        send_photo(call.message)
    elif call.data == "2":
        bot.answer_callback_query(callback_query_id=call.id, text="Вы выбрали 2 картинки")
        count[call.message.chat.id] = 2
        send_photo(call.message)
    elif call.data == "3":
        bot.answer_callback_query(callback_query_id=call.id, text="Вы выбрали 3 картинки")
        count[call.message.chat.id] = 3
        send_photo(call.message)
    elif call.data == "4":
        bot.answer_callback_query(callback_query_id=call.id, text="Вы выбрали 4 картинки")
        count[call.message.chat.id] = 4
        send_photo(call.message)
    elif call.data == "dalle":
        bot.answer_callback_query(callback_query_id=call.id, text="DALL-E-2 запускается...")
        prompt(call.message)
    elif call.data == "gpt":
        bot.answer_callback_query(callback_query_id=call.id, text="ChatGPT запускается...")
        startgpt(call.message)


if __name__ == '__main__':
    bot.infinity_polling()
