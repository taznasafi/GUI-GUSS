import sqlite3
from typing import Optional
import pandas as pd


class DB:
    def __init__(self, db_path:str)->None:
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection]=None
        self.cursor: Optional[sqlite3.Cursor] = None

    def connect(self)->bool:
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            return True
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            return False

    def createDB(self):
        try:
            if self.connect():
                # create as of date table
                self.cursor.execute(
                    '''
                    CREATE TABLE IF NOT EXISTS as_of_date (
                        vintage_id TEXT PRIMARY KEY,
                        date DATE NOT NULL
                        );
                    '''
                )
                # create provider id List
                self.cursor.execute(
                    '''
                    CREATE TABLE IF NOT EXISTS pid_list (
                        pid TEXT PRIMARY KEY,
                        brand_name Text NOT NULL);
                    '''
                )
                # state_fips
                self.cursor.execute(
                    '''
                    CREATE TABLE IF NOT EXISTS state_fips (
                        date TEXT PRIMARY KEY);
                    '''
                )

                # GiS_file_type
                self.cursor.execute(
                    '''
                    CREATE TABLE IF NOT EXISTS file_type (
                        file_id INTEGER PRIMARY KEY 
                        file_type TEXT NOT NULL 
                        );
                    '''
                )
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            return False

    def query(self, sql:str)-> pd.DataFrame():
        pass