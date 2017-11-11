#!/usr/bin/python3
#Copyright © 2017 Gianmarco Garrisi
#Copyright © 2017 Federico Gianno
#Copyright © 2017 Carlo Negri
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

class QuestionSearch:
    
    def __init__(self):
        pass
    def lookup(self, title):
        pass
        

class Conversation:
    states = {}
    STARTED = 0
    CHIEDI = 1
    RISPONDI = 2
    
    
    def messages_handler(self, bot, update):
        if self.states[update.message.chat.id] == None:
            self.states[update.message.chat.id] = self.STARTED
        elif self.states[update.message.chat.id] == self.STARTED:
            if update.message.text == "CHIEDI":
                self.states[update.message.chat.id] = self.CHIEDI
                reply_markup = ReplyKeyboardRemove(selective=False)
                update.message.reply_text("Inserisci la tua domanda:", reply_markup=reply_markup)
            elif update.message.text == "RISPONDI":
                self.states[update.message.chat.id] = self.RISPONDI
                reply_markup = ReplyKeyboardRemove(selective=False)
                update.message.reply_text("Ecco il quesito:", reply_markup=reply_markup)
                self.rispondi(update)
            else:
                update.message.reply_text("Premi /help per aiuto")
        elif self.states[update.message.chat.id] == self.CHIEDI:
            self.chiedi(update)
        elif self.states[update.message.chat.id] == self.RISPONDI:
            self.rispondi(update)

    def chiedi(self, update):
        pass

    def rispondi(self, update):
        pass

    def start(self, bot, update):
        update.message.reply_text("Salve " + update.message.from_user.first_name)
        
        keyboard = [[KeyboardButton("CHIEDI"),
                     KeyboardButton("RISPONDI")]]

        reply_markup = ReplyKeyboardMarkup(keyboard)
        update.message.reply_text('Cosa vuoi fare?', reply_markup=reply_markup)
        self.states[update.message.chat.id] = self.STARTED
        
    def problems(self, bot, update):
    
        keyboard = [[KeyboardButton("CHIEDI"),
                     KeyboardButton("RISPONDI")]]

        reply_markup = ReplyKeyboardMarkup(keyboard)
        update.message.reply_text('Please choose:', reply_markup=reply_markup)

    

    def help(self, bot, update):
        update.message.reply_text("/problems -> Chiedi domanda - Fai domanda")

def main():
    
    updater = Updater("493355727:AAGLJSKPNRod7zflj1pD23EQxiUoDRqivnA")
    
    # Creazione del dispatcher, a cui verranno assegnati i metodi di risposta
    dp = updater.dispatcher

    c = Conversation()
    
    # Gestione messaegi ricevuti
    dp.add_handler(MessageHandler(Filters.text, c.messages_handler))
    dp.add_handler(CommandHandler('problems', c.problems))
    dp.add_handler(CommandHandler('start', c.start))
    dp.add_handler(CommandHandler('help', c.help))

    updater.start_polling()  # Inzio del polling

    # Il bot viene arrestato quando Ctrl-C è stato premuto o il bot riceve un SIGINT, SIGTERM o SIGABRT.
    updater.idle()


if __name__ == '__main__':
    main()
