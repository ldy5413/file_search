import sqlite3

def search_files(keywords):
    conn = sqlite3.connect('file_index.db')
    c = conn.cursor()
    query = "SELECT path, type FROM files WHERE " + " AND ".join(["path LIKE ?"] * len(keywords))
    c.execute(query, tuple('%' + keyword + '%' for keyword in keywords))
    results = c.fetchall()
    conn.close()
    return results

# 例如搜索文件名中包含 "example" 的文件
# results = search_files('Recording 2024-08-01 145512')
# for result in results:
#     print(result[0])
