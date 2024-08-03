import os
import sqlite3
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 定义需要忽略的文件名或路径特征
IGNORE_PATTERNS = ['file_index.db-journal', '.tmp','.TMP','C:\Windows','C:\PerfLogs','C:\ProgramData', 'AppData\Local','AppData\Roaming','.continue','.git','$Recycle.Bin']

def update_file_in_db(file_path):
    conn = sqlite3.connect('file_index.db')
    c = conn.cursor()
    if os.path.isdir(file_path):
        c.execute('INSERT OR IGNORE INTO files (path, name, type) VALUES (?, ?, ?)', (file_path, os.path.basename(file_path), 'directory'))
    else:
        c.execute('INSERT OR IGNORE INTO files (path, name, type) VALUES (?, ?, ?)', (file_path, os.path.basename(file_path), 'file'))
    conn.commit()
    conn.close()

def remove_file_from_db(file_path):
    conn = sqlite3.connect('file_index.db')
    c = conn.cursor()
    c.execute('DELETE FROM files WHERE path = ?', (file_path,))
    conn.commit()
    conn.close()

def should_ignore(path):
    for pattern in IGNORE_PATTERNS:
        if pattern in path:
            return True
    return False

class FileEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if should_ignore(event.src_path):
            return
        if not event.is_directory:
            print(f"File created: {event.src_path}")
        update_file_in_db(event.src_path)
        time.sleep(0.1)  # 添加短暂的延迟

    def on_deleted(self, event):
        if should_ignore(event.src_path):
            return
        if not event.is_directory:
            print(f"File deleted: {event.src_path}")
        remove_file_from_db(event.src_path)
        time.sleep(0.1)  # 添加短暂的延迟

    def on_moved(self, event):
        if should_ignore(event.src_path) or should_ignore(event.dest_path):
            return
        if not event.is_directory:
            print(f"File moved from {event.src_path} to {event.dest_path}")
        remove_file_from_db(event.src_path)
        update_file_in_db(event.dest_path)
        time.sleep(0.1)  # 添加短暂的延迟

def start_monitoring(directory_to_watch, stop_event,poll_interval=5.0):
    event_handler = FileEventHandler()
    observer = Observer(timeout=poll_interval)  # 设置轮询间隔时间
    observer.schedule(event_handler, directory_to_watch, recursive=True)
    observer.start()
    print(f"Started monitoring {directory_to_watch} with poll interval {poll_interval}s")
    try:
        while not stop_event.is_set():
            time.sleep(1)  # 主线程添加延迟，降低 CPU 占用
    except KeyboardInterrupt:
        observer.stop()
    observer.stop()
    observer.join()
    print(f"Stopped monitoring {directory_to_watch}")

if __name__ == "__main__":
    from threading import Event
    stop_event = Event()
    directory_to_watch = "C:\\"  # Change this to the directory you want to watch
    start_monitoring(directory_to_watch, stop_event, poll_interval=5.0)  # 可以调整轮询间隔时间以减少 CPU 占用
