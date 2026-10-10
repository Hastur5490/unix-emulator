import tkinter as tk
from tkinter import scrolledtext
import getpass
import os
import argparse
import socket
import csv
import base64
from io import StringIO


def load_vfs_from_csv(path):
    """Загружает VFS из CSV-файла в память."""
    vfs = {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                p = row["path"].strip()
                t = row["type"].strip()
                content = row.get("content", "")

                if t == "file" and content:
                    try:
                        content = base64.b64decode(content).decode("utf-8")
                    except Exception:
                        pass

                vfs[p] = {"type": t, "content": content}

        return vfs

    except FileNotFoundError:
        print(f"Ошибка: файл VFS не найден: {path}")
        return None
    except Exception as e:
        print(f"Ошибка: неверный формат VFS: {e}")
        return None


def create_default_vfs():
    """Создаёт минимальную VFS в памяти."""
    return {
        "/": {"type": "dir", "content": ""},
        "/home": {"type": "dir", "content": ""},
        "/home/user": {"type": "dir", "content": ""},
        "/home/user/readme.txt": {
            "type": "file",
            "content": "Это файл по умолчанию"
        },
    }
    

def execute_script(script_path):
    """Выполняет стартовый скрипт. Останавливается при первой ошибке."""
    global output, command_entry, root

    try:
        with open(script_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Ошибка: файл скрипта не найден: {script_path}")
        return
    except Exception as e:
        print(f"Ошибка при чтении скрипта: {e}")
        return

    for line in lines:
        command = line.strip()

        if not command or command.startswith("#"):
            continue

        output.config(state="normal")
        output.insert(tk.END, f"$ {command}\n")
        output.config(state="disabled")

        expanded = os.path.expandvars(command)
        parts = expanded.split()
        cmd = parts[0]
        args = parts[1:]

        output.config(state="normal")

        if cmd == "ls":
            output.insert(tk.END, f"Команда: ls\n")
            output.insert(tk.END, f"Аргументы: {args}\n")
        elif cmd == "cd":
            if len(args) > 1:
                output.insert(tk.END, "Ошибка: слишком много аргументов\n")
                output.insert(tk.END, "Использование: cd [путь]\n")
                output.insert(tk.END, "\n")
                output.see(tk.END)
                output.config(state="disabled")
                print(f"Скрипт остановлен из-за ошибки в команде: {command}")
                return
            else:
                output.insert(tk.END, f"Команда: cd\n")
                output.insert(tk.END, f"Аргументы: {args}\n")
        elif cmd == "exit":
            output.insert(tk.END, "Выход из эмулятора...\n")
            output.see(tk.END)
            output.config(state="disabled")
            root.after(400, root.destroy)
            return
        else:
            output.insert(tk.END, f"Ошибка: команда не найдена: {cmd}\n")
            output.insert(tk.END, "\n")
            output.see(tk.END)
            output.config(state="disabled")
            print(f"Скрипт остановлен из-за ошибки в команде: {command}")
            return

        output.insert(tk.END, "\n")
        output.see(tk.END)
        output.config(state="disabled")

def proccess_command(event=None):
    """Обработка введенной функции пользователем"""
    global output, command_entry, root

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

def main():
    """Точка входа в приложение."""
    parser = argparse.ArgumentParser(description="UNIX Shell Emulator")
    parser.add_argument(
        "--vfs",
        type=str,
        default=None,
        help="Путь к физическому расположению VFS"
    )
    parser.add_argument(
        "--script",
        type=str,
        default=None,
        help="Путь к стартовому скрипту"
    )
    args = parser.parse_args()

    print("\tОтладочный вывод параметров")
    print(f"VFS path    : {args.vfs}")
    print(f"Script path : {args.script}")

    global vfs

    if args.vfs:
        print(f"Загрузка VFS из файла: {args.vfs}")
        vfs = load_vfs_from_csv(args.vfs)
        if vfs is None:
            print("Не удалось загрузить VFS. Завершение работы.")
            return
    else:
        print("Путь к VFS не указан. Создаётся VFS по умолчанию.")
        vfs = create_default_vfs()

    print(f"VFS успешно загружена. Объектов: {len(vfs)}")

    global root, output, command_entry

    username = getpass.getuser()
    hostname = socket.gethostname()

    root = tk.Tk()
    root.title(f"Эмулятор - [{username}@{hostname}]")
    root.geometry("800x600")
    root.configure(bg="#121212")

    output = scrolledtext.ScrolledText(
        root,
        bg="#1e1e1e",
        fg="#FFD700",
        font=("Consolas", 12),
        wrap=tk.WORD
    )
    output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    output.config(state="disabled")

    command_entry = tk.Entry(
        root,
        bg="#2d2d2d",
        fg="white",
        insertbackground="white",
        font=("Consolas", 12)
    )
    command_entry.pack(fill=tk.X, padx=5, pady=5)
    command_entry.focus()
    command_entry.bind("<Return>", proccess_command)

    if args.script:
        root.after(100, lambda: execute_script(args.script))

    root.mainloop()

if __name__ == "__main__":
    main()