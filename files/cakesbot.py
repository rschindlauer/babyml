#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot to reply to Telegram messages
# This program is dedicated to the public domain under the CC0 license.
"""
This Bot uses the Updater class to handle the bot.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler
import logging
import requests
import zipfile
import shutil
import os

import secrets
import food_chart

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

STATUS, DAY_CHART = range(2)

TMPFOLDER = './data_files'

MQTT_BROKER = '192.168.1.40'

def extract_file(zipfilename):
    zf = zipfile.ZipFile(zipfilename)

    if os.path.exists(TMPFOLDER):
        shutil.rmtree(TMPFOLDER)
    
    os.makedirs(TMPFOLDER)

    zf.extractall(TMPFOLDER)
    zf.close()

    return TMPFOLDER

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    update.message.reply_text('Hi!')


def help(bot, update):
    update.message.reply_text('Help!')

def day_chart(bot, update):
    file_name = update.message.document['file_name']

    if file_name[:3] != 'csv' or file_name[-3:] != 'zip':
        return

    print("Got baby feeding data file")
    file_info = bot.getFile(update.message.document['file_id'])

    resp = requests.get(file_info['file_path'])

    with open(file_name, 'wb') as f:
        f.write(resp.content)
    
    extract_folder = extract_file(file_name)

    chart_file, previous = food_chart.daily(extract_folder, day_range=4)
    update.message.reply_photo(open(chart_file + '.png', 'rb'))

    # include summary
    summary_msg = 'today so far: {}; yesterday at this time: {}; 2 days ago: {}; 3 days ago: {}'.format(previous[0], previous[1], previous[2], previous[3])

    update.message.reply_text(summary_msg)

    print('chart {} sent to {}'.format(chart_file, update.message.from_user.id))

    os.remove(file_name)


def echo(bot, update):
    update.message.reply_text(update.message.text)

def environment(bot, update):
    logger.info('handler: environment')
    import paho.mqtt.client as mqtt
    import paho.mqtt.subscribe as subscribe
    t_msgs = subscribe.simple('home/+/temperature', hostname=MQTT_BROKER, retained=True, msg_count=20, keepalive=1)
    h_msgs = subscribe.simple('home/+/humidity', hostname=MQTT_BROKER, retained=True, msg_count=20, keepalive=1)
    temps = {}
    hums = {}

    for m in t_msgs:
        t = m.topic.replace('/home/', '').replace('/temperature', '')
        if t in temps:
            continue
        if t == 'test':
            continue
        temps[t] = float(m.payload) / 100.0
    
    for m in h_msgs:
        t = m.topic.replace('/home/', '').replace('/humidity', '')
        if t in hums:
            continue
        if t == 'test':
            continue
        hums[t] = m.payload
    
    reply = ''
    for k in temps:
        reply += '{}: T={}, H={}\n'.format(k, temps[k], hums[k])
    
    update.message.reply_text(reply)

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(secrets.TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(RegexHandler("[eE]nvironment", environment))
    dp.add_handler(MessageHandler(Filters.document, day_chart))

    # on noncommand i.e message - echo the message on Telegram
    # dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()