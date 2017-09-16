#!/usr/bin/env python2
import sys
import time
import telepot
import requests
import os
from telepot.loop import MessageLoop
import zipfile
import shutil

import secrets
# import food_model
import food_chart

TMPFOLDER = './data_files'

# telegram_chat_id = -233166988
telegram_chat_id = secrets.ROMAN_ID

def extract_file(zipfilename):
    zf = zipfile.ZipFile(zipfilename)

    if os.path.exists(TMPFOLDER):
        shutil.rmtree(TMPFOLDER)
    
    os.makedirs(TMPFOLDER)

    zf.extractall(TMPFOLDER)
    zf.close()

    return TMPFOLDER


def predict(data_folder):
    p = food_model.predict(data_folder)

    next_time = p[0]
    next_amount = p[1]

    msg = 'Next feeding predicted at {:%I:%M %p}'.format(next_time)

    print(msg)
    bot.sendMessage(telegram_chat_id, msg)


def chart(data_folder, recipient):
    chart_file = food_chart.daily(data_folder, range=4)
    bot.sendPhoto(recipient, open(chart_file + '.png', 'rb'))
    print('chart {} sent to {}'.format(chart_file, recipient))

def handle(msg):
    flavor = telepot.flavor(msg)

    summary = telepot.glance(msg, flavor=flavor)

    # we expect a file
    if summary[0] == 'document':
        file_name = msg['document']['file_name']
        if file_name[:3] != 'csv' or file_name[-3:] != 'zip':
            return

        print("Got baby feeding data file")
        file_info = bot.getFile(msg['document']['file_id'])

        url = 'https://api.telegram.org/file/bot{}/{}'.format(TOKEN, file_info['file_path'])

        resp = requests.get(url)

        with open(file_name, 'wb') as f:
            f.write(resp.content)

        extract_folder = extract_file(file_name)

        # predict(extract_folder)
        chart(extract_folder, msg['from']['id'])

        os.remove(file_name)


TOKEN = secrets.TOKEN

bot = telepot.Bot(TOKEN)
MessageLoop(bot, handle).run_as_thread()
print 'Listening ...'

# Keep the program running.
while 1:
    time.sleep(10)