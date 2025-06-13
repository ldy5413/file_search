from threading import Event, Thread
import tkinter as tk
from .gui import FileSearchApp
from .monitor import start_monitoring


def main():
    stop_event = Event()
    root = tk.Tk()
    app = FileSearchApp(root, stop_event)
    monitor_thread = Thread(target=start_monitoring, args=('C:\\', stop_event))
    monitor_thread.start()
    root.mainloop()
    monitor_thread.join()


if __name__ == "__main__":
    main()
