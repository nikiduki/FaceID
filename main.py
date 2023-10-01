import face_detection_video
import face_recognition_image
import cv2
import telebot
from config import bot_token_
from sql import sql_insert, get_base
import os

def main():
    class User:
        def __init__(self, name=None):
            self.name = name

    bot = telebot.TeleBot(bot_token_)
    user = User()
    @bot.message_handler(commands=['start'])
    def welcome(message):
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        item1 = telebot.types.InlineKeyboardButton("Войти", callback_data='login')
        item2 = telebot.types.InlineKeyboardButton("Регистрация", callback_data='register')
        markup.add(item1, item2)

        bot.send_message(chat_id=message.chat.id,
                         text="Привет)\nЯ - <b>{1.first_name}</b>\nЕсть два путя:".format(
                          message.from_user, bot.get_me()),
                         parse_mode='html', reply_markup=markup)

    @bot.message_handler(content_types=['text'])
    def get_text(message):
        if message.chat.type == 'private':
            if message.text == 'Войти':
                bot.send_message(chat_id=message.chat.id, text="Отправьте свою фотографию для входа", reply_markup=None)
                while True:
                    try:
                        bot.register_next_step_handler(message, receve_login)
                        break
                    except Exception as ex:
                        print(ex)
                        bot.send_message("Отправьте свою фотографию для входа", reply_markup=None)

            elif message.text == 'Регистрация':
                bot.send_message(chat_id=message.chat.id, text="Напишите свое имя", reply_markup=None)
                bot.register_next_step_handler(message, receve_name)

            else:
                bot.send_message(message.chat.id, 'Я не сильно разговорчивый 👉👈')

    def receve_name(message):
        if message is not None and message.text is not None:
            try:
                user.name = message.text
            except Exception as ex:
                print(ex)
                markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                item1 = telebot.types.InlineKeyboardButton("Войти", callback_data='login')
                item2 = telebot.types.InlineKeyboardButton("Регистрация", callback_data='register')
                markup.add(item1, item2)
                bot.send_message(chat_id=message.chat.id, text="Некорректный ввод",
                                 reply_markup=markup)
            bot.send_message(message.chat.id, f"Привет, {user.name})\nОтправьте видео с вашим лицом для того, чтобы я научился Вас определять\n"
                             "(Желательно 1 сек)",
                             reply_markup=None)
        else:
            markup = telebot.types.InlineKeyboardMarkup(row_width=2)
            item1 = telebot.types.InlineKeyboardButton("Войти", callback_data='login')
            item2 = telebot.types.InlineKeyboardButton("Регистрация", callback_data='register')
            markup.add(item1, item2)
            bot.send_message(chat_id=message.chat.id, text="Некорректный ввод",
                             reply_markup=markup)
            while True:
                try:
                    bot.register_next_step_handler(message, receve)
                    break
                except Exception as ex:
                    print(ex)
                    bot.send_message(message.chat.id,
                                     "Отправьте видео с вашим лицом для того, чтобы я научился Вас распознавать\n"
                                     "(Желательно 1 сек)", reply_markup=None)

    @bot.message_handler(content_types=['video'])
    def receve(message):
        if user.name is not None:
            try:
                file_id = message.video.file_id
                file_info = bot.get_file(file_id)
                filename, file_extension = os.path.splitext(file_info.file_path)
                downloaded_file_video = bot.download_file(file_info.file_path)
                src = r'C:\Users\d5u5d\github\facedars\python-facedars\demo\tmp'
                with open(src, 'wb') as new_file:
                    new_file.write(downloaded_file_video)
                bot.send_message(message.chat.id,
                                 "Учусь распознавать, это может занять некоторое время...",
                                 reply_markup=None, parse_mode='html')
                photos = face_detection_video.face_detect(user.name, src)
                ex = sql_insert(user.name, photos)
                markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                item1 = telebot.types.InlineKeyboardButton("Войти", callback_data='login')
                markup.add(item1)
                if ex:
                    bot.send_message(message.chat.id, "Вы не зарегистрированы, так как регистрация"
                                                      " поломалась по пути до Вас")
                else:
                    bot.send_message(message.chat.id, "Вы зарегистрированы", reply_markup=markup)
            except Exception as ex:
                print(ex)
                markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                item1 = telebot.types.InlineKeyboardButton("Войти", callback_data='login')
                item2 = telebot.types.InlineKeyboardButton("Регистрация", callback_data='register')
                markup.add(item1, item2)
                bot.send_message(message.chat.id,
                                 "Некорректный ввод", reply_markup=markup)

    def receve_login(message):
        user.name = None
        try:
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            filename, file_extension = os.path.splitext(file_info.file_path)
            downloaded_file_photo = bot.download_file(file_info.file_path)
            src = r'C:\Users\d5u5d\github\facedars\python-facedars\demo\tmp'
            with open(src, 'wb') as new_file:
                new_file.write(downloaded_file_photo)
            image = cv2.imread(src)
            bot.send_message(message.chat.id,
                             "Сверяю...",
                             reply_markup=None, parse_mode='html')
            mes, success = face_recognition_image.face_recognise(image, get_base())
            if success:
                photo_out = open(r"C:\Users\d5u5d\github\facedars\python-facedars\demo\recognition_image\output\frames\1.jpg", 'rb')
                bot.send_photo(message.chat.id, photo_out)
                markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                item1 = telebot.types.InlineKeyboardButton("Выйти", callback_data='exit')
                markup.add(item1)
                bot.send_message(message.chat.id,
                                 mes,
                                 reply_markup=markup, parse_mode='html')
            else:
                markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                item1 = telebot.types.InlineKeyboardButton("Войти", callback_data='login')
                item2 = telebot.types.InlineKeyboardButton("Регистрация", callback_data='register')
                markup.add(item1, item2)
                bot.send_message(message.chat.id,
                                 mes,
                                 reply_markup=markup, parse_mode='html')
            user.name = None
        except Exception as ex:
            print(ex)
            markup = telebot.types.InlineKeyboardMarkup(row_width=2)
            item1 = telebot.types.InlineKeyboardButton("Войти", callback_data='login')
            item2 = telebot.types.InlineKeyboardButton("Регистрация", callback_data='register')
            markup.add(item1, item2)
            bot.send_message(chat_id=message.chat.id, text="Некорректный ввод",
                             reply_markup=markup)


    @bot.callback_query_handler(func=lambda call: True)
    def callback_inline(call):
        try:
            if call.message:
                if call.data == 'login':
                    bot.send_message(chat_id=call.message.chat.id, text="Отправьте свою фотографию для входа",
                                     reply_markup=None)
                    while True:
                        try:
                            bot.register_next_step_handler(call.message, receve_login)
                            break
                        except Exception as ex:
                            print(ex)
                            bot.send_message(chat_id=call.message.chat.id,text="Отправьте свою фотографию для входа", reply_markup=None)

                elif call.data == 'register':
                    bot.send_message(chat_id=call.message.chat.id, text="Напишите свое имя", reply_markup=None)
                    while True:
                        try:
                            bot.register_next_step_handler(call.message, receve_name)
                            break
                        except Exception as ex:
                            print(ex)
                            bot.send_message(chat_id=call.message.chat.id, text="Напишите свое имя", reply_markup=None)
                elif call.data == 'exit':
                    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                    item1 = telebot.types.InlineKeyboardButton("Войти", callback_data='login')
                    item2 = telebot.types.InlineKeyboardButton("Регистрация", callback_data='register')
                    markup.add(item1, item2)
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          text="Вы вышли",
                                          reply_markup=markup)
        except Exception as e:
            print(repr(e))

    bot.polling(none_stop=True)

if __name__ == "__main__":
    main()
