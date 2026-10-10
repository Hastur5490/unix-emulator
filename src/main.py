import tkinter as tk
from tkinter import scrolledtext
import getpass
import os

root = tk.Tk()

username = getpass.getuser()
root.title(f"Эмулятор пользователя - [{username}]")
root.geometry("800x800")
root.configure(bg="#121212")

output = scrolledtext.ScrolledText(root, 
                                   bg="#1e1e1e", 
                                   fg= "#FFD700", 
                                   font=("Consolas", 12), 
                                   wrap=tk.WORD)
output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
output.config(state="disabled")

command_entry = tk.Entry(root, 
                         bg="#2d2d2d", 
                         fg="white", 
                         insertbackground="white", 
                         font=("Consolas", 12))
command_entry.pack(fill=tk.X, padx=5, pady=5)
command_entry.focus()

def proccess_command(event=None):
    """Обработка введенной функции пользователем"""
    command = command_entry.get().strip()
    command_entry.delete(0, tk.END)
    if not command:
        return

    expanded_command = os.path.expandvars(command)

    parts = expanded_command.split()
    cmd = parts[0]
    args = parts[1:]

    output.config(state="normal")
    output.insert(tk.END, f"$ {command}\n")

    if cmd == "ls":
        output.insert(tk.END, f"Команда: ls\n")
        output.insert(tk.END, f"Аргумент: {args}\n")
    elif cmd == "cd":
        if len(args) > 1:
            output.insert(tk.END, "Ошибка: слишком много аргументов\n")
        else:
            output.insert(tk.END, f"Команда: cd\n")
            output.insert(tk.END, f"Аргумент: {args}\n")
    elif cmd == "exit":
        if len(args) > 0:
            output.insert(tk.END, "Ошибка: команда exit не принимает аргументы")
        else:
            output.insert(tk.END, "Выход...\n")
            output.see(tk.END)
            output.config(state="disabled")
            root.after(350, root.destroy)
            return
    else:
        output.insert(tk.END, f"Команда не найдена: {cmd}\n")

    output.insert(tk.END, "\n")
    output.see(tk.END)
    output.config(state="disabled")

command_entry.bind("<Return>", proccess_command)

root.mainloop()