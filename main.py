import telebot
from telebot import types
import random
import string
import schedule
import time
import smtplib
import re
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class Telegram:
    logging.basicConfig(filename='random_coffee.log', level=logging.INFO)
    bot = telebot.TeleBot('6201647736:AAGkXxhyipMXHmRcREA4DbMa2Yorabw8QPE')
    allowed_domains = ['syssoft.ru']
    admin_emails = {'a.novoseltsev@syssoft.ru': 'active', 'askerov@syssoft.ru': 'inactive'}
    user_email = {}
    codes = {}
    times = {}

    # Если пользователь только начал общение с ботом, отправляем ему сообщение с просьбой указать свой адрес почты
    @bot.message_handler(commands=["start"])
    def start(message):
        user_full_name = message.from_user.full_name
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        Telegram.bot.send_message(message.from_user.id,
                                  f"Привет, {user_full_name}! Укажите свой адрес электронной почты",
                                  reply_markup=markup)

    # Функция для проверки почты
    @bot.message_handler(
        func=lambda message: bool(re.search(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', message.text)))
    def check_email(message):
        if message.text.split("@")[-1] not in Telegram.allowed_domains:
            Telegram.bot.send_message(message.from_user.id, "Домен не разрешен для регистрации!")
            domain_unsuccess = "Домен не разрешен для регистрации!"
            user_id = message.from_user.id
            user_full_name = message.from_user.full_name
            logging.error(f'Пользователь: {user_id} {user_full_name}, '
                         f'Регистрация: {domain_unsuccess}, '
                         f'{time.asctime()}')
            return
        Telegram.user_email = message.text.lower()
        if Telegram.user_email in Telegram.admin_emails and Telegram.admin_emails[Telegram.user_email] == "active":
            Telegram.bot.send_message(message.from_user.id,
                                      "По вашему адресу отправлен код подтверждения, проверьте почту и введите код")
            Telegram.send_email(Telegram.user_email)
        else:
            Telegram.bot.send_message(message.from_user.id,
                                      "Адрес не активен!")
            email_unsuccess = "Адрес не активен!"
            user_id = message.from_user.id
            user_full_name = message.from_user.full_name
            logging.error(f'Пользователь: {user_id} {user_full_name}, '
                         f'Регистрация: {email_unsuccess}, '
                         f'{time.asctime()}')
            return

    # Функция для проверки кода подтверждения и добавления пользователя в список зарегистрированных
    @bot.message_handler(func=lambda message: re.search(r'\d{6}', message.text))
    def check_code(message):
        if Telegram.times[Telegram.user_email] + 1200 < time.time():
            Telegram.bot.send_message(message.chat.id, "Время жизни кода истекло. Попробуйте еще раз.")
            code_unsuccess = "Код истёк!"
            user_id = message.from_user.id
            user_full_name = message.from_user.full_name
            logging.error(f'Пользователь: {user_id} {user_full_name}, '
                         f'Регистрация: {code_unsuccess}, '
                         f'{time.asctime()}')
            return
        if Telegram.codes[Telegram.user_email] == message.text:
            # Запись данных в базу данных
            Session = sessionmaker(bind=engine)
            session = Session()
            user = User(email=Telegram.user_email[message.chat.id], telegram_id=message.from_user.id)
            session.add(user)
            session.commit()
            # Отправка сообщения об успешной регистрации
            Telegram.bot.send_message(message.chat.id,
                                      "Поздравляем! Вы зарегистрированы. Правила использования бота вы можете найти в нашем канале @syssoft_random_coffee_bot.")
            result_success = "Регистрация прошла успешно!"
            user_id = message.from_user.id
            user_full_name = message.from_user.full_name
            logging.info(f'Пользователь: {user_id} {user_full_name}, '
                         f'Регистрация: {result_success}, '
                         f'{time.asctime()}')
        else:
            Telegram.bot.send_message(message.chat.id, "Неверный код подтверждения")
            result_unsuccess = "Регистрация безуспешна!"
            user_id = message.from_user.id
            user_full_name = message.from_user.full_name
            logging.error(f'Пользователь: {user_id} {user_full_name}, '
                         f'Регистрация: {result_unsuccess}, '
                         f'{time.asctime()}')

    # Функция для отправки письма с кодом подтверждения
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

    # Функция для отправки опроса
    def send_poll(chat_id):
        # Получение списка зарегистрированных пользователей
        registered_users = list(Telegram.user_email.keys())
        for user_id in registered_users:
            try:
                # Отправка рассылки
                question1 = "1: Состоялась встреча?"
                options1 = ["Да", "Нет"]
                question2 = "2: Как все прошло?"
                options2 = ["Хорошо", "Плохо"]
                question3 = "3: На следующей неделе участвуешь?"
                options3 = ["Да", "Нет"]

                poll = Telegram.bot.send_poll(chat_id, question1, options1, is_anonymous=False)
                Telegram.bot.send_poll(chat_id, question2, options2, is_anonymous=False,
                                       reply_to_message_id=poll.message_id)
                Telegram.bot.send_poll(chat_id, question3, options3, is_anonymous=False,
                                       reply_to_message_id=poll.message_id)
            except Exception as e:
                logging.error(f"Ошибка отправки рассылки пользователю: {user_id} ({Telegram.get_full_name(user_id)}) ({time.asctime()}): {str(e)}")
            # Ожидание ответа пользователя
            time.sleep(5)
            # Получение ответа пользователя на последний вопрос
            last_answer = Telegram.bot.poll_answer_handlers[-1].last_answer
            # Проверка ответа на последний вопрос
            if last_answer and last_answer.user.id == user_id:
                if last_answer.option_ids[0] == 1:
                    # Обработка ответа "Нет"
                    # Удаление пользователя из списка зарегистрированных
                    Telegram.user_email.pop(user_id, None)
                    logging.info(f"Пользователь {user_id} ({Telegram.get_full_name(user_id)}) удален из списка зарегистрированных пользователей ({time.asctime()})")

    # Обработка ответов на опрос
    @bot.poll_answer_handler()
    def handle_poll_answer(poll_answer):
        # Отправляем сообщение с результатами опроса
        Telegram.bot.send_message(poll_answer.user.id, "Спасибо за ваш ответ! Результаты опроса:")
        for option in poll_answer.option_ids:
            Telegram.bot.send_message(poll_answer.user.id, f"{option=}")

    # Обработка рассылки
    @bot.message_handler(commands=['start'])
    def start_newsletter(message):
        # Запускаем рассылку каждую пятницу в 17:00
        schedule.every().friday.at("17:00").do(Telegram.send_poll, Telegram.chat_id)

        # Цикл для выполнения расписания
        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == '__main__':
    telegram = Telegram()
    telegram.bot.polling(none_stop=True, interval=0)
