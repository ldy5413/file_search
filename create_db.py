import os
import sqlite3
import tkinter as tk
from tkinter import filedialog

def index_files(directory):
    conn = sqlite3.connect('file_index.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS files
                 (path TEXT PRIMARY KEY, name TEXT, type TEXT)''')
    for root, dirs, files in os.walk(directory):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            c.execute('INSERT OR IGNORE INTO files (path, name, type) VALUES (?, ?, ?)', (dir_path, dir_name, 'directory'))
        for file in files:
            file_path = os.path.join(root, file)
            c.execute('INSERT OR IGNORE INTO files (path, name, type) VALUES (?, ?, ?)', (file_path, file, 'file'))
    conn.commit()
    conn.close()

def choose_directory():
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    directory = filedialog.askdirectory(title="Choose Directory to Index")
    if directory:
        index_files(directory)

if __name__ == "__main__":
    choose_directory()
