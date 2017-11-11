from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

import logging

class QuestionSearch:
    
    def __init__(self):
        pass
    def lookup(self, title):
        

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

class Conversation:
    states = {}
    STARTED = 0
    CHIEDI = 1
    RISPONDI = 2
    
    
    def messages_handler(bot, update):
        if self.states[update.message.chat.id] == Null:
            self.states[update.message.chat.id] = STARTED
        elif self.states[update.message.chat.id] == STARTED
            if update.message.text == "CHIEDI":
                self.states[update.message.chat.id] = CHIEDI
                reply_markup = ReplyKeyboardRemove(selective=False)
                update.message.reply_text("Inserisci la tua domanda:", reply_markup=reply_markup)
            if update.message.text == "RISPONDI":
                self.states[update.message.chat.id] = RISPONDI
                reply_markup = ReplyKeyboardRemove(selective=False)
                update.message.reply_text("Ecco il quesito:", reply_markup=reply_markup)
                self.rispondi()
            else:
                update.message.reply_text("Premi /help per aiuto")
        elif self.states[update.message.chat.id] == CHIEDI:
            self.chiedi()
        elif self.states[update.message.chat.id] == RISPONDI:
            self.rispondi()

    def chiedi(self):
        pass
        

    def start(bot, update):
        update.message.reply_text("Salve " + update.message.from_user.first_name)
        
        keyboard = [[KeyboardButton("CHIEDI"),
                     KeyboardButton("RISPONDI")]]

        reply_markup = ReplyKeyboardMarkup(keyboard)
        update.message.reply_text('Cosa vuoi fare?', reply_markup=reply_markup)
        states[update.message.chat.id] = STARTED
        
    def problems(bot, update):
    
        keyboard = [[KeyboardButton("CHIEDI"),
                     KeyboardButton("RISPONDI")]]

        reply_markup = ReplyKeyboardMarkup(keyboard)
        update.message.reply_text('Please choose:', reply_markup=reply_markup)

    

    def help(bot, update):
        update.message.reply_text("/problems -> Chiedi domanda - Fai domanda")

def main():
    
    updater = Updater("493355727:AAGLJSKPNRod7zflj1pD23EQxiUoDRqivnA")
    
    # Creazione del dispatcher, a cui verranno assegnati i metodi di risposta
    dp = updater.dispatcher

    # Gestione messaegi ricevuti
    dp.add_handler(MessageHandler(Filters.text, messages_handler))
    dp.add_handler(CommandHandler('problems', problems))
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))

    updater.start_polling()  # Inzio del polling

    # Il bot viene arrestato quando Ctrl-C è stato premuto o il bot riceve un SIGINT, SIGTERM o SIGABRT.
    updater.idle()


if __name__ == '__main__':
    main()
