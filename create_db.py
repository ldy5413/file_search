import os
import sqlite3

# 创建数据库连接和游标
conn = sqlite3.connect('file_index.db')
c = conn.cursor()

# 创建文件索引表
c.execute('''CREATE TABLE IF NOT EXISTS files
             (path TEXT PRIMARY KEY, name TEXT, type TEXT)''')

# 遍历目录并索引文件
def index_files(directory):
    for root, dirs, files in os.walk(directory):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            c.execute('INSERT OR IGNORE INTO files (path, name, type) VALUES (?, ?, ?)', (dir_path, dir_name, 'directory'))
        for file in files:
            file_path = os.path.join(root, file)
            c.execute('INSERT OR IGNORE INTO files (path, name, type) VALUES (?, ?, ?)', (file_path, file, 'file'))
    conn.commit()

# 例如索引 C: 盘
index_files('C:\\')

# 关闭数据库连接
conn.close()
