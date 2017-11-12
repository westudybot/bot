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
import random

import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

class Status:
    stato = 0

class QuestionSearch:
    conn = MySQLdb.connect("localhost", port=3306, user="gianmarco", passwd="", db="bot")
    cursor = conn.cursor()
    def lookup(self, title):
        cursor= self.cursor
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
        return titoli

    
    def insert(self, chatid, text):
        cursor = self.cursor
        cursor.execute("""
SELECT ID FROM Utenti
WHERE ID = %d;
        """ % chatid)
        if cursor.fetchone() == None:
            cursor.execute("""
            INSERT INTO Utenti (ID, punti, ndomande, nrisposte)
            VALUES (%d, 0, 1, 0);
            """ % chatid)
        else:
            cursor.execute("""
UPDATE Utenti
SET ndomande = ndomande+1
WHERE ID = %d
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
        self.conn.commit()
        
    def domanda_random(self):
        cursor = self.cursor
        cursor.execute("""
SELECT ID, titolo FROM Domande
WHERE ID NOT IN 
    ( SELECT domanda FROM Risposte
      WHERE flag = true
    );
        """)
        rows = cursor.fetchall()
        n = cursor.rowcount
        rnd = random.randrange(n)
        return (rows[rnd][0], rows[rnd][1])
    
    def inserisci_r(self, chatid, risposta_text, domanda_id):
        cursor = self.cursor
        cursor.execute("""
SELECT ID FROM Utenti
WHERE ID = %d;
        """ % chatid)
        if cursor.fetchone() == None:
            cursor.execute("""
            INSERT INTO Utenti (ID, punti, ndomande, nrisposte)
            VALUES (%d, 0, 0, 1);
            """ % chatid)
        else:
            cursor.execute("""
UPDATE Utenti
SET nrisposte = nrisposte+1
WHERE ID = %d
""" % chatid)
        cursor.execute("""
        INSERT INTO Risposte (testo, valutazione, flag, domanda, utente, data)
        VALUES ('%s', 0, false, %d, %d, CURDATE())
        """ % (risposta_text, domanda_id, chatid))
        self.conn.commit()
        cursor.execute("""
SELECT utente FROM Post
WHERE domanda = %d
        """ % domanda_id)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            result.append(r[0])
        return result
#    def retrieve(self, )


class Conversation:
    states = {}
    STARTED = 0
    CHIEDI = 1
    RISPONDI = 2
    SELEZIONE_DOMANDA = 3
    SELEZIONE_RISPOSTA = 4
    INSERIMENTO_RISPOSTA = 5

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
        elif self.states[update.message.chat.id].stato == self.SELEZIONE_RISPOSTA:
            if update.message.text == "Rispondi":
                self.states[update.message.chat.id].stato = self.INSERIMENTO_RISPOSTA
                reply_markup = ReplyKeyboardRemove(selective=False)
                update.message.reply_text("Inserisci la risposta:", reply_markup=reply_markup)
            elif update.message.text == "Salta":
                self.rispondi(update)
            elif update.message.text == "Menu principale":
                self.start(bot, update)
            else:
                update.message.reply_text("Premi /help per aiuto")
        elif self.states[update.message.chat.id].stato == self.INSERIMENTO_RISPOSTA:
            self.ins_r(bot, update)

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
        (id_domanda, titolo_domanda) = self.db.domanda_random()
        keyboard = [[KeyboardButton("Rispondi")],
                    [KeyboardButton("Salta")],
                    [KeyboardButton("Menu principale")]]
        markup = ReplyKeyboardMarkup(keyboard)
        self.states[update.message.chat.id].stato = self.SELEZIONE_RISPOSTA
        self.states[update.message.chat.id].domanda = id_domanda
        update.message.reply_text(titolo_domanda, reply_markup=markup)

    def ins_r(self, bot, update):
        utenti = self.db.inserisci_r(update.message.chat.id, update.message.text, self.states[update.message.chat.id].domanda)
        update.message.reply_text("La tua risposta è stata inserita. Grazie!")
        for u in utenti:
            bot.sendMessage(u, "Un utente ha risposto alla tua domanda!")

    def start(self, bot, update):
        update.message.reply_text("Salve " + update.message.from_user.first_name)
        
        keyboard = [[KeyboardButton("CHIEDI")],
                     [KeyboardButton("RISPONDI")]]

        reply_markup = ReplyKeyboardMarkup(keyboard)
        update.message.reply_text('Cosa vuoi fare?', reply_markup=reply_markup)
        self.states[update.message.chat.id] = Status()
        
    def help(self, bot, update):
        update.message.reply_text("/start per il menu principale")

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
