import os, time
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


def update_database(status_label):
    start_time = time.time()
    status_label.config(text="Start indexing...")
    status_label.update_idletasks()

    conn = sqlite3.connect('file_index.db')
    c = conn.cursor()
    
    # 获取当前数据库中的文件路径
    c.execute('SELECT path FROM files')
    db_files = set(row[0] for row in c.fetchall())
    
    # 遍历C盘并更新数据库
    c_drive_files = set()
    for root, dirs, files in os.walk('C:\\'):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            c_drive_files.add(dir_path)
            if dir_path not in db_files:
                c.execute('INSERT OR IGNORE INTO files (path, name, type) VALUES (?, ?, ?)', (dir_path, dir_name, 'directory'))
        for file in files:
            file_path = os.path.join(root, file)
            c_drive_files.add(file_path)
            if file_path not in db_files:
                c.execute('INSERT OR IGNORE INTO files (path, name, type) VALUES (?, ?, ?)', (file_path, file, 'file'))
    
    # 删除数据库中不存在于C盘中的文件路径
    for file_path in db_files:
        if file_path not in c_drive_files:
            c.execute('DELETE FROM files WHERE path = ?', (file_path,))
    
    conn.commit()
    conn.close()

    end_time = time.time()
    elapsed_time = end_time - start_time
    status_label.config(text=f"Indexed within {elapsed_time:.2f} seconds.")
    status_label.update_idletasks()

if __name__ == "__main__":
    choose_directory()
