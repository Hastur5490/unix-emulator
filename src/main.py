import tkinter as tk
from tkinter import scrolledtext
import getpass
import os
import argparse
import socket
import csv
import base64

EXIT_DELAY_MS = 400
SCRIPT_START_DELAY_MS = 100

root = None
output = None
command_entry = None
vfs = {}

def load_vfs_from_csv(path):
    """Загружает VFS из CSV-файла в память."""
    result = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                p = row["path"].strip()
                t = row["type"].strip()
                content = row.get("content", "")
                if t == "file" and content:
                    try:
                        decoded = base64.b64decode(content)
                        content = decoded.decode("utf-8")
                    except Exception:
                        pass
                result[p] = {"type": t, "content": content}
        return result
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
            "content": "Это файл по умолчанию",
        },
    }

def handle_command(cmd, args):
    """Обрабатывает одну команду. Возвращает True при ошибке."""
    if cmd == "ls":
        output.insert(tk.END, "Команда: ls\n")
        output.insert(tk.END, f"Аргументы: {args}\n")
        return False

    if cmd == "cd":
        if len(args) > 1:
            output.insert(tk.END, "Ошибка: слишком много аргументов\n")
            output.insert(tk.END, "Использование: cd [путь]\n")
            return True
        output.insert(tk.END, "Команда: cd\n")
        output.insert(tk.END, f"Аргументы: {args}\n")
        return False

    if cmd == "exit":
        if args:
            output.insert(tk.END, "Ошибка: exit не принимает аргументы\n")
            return True
        output.insert(tk.END, "Выход из эмулятора...\n")
        output.see(tk.END)
        output.config(state="disabled")
        root.after(EXIT_DELAY_MS, root.destroy)
        return False

    output.insert(tk.END, f"Ошибка: команда не найдена: {cmd}\n")
    return True

def execute_script(script_path):
    """Выполняет стартовый скрипт. Останавливается при ошибке."""
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

        parts = os.path.expandvars(command).split()
        error = handle_command(parts[0], parts[1:])

        output.insert(tk.END, "\n")
        output.see(tk.END)
        output.config(state="disabled")

        if error:
            print(f"Скрипт остановлен: {command}")
            return

def process_command(event=None):
    """Обрабатывает команду из поля ввода."""
    command = command_entry.get().strip()
    command_entry.delete(0, tk.END)
    if not command:
        return

    output.config(state="normal")
    output.insert(tk.END, f"$ {command}\n")

    parts = os.path.expandvars(command).split()
    handle_command(parts[0], parts[1:])

    output.insert(tk.END, "\n")
    output.see(tk.END)
    output.config(state="disabled")

def create_gui():
    """Создаёт графический интерфейс."""
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
        wrap=tk.WORD,
    )
    output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    output.config(state="disabled")

    command_entry = tk.Entry(
        root,
        bg="#2d2d2d",
        fg="white",
        insertbackground="white",
        font=("Consolas", 12),
    )
    command_entry.pack(fill=tk.X, padx=5, pady=5)
    command_entry.focus()
    command_entry.bind("<Return>", process_command)

def main():
    """Точка входа в приложение."""
    global vfs

    parser = argparse.ArgumentParser(description="UNIX Shell Emulator")
    parser.add_argument("--vfs", type=str, default=None, help="Путь к VFS")
    parser.add_argument(
        "--script", type=str, default=None, help="Путь к скрипту"
    )
    args = parser.parse_args()

    print("=== Отладочный вывод параметров ===")
    print(f"VFS path    : {args.vfs}")
    print(f"Script path : {args.script}")
    print("===================================")

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

    create_gui()

    if args.script:
        root.after(
            SCRIPT_START_DELAY_MS,
            lambda: execute_script(args.script),
        )

    root.mainloop()

if __name__ == "__main__":
    main()