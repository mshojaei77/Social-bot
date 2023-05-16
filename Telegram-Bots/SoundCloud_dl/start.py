# -*- coding: utf-8 -*-

import telebot
from time import sleep
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, \
                          ForceReply
from requests import get as get_web
from json import loads as get_json
from db_class import DB_Worker


get_text = DB_Worker().get_text
bot = telebot.TeleBot("BOT_API")

TRACKS_API = 'https://api.soundcloud.com/tracks'
SC_API = 'client_id=WKcQQdEZw7Oi01KqtHWxeVSxNyRzgT8M'
SC = 'soundcloud.com'


def check_reg(id):
    ''' Check if user exist in DB '''

    try:
        get_text(id, 'good')
    except:
        sleep(2)
        check_reg(id)


def generate_markup3(id, mid):
    ''' Reply good music or bad? '''

    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(
            '👍🏼',
            callback_data=f'yes|{mid}'),
            InlineKeyboardButton('👎🏼',
            callback_data=f'no|'
        )
    )

    return markup


def generate_markup2():
    ''' Reply language for user first seen '''

    markup = InlineKeyboardMarkup()
    markup.row_width = 1

    # Receive all aviable language from DB
    rows = DB_Worker().get_lang()

    for row in rows:
        markup.add(
            InlineKeyboardButton(row[0], callback_data=f'lang|{row[1]}')
        )

    return markup


def generate_markup(data):
    ''' Reply music inline buttons from received JSON data '''

    markup = InlineKeyboardMarkup()
    markup.row_width = 1

    # Receive info about founded tracks
    for row in data:
        code = row['stream_url'].replace(TRACKS_API + '/', '')
        code = code.replace('/stream', '')
        markup.add(
            InlineKeyboardButton(
                f"{row['title']}",
                callback_data=f"music|{code}"
            )
        )

    return markup


def reply_by_link(m, del_id):
    try:
        # check if link contains SoundCloud start
        if m.text[:23] == f'https://{SC}/' or m.text[:23] == f'http://{SC}/':
            # Send action: "Uploading file"
            bot.send_chat_action(
                chat_id=m.chat.id,
                action='upload_document'
            )

            # Receive track API info
            info = get_json(
                get_web(f'http://api.{SC}/resolve?url={m.text}&{SC_API}').text
            )

            # Open link to download audio
            temp = get_web(info['stream_url'] + '?' + SC_API).url

            # Send this link -> Telegram -> as file to user
            bot.send_audio(m.chat.id, audio=temp, caption=info['title'])
        else:
            # Bad link detected
            bot.send_message(
                chat_id=m.chat.id,
                text=get_text(m.chat.id, 'ulink')
            )

        bot.delete_message(chat_id=m.chat.id, message_id=del_id)
    except:
        bot.send_message(id, get_text(id, 'uerror'))


def reply_music(id, code, mcode):
    try:
        # Send action "Uploading file"
        bot.send_chat_action(chat_id=id, action='upload_document')

        # Receive audio download link
        temp = get_web(f'{TRACKS_API}/{code}/stream?{SC_API}').url

        # Receive audio info
        temp2 = get_json(get_web(f'{TRACKS_API}/{code}?{SC_API}').text)

        # Send link and desc -> Telegram -> as file + desc to user
        bot.send_audio(
            id,
            audio=temp,
            reply_markup=generate_markup3(id, mcode),
            caption=f"{temp2['user']['username']} - {temp2['title']}"
        )
    except:
        bot.send_message(id, get_text(id, 'uerror'))


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    step = call.data.split('|', 2)
    id = call.message.chat.id

    if step[0] == "music":
        bot.answer_callback_query(call.id, get_text(id, 'good'))
        reply_music(id, step[1], call.message.message_id)
    elif step[0] == "lang":
        DB_Worker().add_user(id, step[1])
        bot.answer_callback_query(call.id, get_text(id, 'reg_completed'))
    elif step[0] == "yes":
        bot.answer_callback_query(call.id, ';-)')
        bot.clear_step_handler_by_chat_id(id)
        bot.edit_message_reply_markup(chat_id=id,
                                      message_id=call.message.message_id,
                                      reply_markup=None)
        bot.delete_message(id, step[1])
    elif step[0] == "no":
        bot.answer_callback_query(call.id, ';-(')
        bot.delete_message(id, call.message.message_id)


@bot.message_handler(commands=['start'])
def on_start(m):
    id = m.chat.id

    if DB_Worker().first_seen(id):
        mess = bot.send_message(
            id,
            '🇦🇺🇨🇿🇩🇪🇷🇼🇷🇺',
            reply_markup=generate_markup2()
        )

        check_reg(id)
        bot.delete_message(id, mess.message_id)

    bot.send_message(id, get_text(id, 'start'))


@bot.message_handler(commands=['link'])
def on_link(message):
    mess = bot.send_message(chat_id=message.chat.id,
                            text=get_text(message.chat.id, 'link'),
                            reply_markup=ForceReply())
    bot.register_for_reply(mess, reply_by_link, mess.message_id)


@bot.message_handler()
def command_receive(message):
    id = message.chat.id

    try:
        if len(message.text) >= 4 and 'http' not in message.text:
            bot.clear_step_handler_by_chat_id(id)
            a = get_json(
                get_web(f'{TRACKS_API}?q={message.text}&{SC_API}').text
            )

            if len(a) <= 1:
                # No JSON content in reply data
                bot.send_message(id, get_text(id, 'nfound'))
            else:
                # We received JSON search answer
                bot.send_message(
                    id,
                    get_text(id, 'smusic'),
                    reply_markup=generate_markup(a)
                )
    except:
        bot.send_message(id, get_text(id, 'uerror'))


def run():
    try:
        bot.polling(none_stop=True)
    except:
        run()


if __name__ == "__main__":
    run()
