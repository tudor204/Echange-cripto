import sqlite3
from app import ORIGIN_DATA

class Conexion:
    def __init__(self,querySql,params=[]):
        self.con = sqlite3.connect(ORIGIN_DATA)
        self.cur = self.con.cursor()
        self.res = self.cur.execute(querySql,params)