from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def messages_handler(bot, update):
    
    if update.message.text == "ciao":
        update.message.reply_text("Salve " + update.message.from_user.first_name)
    else:
        update.message.reply_text("Premi /help per aiuto")

def problems(bot, update):
    
    keyboard = [[KeyboardButton("CHIEDI"),
                 KeyboardButton("RISPONDI")]]

    reply_markup = ReplyKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)

    

def help(bot, update):
    update.message.reply_text("/problems -> Chiedi domanda - Fai domanda")

def main():
    
    updater = Updater("474629018:AAFylYi5Zjh9P4fA4L_qawnd_SxLl9YlZ4I")
    
    # Creazione del dispatcher, a cui verranno assegnati i metodi di risposta
    dp = updater.dispatcher

    # Gestione messaegi ricevuti
    dp.add_handler(MessageHandler(Filters.text, messages_handler))
    dp.add_handler(CommandHandler('problems', problems))
    dp.add_handler(CommandHandler('help', help))

    updater.start_polling()  # Inzio del polling

    # Il bot viene arrestato quando Ctrl-C è stato premuto o il bot riceve un SIGINT, SIGTERM o SIGABRT.
    updater.idle()


if __name__ == '__main__':
    main()
