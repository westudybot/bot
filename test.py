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
    def __init__(self):
        self.conn = MySQLdb.connect("localhost", port=3306, user="gianmarco", passwd="", db="bot")
        self.cursor = self.conn.cursor()
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
SELECT titolo FROM Domande
WHERE ID = %d
        """ % domanda_id)
        res = cursor.fetchone()
        domanda_text = res[0]
        cursor.execute("""
SELECT utente FROM Post
WHERE domanda = %d
        """ % domanda_id)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            result.append(r[0])
        return (result, domanda_text)
    def segnapunti(self, chatid, punti):
        cursor = self.cursor
        cursor.execute("""
UPDATE Utenti
SET punti = punti + %d
WHERE ID = %d
        """ % (punti, chatid))
        self.conn.commit()
        return

    def get_punti(self, chatid):
        cursor = self.cursor
        cursor.execute("""
SELECT punti FROM Utenti
WHERE ID = %d
        """ % chatid)
        r = cursor.fetchone()
        if r == None:
            return 0
        else:
            return r[0]
        
    def get_domande(self, chatid):
        cursor = self.cursor
        cursor.execute("""
        SELECT Domande.titolo FROM Domande, Post
WHERE Domande.ID = Post.domanda
AND Post.utente = %d;
        """ % chatid)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            result.append(r[0])
        return result
    def retrieve(self, text):
        cursor = self.cursor
        cursor.execute("""
        SELECT ID FROM Domande
WHERE Domande.titolo = '%s';
        """ %  text)
        i = cursor.fetchone()[0]
        cursor.execute("""
        SELECT ID, testo, flag FROM Risposte
WHERE domanda = %d;
        """ % i)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            result.append([r[0], r[1], r[2]])
        return result
    def register(self, chatid, domanda):
        cursor = self.cursor
        cursor.execute("""
        SELECT Domande.ID FROM Domande, Post
WHERE Domande.ID = Post.domanda
AND Domande.titolo = '%s';
        """ %  domanda)
        i = cursor.fetchone()[0]
        try:
            cursor.execute("""
        INSERT INTO Post (utente, domanda, data)
        VALUES (%d, %d, CURDATE())
            """ % (chatid, i))
            self.conn.commit()
        except MySQLdb._mysql_exceptions.IntegrityError:
            pass
    def close(self, id_risposta):
        cursor = self.cursor
        cursor.execute("""
UPDATE Risposte
SET flag = true
WHERE ID = %d;
        """ % id_risposta)
        cursor.execute("""
SELECT utente FROM Risposte
        WHERE ID = %d;
        """ % id_risposta)
        i = cursor.fetchone()[0]
        cursor.execute("""
UPDATE Utenti
SET punti = punti+100
WHERE ID = %d;
        """ % i)
        self.conn.commit()
        return i

class Conversation:
    states = {}
    STARTED = 0
    CHIEDI = 1
    RISPONDI = 2
    SELEZIONE_DOMANDA = 3
    SELEZIONE_RISPOSTA = 4
    FEEDBACK = 5
    MOSTRA_RISPOSTE = 6
    BEST = 7

    db = QuestionSearch()

    #gestione stati
    def messages_handler(self, bot, update):
        #stato indefinito
        if update.message.chat.id not in self.states:
            self.start(bot, update)
        #bot avviato, scelta dalla prima tastiera
        elif self.states[update.message.chat.id].stato == self.STARTED:
            #chiedi
            if update.message.text == "Chiedi":
                self.states[update.message.chat.id].stato = self.CHIEDI
                reply_markup = ReplyKeyboardRemove(selective=False)
                update.message.reply_text("Inserisci la tua domanda:", reply_markup=reply_markup)
            #rispondi
            elif update.message.text == "Rispondi":
                self.states[update.message.chat.id].stato = self.RISPONDI
                reply_markup = ReplyKeyboardRemove(selective=False)
                update.message.reply_text("Ecco il quesito:", reply_markup=reply_markup)
                self.rispondi(update)
            #punteggio
            elif update.message.text == "Punteggio":
                p = self.db.get_punti(update.message.chat.id)
                update.message.reply_text("Hai accumulato %d punti!" % p)
                self.start2(bot, update)
            #mostra domande
            elif update.message.text == "Mostra domande":
                domande = self.db.get_domande(update.message.chat.id)
                keyboard = []
                for d in domande:
                    keyboard.append([KeyboardButton(d)])
                reply_markup = ReplyKeyboardMarkup(keyboard)
                update.message.reply_text("Ecco le tue domande. Selezionane una per vedere le risposte:", reply_markup=reply_markup)
                self.states[update.message.chat.id].stato = self.MOSTRA_RISPOSTE
            #errore: input inatteso
            else:
                update.message.reply_text("Premi /help per aiuto")
        #gestione stato chiedi: inserimeno della domanda
        elif self.states[update.message.chat.id].stato == self.CHIEDI:
            self.chiedi(bot, update)
        #gestione stato rispondi: mostra una domanda, chiedi inserimento riposta e mostra tastiera
        elif self.states[update.message.chat.id].stato == self.RISPONDI:
            self.rispondi(update)
        #gestione stato selezione domanda: scegli una tra le domande proposte o inseriscila [da CHIEDI]
        elif self.states[update.message.chat.id].stato == self.SELEZIONE_DOMANDA:
            self.selezione(bot, update)
        #gestione stato selezione risposta: salta domanda o inserisci risposta nel DB (o menu) [da RISPONDI]
        elif self.states[update.message.chat.id].stato == self.SELEZIONE_RISPOSTA:
            if update.message.text == "Salta":
                self.rispondi(update)
            elif update.message.text == "Menu principale":
                self.start2(bot, update)
            else:
                self.ins_r(bot, update)
        #inserisci il feedback [dalla notifica inviata all'utente dopo la riposta ad una sua domanda]
        elif self.states[update.message.chat.id].stato == self.FEEDBACK:
            self.feedback(bot, update)
        #mostra le risposte a una domanda simile [da seleziona domanda]
        elif self.states[update.message.chat.id].stato == self.MOSTRA_RISPOSTE:
            res = self.db.retrieve(update.message.text)
            if len(res) == 0:
                update.message.reply_text("Non sono presenti risposte per questa domanda")
            for i, r in enumerate(res):
                if r[2] == True:
                    update.message.reply_text(repr(i) + ". " + r[1] + "✅")
                else:
                    update.message.reply_text(repr(i) + ". " + r[1])
                markup = ReplyKeyboardRemove(selective = False)
            update.message.reply_text("Inserisci il numero della risposta che ti soddisfa per chiudere il topic o /start per tornare al menu principale", reply_markup=markup)
            self.states[update.message.chat.id].stato = self.BEST
            self.states[update.message.chat.id].risposte = res
        elif self.states[update.message.chat.id].stato == self.BEST:
            try:
                n = int(update.message.text)
                if n >= 0 or n < len(self.states[update.message.chat.id].risposte):
                    #chiudi topic, flag risposta, +100pt utente
                    u = self.db.close(self.states[update.message.chat.id].risposte[n][0])
                    update.message.reply_text("La risposta " + repr(n) + " è stata selezionata come la migliore")
                    bot.sendMessage(u, "Hai ottenuto 100 punti dopamina perché la tua risposta è stata selezionata dall'utente come migliore")
                    self.start2(bot, update)
            except ValueError:
                pass
        else:
            self.start2(bot, update)

    def chiedi(self, bot, update):
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
            self.start2(bot, update)

    def selezione(self, bot, update):
        if update.message.text == "AGGIUNGI":
            message = """
La tua domanda è stata aggiunta al database.
Sarai notificato se qualcuno risponderà alla tua domanda
"""
            self.db.insert(update.message.chat.id, self.states[update.message.chat.id].messaggio)
            reply_markup = ReplyKeyboardRemove(selective=False)
            update.message.reply_text(message, reply_markup=reply_markup)
            self.start2(bot, update)
        else:
            res = self.db.retrieve(update.message.text)
            if len(res) == 0:
                update.message.reply_text("Non sono presenti risposte per questa domanda")
            else:
                message = """
Sono state trovate le seguenti risposte al tuo quesito
"""
                update.message.reply_text(message)
            for r in res:
                update.message.reply_text(r[1])
            self.db.register(update.message.chat.id, update.message.text)
            self.start2(bot, update)
    
    def rispondi(self, update):
        (id_domanda, titolo_domanda) = self.db.domanda_random()
        keyboard = [[KeyboardButton("Salta")],
                    [KeyboardButton("Menu principale")]]
        markup = ReplyKeyboardMarkup(keyboard)
        self.states[update.message.chat.id].stato = self.SELEZIONE_RISPOSTA
        self.states[update.message.chat.id].domanda = id_domanda
        update.message.reply_text(titolo_domanda, reply_markup=markup)

    def ins_r(self, bot, update):
        (utenti, domanda) = self.db.inserisci_r(update.message.chat.id, update.message.text, self.states[update.message.chat.id].domanda)
        update.message.reply_text("La tua risposta è stata inserita. Grazie!")
        self.start2(bot, update)
        for u in utenti:
            bot.sendMessage(u, "Un utente ha risposto alla tua domanda!")
            bot.sendMessage(u, domanda)
            bot.sendMessage(u, update.message.text)
            #keyboard = [[KeyboardButton("1️"),
            #             KeyboardButton("2"),
            #             KeyboardButton("3")],
            #            [KeyboardButton("4"),
            #             KeyboardButton("5")]]
            #markup = ReplyKeyboardMarkup(keyboard)
            bot.sendMessage(u, "Valuta la risposta tra 1 e 5:")#, replay_markup=markup)
            if u not in self.states:
                self.states[u] = Status()
            self.states[u].stato = self.FEEDBACK
            self.states[u].risposta = update.message.chat.id

    def feedback(self, bot, update):
        try:
            punti = int(update.message.text)
            if punti <1:
                punti = 0
            elif punti >= 5:
                punti = 5
            punti = punti*10
            self.db.segnapunti(self.states[update.message.chat.id].risposta, punti)
            bot.sendMessage(self.states[update.message.chat.id].risposta, "La tua risposta è stata valutata %d punti dopamina" % punti)
            self.start2(bot, update)
        except e:
            pass
        return
    def start2(self, bot, update):
        keyboard = [[KeyboardButton("Chiedi"),
                     KeyboardButton("Rispondi")],
                    [KeyboardButton("Mostra domande"),
                     KeyboardButton("Punteggio")]]

        reply_markup = ReplyKeyboardMarkup(keyboard)
        update.message.reply_text('Cosa vuoi fare?', reply_markup=reply_markup)
        self.states[update.message.chat.id] = Status()
        
    def start(self, bot, update):
        update.message.reply_text("Ciao " + update.message.from_user.first_name)
        self.start2(bot, update)
        
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
