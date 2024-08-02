import os
import sqlite3
import tkinter as tk
from tkinter import ttk
import webbrowser
from collections import Counter

def search_files(keywords):
    conn = sqlite3.connect('file_index.db')
    c = conn.cursor()
    query = "SELECT path, type FROM files WHERE " + " AND ".join(["path LIKE ?"] * len(keywords))
    c.execute(query, tuple('%' + keyword + '%' for keyword in keywords))
    results = c.fetchall()
    conn.close()
    return results

class FileSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Search")

        self.search_label = ttk.Label(root, text="Search:")
        self.search_label.grid(row=0, column=1, padx=10, pady=10)

        self.search_entry = ttk.Entry(root, width=50)
        self.search_entry.grid(row=0, column=2, padx=10, pady=10)

        self.search_button = ttk.Button(root, text="Search", command=self.perform_search)
        self.search_button.grid(row=0, column=3, padx=10, pady=10)

        self.sidebar = ttk.Frame(root)
        self.sidebar.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')

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

    def perform_search(self):
        keyword = self.search_entry.get()
        keywords = keyword.split()
        results = search_files(keywords)
        self.all_results = results
        self.update_treeview(results)
        self.update_dynamic_buttons()

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
        # 清除旧的动态按钮
        for btn in self.dynamic_buttons:
            btn.destroy()
        self.dynamic_buttons.clear()

        # 统计文件后缀
        counter = Counter(os.path.splitext(path)[1] for path, ftype in self.all_results if ftype != 'directory' and not path.endswith(('.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.md', '.txt')))

        # 获取最常见的前三个文件后缀
        most_common_extensions = [ext for ext, count in counter.most_common(3)]

        # 创建新的动态按钮
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

# 运行应用程序
root = tk.Tk()
app = FileSearchApp(root)
root.mainloop()
