# -*- coding: utf-8 -*-

import sqlite3
from json import loads as get_json


class DB_Worker:
    def __init__(self):
        self.db = 'db.db'

    def _sql_execute(self, sql, fletch=True, multi=False):
        conn = sqlite3.connect(self.db)
        db_worker = conn.cursor()
        db_worker.execute(sql)

        if fletch:
            if multi:
                seen = db_worker.fetchall()
            else:
                seen = db_worker.fetchone()[0]

            conn.close()
            return seen
        else:
            conn.commit()
            conn.close()

    def add_user(self, user_id, lang):
        ''' Add user to database '''

        self._sql_execute(
            f'INSERT INTO `users` VALUES ("{user_id}", "{lang}")', fletch=False
        )

    def first_seen(self, user_id):
        ''' First seen by this user? '''

        seen = self._sql_execute(
            f'SELECT COUNT(`lang`) FROM `users` WHERE `id` = "{user_id}"'
        )

        if seen == 0:
            return True
        else:
            return False

    def get_text(self, user_id, what):
        ''' Get user launguage code from DB and text from JSON by lng code '''

        lang = self._sql_execute(
            f'SELECT `lang` FROM `users` WHERE `id` = "{user_id}"'
        )

        return get_json(
            open(f'lang/{lang}.json', 'r', encoding='utf-8').read()
        )[what]

    def get_lang(self):
        lang = self._sql_execute('SELECT * FROM `lang`', multi=True)

        return lang
