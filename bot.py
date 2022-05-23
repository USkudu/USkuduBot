import datetime
import telebot
import config
import calendar
from main import TelegramBot, HELP_MESSAGE, START_MESSAGE
from wiki import wiki

bot = telebot.TeleBot(config.TOKEN)
obj = TelegramBot()


@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, START_MESSAGE)


@bot.message_handler(commands=['help'])
def helper(message):
    bot.send_message(message.chat.id, HELP_MESSAGE)


@bot.message_handler(commands=['duty'])
def welcome(message):
    bot.send_message(message.chat.id, obj.duty())


@bot.message_handler(commands=['next'])
def welcome(message):
    bot.send_message(message.chat.id, obj.next())


@bot.message_handler(commands=['success'])
def welcome(message):
    bot.send_message(message.chat.id, obj.success())


@bot.message_handler(content_types=['text'])
def main(message):
    try:
        if message.text.startswith(config.USERNAME_BOT):
            user_message = message.text[len(config.USERNAME_BOT):].lower().strip()
            t = str(datetime.datetime.now(tz=obj.tz))[:10]
            t = datetime.datetime.strptime(t, "%Y-%m-%d")
            if calendar.day_name[t.today().weekday()].lower() == 'sunday':
                obj.update()
            if 'пары' in user_message and 'сегодня' in user_message:
                bot.send_message(message.chat.id, obj.today())
            elif 'пары' in user_message and 'завтра' in user_message:
                bot.send_message(message.chat.id, obj.tomorrow())
            elif 'номер' in user_message and 'недели' in user_message:
                bot.send_message(message.chat.id, obj.number_week())
            elif 'аттестация' in user_message or 'аттестации' in user_message:
                obj.attestations(bot, message.chat.id, user_message)
            elif 'расписание' in user_message or 'расписания' == user_message:
                obj.schedule(bot, message.chat.id, user_message)
            elif 'предметы' == user_message:
                bot.send_message(message.chat.id, obj.subjects())
            elif user_message in obj.set_subjects:
                bot.send_message(message.chat.id, obj.test_or_exams(user_message))
            elif 'где' in user_message and 'пара' in user_message:
                bot.send_message(message.chat.id, obj.audience_couple())
            else:
                bot.send_message(message.chat.id, 'Некорректный запрос. Инструкцию бота можно прочесть нажав на /help')
        elif message.text.lower().split()[0] in ['вики', 'wiki']:
            bot.send_message(message.chat.id, wiki(' '.join(message.text.split()[1:])))
    except Exception as error:
        bot.send_message(802590461, f'{str(error)}\n\ntext: {message.text}\n\nusername: @{message.from_user.username}')


bot.polling(none_stop=True)
