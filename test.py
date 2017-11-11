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
from http import client as http
import MySQLdb
import operator

import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

class Status:
    stato = 0

class QuestionSearch:
    conn = MySQLdb.connect("localhost", port=3306, user="gianmarco", passwd="", db="bot")
    def lookup(self, title):
        cursor= self.conn.cursor()
        matches = {}
        titoli = []
        for w in title.split():
            cursor.execute("""
SELECT ID FROM Domande
            WHERE MATCH (titolo, testo)
            AGAINST ('%s' IN NATURAL LANGUAGE MODE);
            """ % title)
            rows = cursor.fetchall()
            for row in rows:
                if row[0] not in matches:
                    matches[row[0]] = 1
                else:
                    matches[row[0]] +=1
            if len(matches) > 3:
                sorted_ = sorted(matches.items(), key=operator.itemgetter(1), reverse=True)
                IDs =  [i[0] for i in sorted_[0:3]]
            else:
                IDs = matches.keys()
        for ID in IDs:
            cursor.execute("""
SELECT titolo FROM Domande
            WHERE ID = %d;
            """ % ID
                )
            titoli.append(cursor.fetchone()[0])
        cursor.close()
        return titoli

    
    def insert(self, chatid, text):
        cursor = self.conn.cursor()
        cursor.execute("""
SELECT ID FROM Utenti
WHERE ID = %d;
        """ % chatid)
        if cursor.fetchone() == None:
            cursor.execute("""
            INSERT INTO Utenti (ID, punti, ndomande, nrisposte)
            VALUES (%d, 0, 1, 0);
            """ % chatid)
        cursor.execute("""
        INSERT INTO Domande (titolo)
        VALUES ('%s');
        """ % text)
        cursor.execute("""
        INSERT INTO Post (utente, domanda, data)
        VALUES (
        %d, (SELECT MAX(ID) FROM Domande), CURDATE());
        """ % chatid)
        cursor.close()
        self.conn.commit()
        
    def domanda_random(self):
        cursor = self.conn.cursor()
        cursor.execute("""
SELECT titolo FROM domande
WHERE ID NOT IN 
    ( SELECT domanda FROM Risposte
      WHERE flag = true
    );
        """)
        
#    def retrieve(self, )


class Conversation:
    states = {}
    STARTED = 0
    CHIEDI = 1
    RISPONDI = 2
    SELEZIONE_DOMANDA = 3

    db = QuestionSearch()
    
    def messages_handler(self, bot, update):
        if update.message.chat.id not in self.states:
            self.start(bot, update)
        elif self.states[update.message.chat.id].stato == self.STARTED:
            if update.message.text == "CHIEDI":
                self.states[update.message.chat.id].stato = self.CHIEDI
                reply_markup = ReplyKeyboardRemove(selective=False)
                update.message.reply_text("Inserisci la tua domanda:", reply_markup=reply_markup)
            elif update.message.text == "RISPONDI":
                self.states[update.message.chat.id].stato = self.RISPONDI
                reply_markup = ReplyKeyboardRemove(selective=False)
                update.message.reply_text("Ecco il quesito:", reply_markup=reply_markup)
                self.rispondi(update)
            else:
                update.message.reply_text("Premi /help per aiuto")
        elif self.states[update.message.chat.id].stato == self.CHIEDI:
            self.chiedi(update)
        elif self.states[update.message.chat.id].stato == self.RISPONDI:
            self.rispondi(update)
        elif self.states[update.message.chat.id].stato == self.SELEZIONE_DOMANDA:
            self.selezione(update)

    def chiedi(self, update):
        results = self.db.lookup(update.message.text)
        if len(results) > 0:
            message = """Sono state trovate alcune domande simili alla tua.
Seleziona quella più adatta oppure inserisci la domanda
"""
            buttons = []
            for r in results:
                #TODO: InlineKeyboardButton
                buttons.append([KeyboardButton(r)])
            buttons.append([KeyboardButton("AGGIUNGI")])
            markup = ReplyKeyboardMarkup(buttons)
            self.states[update.message.chat.id].stato = self.SELEZIONE_DOMANDA
            self.states[update.message.chat.id].messaggio = update.message.text
            update.message.reply_text(message, reply_markup=markup)
        else:
            message = """
Non sono state trovate domande simili.
La tua domanda è stata aggiunta al database.
Sarai notificato se qualcuno risponderà alla tua domanda
"""
            self.db.insert(update.message.chat.id, update.message.text)
            update.message.reply_text(message)

    def selezione(self, update):
        if update.message.text == "AGGIUNGI":
            message = """
La tua domanda è stata aggiunta al database.
Sarai notificato se qualcuno risponderà alla tua domanda
"""
            self.db.insert(update.message.chat.id, self.states[update.message.chat.id].messaggio)
            reply_markup = ReplyKeyboardRemove(selective=False)
            update.message.reply_text(message, reply_markup=reply_markup)
            
        else:
            #cerca nel db la risposta
            pass
    
    def rispondi(self, update):
        #domanda scelta casualmente
        

    def start(self, bot, update):
        update.message.reply_text("Salve " + update.message.from_user.first_name)
        
        keyboard = [[KeyboardButton("CHIEDI")],
                     [KeyboardButton("RISPONDI")]]

        reply_markup = ReplyKeyboardMarkup(keyboard)
        update.message.reply_text('Cosa vuoi fare?', reply_markup=reply_markup)
        self.states[update.message.chat.id] = Status()
        
    def help(self, bot, update):
        update.message.reply_text("/problems -> Chiedi domanda - Fai domanda")

def main():
    
    updater = Updater("493355727:AAGLJSKPNRod7zflj1pD23EQxiUoDRqivnA")
    
    # Creazione del dispatcher, a cui verranno assegnati i metodi di risposta
    dp = updater.dispatcher

    c = Conversation()
    
    # Gestione messaegi ricevuti
    dp.add_handler(MessageHandler(Filters.text, c.messages_handler))
    dp.add_handler(CommandHandler('start', c.start))
    dp.add_handler(CommandHandler('help', c.help))

    updater.start_polling()  # Inzio del polling

    # Il bot viene arrestato quando Ctrl-C è stato premuto o il bot riceve un SIGINT, SIGTERM o SIGABRT.
    updater.idle()


if __name__ == '__main__':
    main()
