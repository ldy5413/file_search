import os
import sqlite3
import tkinter as tk
from tkinter import ttk
import webbrowser
import threading
import ctypes
from PIL import Image, ImageTk

# 创建数据库连接和游标
conn = sqlite3.connect('file_index.db')
c = conn.cursor()

# 创建文件索引表
c.execute('''CREATE TABLE IF NOT EXISTS files
             (path TEXT PRIMARY KEY, name TEXT, type TEXT)''')

# 遍历目录并索引文件和文件夹
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
# index_files('C:\\')

# 关闭数据库连接
conn.close()

def search_files(keyword):
    conn = sqlite3.connect('file_index.db')
    c = conn.cursor()
    query = f"SELECT path, type FROM files WHERE name LIKE ?"
    c.execute(query, ('%' + keyword + '%',))
    results = c.fetchall()
    conn.close()
    return results

def get_file_icon(file_path):
    shl = ctypes.windll.shell32
    shinfo = ctypes.create_string_buffer(692)
    res = shl.SHGetFileInfoW(file_path, 0, ctypes.byref(shinfo), ctypes.sizeof(shinfo), 0x101)
    hicon = ctypes.cast(ctypes.pointer(ctypes.c_int.from_buffer_copy(shinfo[4:8])), ctypes.POINTER(ctypes.c_void_p)).contents.value
    if hicon == 0:
        return None
    hdc = ctypes.windll.user32.GetDC(0)
    hbitmap = ctypes.windll.gdi32.CreateCompatibleBitmap(hdc, 32, 32)
    hdcMem = ctypes.windll.gdi32.CreateCompatibleDC(hdc)
    hOld = ctypes.windll.gdi32.SelectObject(hdcMem, hbitmap)
    ctypes.windll.user32.DrawIconEx(hdcMem, 0, 0, hicon, 32, 32, 0, None, 3)
    ctypes.windll.gdi32.SelectObject(hdcMem, hOld)
    ctypes.windll.gdi32.DeleteDC(hdcMem)
    ctypes.windll.user32.ReleaseDC(0, hdc)
    bmpinfo = ctypes.create_string_buffer(ctypes.sizeof(ctypes.c_ulong) * 32 * 32)
    ctypes.windll.gdi32.GetBitmapBits(hbitmap, ctypes.sizeof(bmpinfo), bmpinfo)
    img = Image.frombuffer('RGBA', (32, 32), bmpinfo, 'raw', 'BGRA', 0, 1)
    return ImageTk.PhotoImage(img)

class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None

    def show_tip(self, text, x, y):
        self.hide_tip()
        if not text:
            return
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self):
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None

class FileSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Search")

        self.search_label = ttk.Label(root, text="Search:")
        self.search_label.grid(row=0, column=0, padx=10, pady=10)

        self.search_entry = ttk.Entry(root, width=50)
        self.search_entry.grid(row=0, column=1, padx=10, pady=10)
        self.search_entry.bind('<KeyRelease>', self.delayed_search)

        self.search_button = ttk.Button(root, text="Search", command=self.perform_search)
        self.search_button.grid(row=0, column=2, padx=10, pady=10)

        self.results_frame = ttk.Frame(root)
        self.results_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')

        self.results_canvas = tk.Canvas(self.results_frame)
        self.results_canvas.grid(row=0, column=0, sticky='nsew')

        self.scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.results_canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        self.results_canvas.config(yscrollcommand=self.scrollbar.set)

        self.results_frame.grid_rowconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(0, weight=1)

        self.results_canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.results_canvas.bind("<Button-4>", self.on_mouse_wheel)
        self.results_canvas.bind("<Button-5>", self.on_mouse_wheel)
        self.results_canvas.bind("<Button-1>", self.on_click)

        self.tooltip = ToolTip(self.results_canvas)
        self.file_paths = []
        self.file_icons = []
        self.search_delay = 500  # 延迟时间（毫秒）
        self.after_id = None

    def delayed_search(self, event):
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.after_id = self.root.after(self.search_delay, self.perform_search)

    def perform_search(self):
        keyword = self.search_entry.get()
        threading.Thread(target=self.update_results, args=(keyword,)).start()

    def update_results(self, keyword):
        results = search_files(keyword)
        self.root.after(0, self.display_results, results)

    def display_results(self, results):
        self.results_canvas.delete("all")
        self.file_paths = []
        self.file_icons = []
        y = 0
        for result in results:
            self.file_paths.append(result[0])
            display_name = os.path.basename(result[0])
            if result[1] == 'directory':
                display_name += '/'
            icon = get_file_icon(result[0])
            if icon:
                self.file_icons.append(icon)
                self.results_canvas.create_image(10, y + 10, image=icon, anchor='nw')
            self.results_canvas.create_text(50, y + 10, text=display_name, anchor='nw')
            y += 40
        self.results_canvas.config(scrollregion=self.results_canvas.bbox("all"))
        if len(results) > 20:
            self.scrollbar.grid()
        else:
            self.scrollbar.grid_remove()

    def on_mouse_wheel(self, event):
        if event.num == 5 or event.delta == -120:
            self.results_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta == 120:
            self.results_canvas.yview_scroll(-1, "units")

    def on_click(self, event):
        selected_index = self.results_canvas.find_closest(event.x, event.y)[0] - 1
        if selected_index >= 0 and selected_index < len(self.file_paths):
            file_path = self.file_paths[selected_index]
            if os.path.isdir(file_path):
                webbrowser.open(file_path)
            else:
                webbrowser.open(file_path)

    def open_file_directory(self, event):
        selected_index = self.results_canvas.find_closest(event.x, event.y)[0] - 1
        if selected_index >= 0 and selected_index < len(self.file_paths):
            file_path = self.file_paths[selected_index]
            if os.path.isdir(file_path):
                webbrowser.open(file_path)
            else:
                directory = os.path.dirname(file_path)
                webbrowser.open(directory)

    def show_tooltip(self, event):
        selected_index = self.results_canvas.find_closest(event.x, event.y)[0] - 1
        if selected_index >= 0 and selected_index < len(self.file_paths):
            file_path = self.file_paths[selected_index]
            x = event.x_root + 20  # 偏移量
            y = event.y_root + 20  # 偏移量
            self.tooltip.show_tip(file_path, x, y)
        else:
            self.tooltip.hide_tip()

# 运行应用程序
root = tk.Tk()
app = FileSearchApp(root)
root.mainloop()
