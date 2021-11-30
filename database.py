import sqlite3


class Database:
    def __new__(cls, *args, **kwargs):
        """
        Singleton 객체를 구현하기 위한 메소드
        """
        if not hasattr(cls, '_instance'):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        초기화 메소드
        """
        cls = type(self)
        if not hasattr(cls, '_init'):
            self.conn = sqlite3.connect('db.sqlite3')
            self.conn.row_factory = sqlite3.Row
            self.cur = self.conn.cursor()
            self.cur.execute('PRAGMA foreign_keys = ON')

    def query(self, sql, params=None):
        """
        쿼리문 실행 메소드
        """
        if params is None:
            self.cur.execute(sql)
        else:
            self.cur.execute(sql, params)
        self.conn.commit()

        return self.cur
