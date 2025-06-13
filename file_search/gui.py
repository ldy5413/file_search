import os
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser
from collections import Counter
from threading import Thread, Event
from .database import choose_directory, update_database
from .search import search_files
from .monitor import start_monitoring



class FileSearchApp:
    def __init__(self, root, stop_event):
        self.root = root
        self.root.title("File Search")
        self.stop_event = stop_event
        if not os.path.exists('file_index.db'):
            messagebox.showinfo("Indexing", "Please choose a directory to index.")
            choose_directory()

        # 启动时后台更新数据库
        if os.path.exists('file_index.db'):
            self.status_label = ttk.Label(root, text="")
            self.status_label.grid(row=2, column=2, padx=10, pady=10, sticky='se')
            update_thread = Thread(target=self.update_database_wrapper)
            update_thread.start()
        else:
            messagebox.showinfo("Indexing", "Please choose a directory to index.")
            choose_directory()

        self.search_label = ttk.Label(root, text="Search:")
        self.search_label.grid(row=0, column=1, padx=10, pady=10, sticky='w')

        self.search_entry = ttk.Entry(root, width=50)
        self.search_entry.grid(row=0, column=2, padx=10, pady=10, sticky='ew')

        self.search_button = ttk.Button(root, text="Search", command=self.perform_search)
        self.search_button.grid(row=0, column=3, padx=10, pady=10, sticky='e')

        self.sidebar = ttk.Frame(root)
        self.sidebar.grid(row=1, column=0, padx=10, pady=10, sticky='ns')

        self.all_button = ttk.Button(self.sidebar, text="All", command=lambda: self.filter_results('all'))
        self.all_button.pack(fill='x')

        self.folder_button = ttk.Button(self.sidebar, text="Folder", command=lambda: self.filter_results('folder'))
        self.folder_button.pack(fill='x')

        self.document_button = ttk.Button(self.sidebar, text="Document", command=lambda: self.filter_results('document'))
        self.document_button.pack(fill='x')

        self.other_button = ttk.Button(self.sidebar, text="Other", command=lambda: self.filter_results('other'))
        self.other_button.pack(fill='x')

        self.dynamic_buttons = []

        self.results_frame = ttk.Frame(root)
        self.results_frame.grid(row=1, column=1, columnspan=3, padx=10, pady=10, sticky='nsew')

        self.scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical")
        self.scrollbar.grid(row=0, column=1, sticky='ns')

        self.results_tree = ttk.Treeview(self.results_frame, columns=('Name', 'Path'), show='headings', yscrollcommand=self.scrollbar.set)
        self.results_tree.heading('Name', text='File Name')
        self.results_tree.heading('Path', text='Directory Path')
        self.results_tree.grid(row=0, column=0, sticky='nsew')
        self.scrollbar.config(command=self.results_tree.yview)

        self.results_frame.grid_rowconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(0, weight=1)

        self.results_tree.bind('<Double-1>', self.open_file)
        self.results_tree.bind('<Control-1>', self.open_file_directory)

        self.file_paths = []
        self.all_results = []

        # 添加窗口大小变化事件
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(2, weight=1)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_database_wrapper(self):
        update_database(self.status_label, self.stop_event)

    def perform_search(self):
        keyword = self.search_entry.get()
        keywords = keyword.split()
        results = search_files(keywords)
        sorted_results = self.sort_results(results, keywords)
        self.all_results = sorted_results
        self.update_treeview(sorted_results)
        self.update_dynamic_buttons()

    def sort_results(self, results, keywords):
        def score(result):
            path, _ = result
            filename = os.path.basename(path)
            filename_score = sum(1 for keyword in keywords if keyword.lower() in filename.lower())
            path_score = sum(1 for keyword in keywords if keyword.lower() in path.lower())
            return (filename_score, path_score)
        return sorted(results, key=score, reverse=True)

    def update_treeview(self, results):
        for i in self.results_tree.get_children():
            self.results_tree.delete(i)
        self.file_paths = []
        for result in results:
            self.file_paths.append(result[0])
            display_name = os.path.basename(result[0])
            self.results_tree.insert('', 'end', values=(display_name, result[0]))

    def filter_results(self, category):
        filtered_results = []
        for path, ftype in self.all_results:
            if category == 'all':
                filtered_results.append((path, ftype))
            elif category == 'folder' and ftype == 'directory':
                filtered_results.append((path, ftype))
            elif category == 'document' and path.endswith(('.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.md', '.txt')):
                filtered_results.append((path, ftype))
            elif category in path:
                filtered_results.append((path, ftype))
            elif category == 'other' and not ftype == 'directory' and not path.endswith(('.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.md', '.txt')) and not any(path.endswith(ext) for ext in self.get_most_common_extensions()):
                filtered_results.append((path, ftype))
        self.update_treeview(filtered_results)

    def update_dynamic_buttons(self):
        for btn in self.dynamic_buttons:
            btn.destroy()
        self.dynamic_buttons.clear()

        most_common_extensions = self.get_most_common_extensions()

        for ext in most_common_extensions:
            btn = ttk.Button(self.sidebar, text=ext, command=lambda ext=ext: self.filter_results(ext))
            btn.pack(fill='x')
            self.dynamic_buttons.append(btn)

    def get_most_common_extensions(self):
        counter = Counter(os.path.splitext(path)[1] for path, ftype in self.all_results if ftype != 'directory' and not path.endswith(('.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.md', '.txt')))
        return [ext for ext, count in counter.most_common(3)]

    def open_file(self, event):
        selected_item = self.results_tree.selection()
        if selected_item:
            file_path = self.results_tree.item(selected_item[0], 'values')[1]
            if os.path.isdir(file_path):
                webbrowser.open(file_path)
            else:
                webbrowser.open(file_path)

    def open_file_directory(self, event):
        selected_item = self.results_tree.selection()
        if selected_item:
            file_path = self.results_tree.item(selected_item[0], 'values')[1]
            if not os.path.isdir(file_path):
                directory = os.path.dirname(file_path)
                webbrowser.open(directory)
            else:
                webbrowser.open(file_path)

    def on_closing(self):
        self.stop_event.set()  # 设置事件来停止监控线程
        self.root.destroy()

if __name__ == "__main__":
    stop_event = Event()
    root = tk.Tk()
    app = FileSearchApp(root, stop_event)
    monitor_thread = Thread(target=start_monitoring,args=('C:\\', stop_event))
    monitor_thread.start()
    root.mainloop()
    monitor_thread.join()
