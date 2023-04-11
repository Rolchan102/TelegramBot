import telebot
from telebot import types
import random
import string
import time
import smtplib
import re
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class Telegram:
    logging.basicConfig(level=logging.INFO)
    bot = telebot.TeleBot('6201647736:AAGkXxhyipMXHmRcREA4DbMa2Yorabw8QPE')
    allowed_domains = ['syssoft.ru']
    admin_emails = {'a.novoseltsev@syssoft.ru': 'active', 'askerov@syssoft.ru': 'inactive'}
    user_email = {}
    codes = {}
    times = {}

    @bot.message_handler(commands=["start"])
    def start(message):
        user_id = message.from_user.id
        user_full_name = message.from_user.full_name
        logging.info(f'{user_id} {user_full_name} {time.asctime()}')
        # Если пользователь только начал общение с ботом, отправляем ему сообщение с просьбой указать свой адрес почты
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        Telegram.bot.send_message(message.from_user.id,
                                  f"Привет, {user_full_name}! Укажите свой адрес электронной почты",
                                  reply_markup=markup)

    @bot.message_handler(func=lambda message: bool(re.search(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', message.text)))
    def check_email(message):
        if message.text.split("@")[-1] not in Telegram.allowed_domains:
            Telegram.bot.send_message(message.from_user.id, "К сожалению, ваш домен не разрешен для регистрации")
            return
        Telegram.user_email = message.text.lower()
        if Telegram.user_email in Telegram.admin_emails and Telegram.admin_emails[Telegram.user_email] == "active":
            Telegram.bot.send_message(message.from_user.id,
                                      "По вашему адресу отправлен код подтверждения, проверьте почту и введите код")
            Telegram.send_email(Telegram.user_email)
        else:
            Telegram.bot.send_message(message.from_user.id,
                                      "Адрес не найден в списке администраторов или не активен")
            return

    @bot.message_handler(func=lambda message: re.search(r'\d{6}', message.text))
    def check_code(message):
        if Telegram.times[Telegram.user_email] + 1200 < time.time():
            Telegram.bot.send_message(message.chat.id, "Время жизни кода истекло. Попробуйте еще раз.")
            return
        if Telegram.codes[Telegram.user_email] == message.text:
            Telegram.bot.send_message(message.chat.id,
                                      "Поздравляем! Вы зарегистрированы. Правила использования бота вы можете найти в нашем канале @syssoft_random_coffee_bot.")
        else:
            Telegram.bot.send_message(message.chat.id, "Неверный код подтверждения")

    def send_email(user_email):
        # Генерируем случайный код подтверждения
        code = ''.join(random.choice(string.digits) for _ in range(6))
        # Запоминаем код в словаре codes
        Telegram.codes[user_email] = code
        # Запоминаем время отправки кода в словаре times
        Telegram.times[user_email] = time.time()

        smtp_username = "novosltsev2010@gmail.com"
        smtp_password = "uvxhzvmfpvdhkhoo"

        smtp_conn = smtplib.SMTP('smtp.gmail.com: 587')
        smtp_conn.starttls()
        smtp_conn.login(smtp_username, smtp_password)

        message = MIMEMultipart()
        message['From'] = smtp_username
        message['To'] = user_email
        message['Subject'] = 'Код подтверждения'

        # Отправляем код на почту пользователя
        code_message = f"Код подтверждения: {code}. Введите его в боте для подтверждения регистрации."
        message.attach(MIMEText(code_message, 'plain'))
        smtp_conn.sendmail(smtp_username, user_email, message.as_string())
        smtp_conn.quit()


if __name__ == '__main__':
    telegram = Telegram()
    telegram.bot.polling(none_stop=True, interval=0)
