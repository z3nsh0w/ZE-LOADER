import sqlite3 
import os

database_path = None

def initialize_database(path_to_database):
    global database_path
    database_path = path_to_database



def create_database(path_to_database, history, download_type, download_quality, download_path, browser_cookie):
    database = sqlite3.connect(path_to_database)
    cursor = database.cursor()

    cursor.execute('CREATE TABLE IF NOT EXISTS settings(history TEXT, download_type TEXT, download_quality TEXT, download_path TEXT, browser_cookie TEXT)')

    database.commit()

    cursor.execute('INSERT INTO settings (history, download_type, download_quality, download_path, browser_cookie) VALUES (?, ?, ?, ?, ?)', (history, download_type, download_quality, download_path, browser_cookie))

    database.commit()
    database.close()


def get_history():
    database = sqlite3.connect(database_path)
    cursor = database.cursor()

    cursor.execute('''
    SELECT history FROM settings
                   ''')

    data = cursor.fetchone()[0]
    

    database.close()

    return data


def get_download_type():
    database = sqlite3.connect(database_path)
    cursor = database.cursor()

    cursor.execute('''
    SELECT download_type FROM settings
                   ''')

    data = cursor.fetchone()[0]

    database.close()

    return data


def get_download_quality():
    database = sqlite3.connect(database_path)
    cursor = database.cursor()

    cursor.execute('''
    SELECT download_quality FROM settings
                   ''')

    data = cursor.fetchone()[0]

    database.close()

    return data

def get_download_path():
    database = sqlite3.connect(database_path)
    cursor = database.cursor()

    cursor.execute('''
    SELECT download_path FROM settings
                   ''')

    data = cursor.fetchone()[0]

    database.close()

    return data


def get_browser_cookie():
    print(database_path)
    # print('\n\n')
    database = sqlite3.connect(database_path)
    cursor = database.cursor()

    cursor.execute('''
    SELECT browser_cookie FROM settings
                   ''')

    data = cursor.fetchone()[0]

    database.close()

    return data




def set_history(new_value):
    database = sqlite3.connect(database_path)
    cursor = database.cursor()

    cursor.execute(f'UPDATE settings SET history = ?', (new_value,))
    database.commit()

    database.close()



def set_download_type(new_value):
    database = sqlite3.connect(database_path)
    cursor = database.cursor()

    cursor.execute(f'UPDATE settings SET download_type = ?', (new_value,))
    database.commit()

    database.close()



def set_download_quality(new_value):
    database = sqlite3.connect(database_path)
    cursor = database.cursor()

    cursor.execute(f'UPDATE settings SET download_quality = ?', (new_value,))
    database.commit()

    database.close()



def set_download_path(new_value):
    database = sqlite3.connect(database_path)
    cursor = database.cursor()

    cursor.execute(f'UPDATE settings SET download_path = ?', (new_value,))
    database.commit()

    database.close()



def set_browser_cookie(new_value):
    database = sqlite3.connect(database_path)
    cursor = database.cursor()

    cursor.execute(f'UPDATE settings SET browser_cookie = ?', (new_value,))

    database.commit()

    database.close()



# initialize('data.db')
# get_download_type('data.db')