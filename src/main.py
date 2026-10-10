import tkinter as tk
from tkinter import scrolledtext
import getpass
import os
import argparse
import socket
import csv
import base64
from io import StringIO

current_dir = "/"


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
    global output, command_entry, root, current_dir, vfs

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
            target = args[0] if args else current_dir

            if not target.startswith("/"):
                target = current_dir.rstrip("/") + "/" + target
            if target != "/":
                target = target.rstrip("/")

            items = []
            prefix = target if target.endswith("/") else target + "/"
            if target == "/":
                prefix = "/"

            for path in vfs:
                if path == target:
                    continue
                if path.startswith(prefix):
                    relative = path[len(prefix):].lstrip("/")
                    if "/" not in relative and relative:
                        items.append(relative)

            if not items and target not in vfs:
                output.insert(tk.END, f"Ошибка: нет такого файла или каталога: {target}\n")
            else:
                if items:
                    output.insert(tk.END, "  ".join(sorted(items)) + "\n")
                else:
                    output.insert(tk.END, "\n")
        elif cmd == "cd":
            if len(args) > 1:
                output.insert(tk.END, "Ошибка: слишком много аргументов\n")
                output.insert(tk.END, "Использование: cd [путь]\n")
            else:
                if not args:
                    current_dir = "/"
                    output.insert(tk.END, f"Текущая директория: {current_dir}\n")
                else:
                    target = args[0]

                    if not target.startswith("/"):
                        if current_dir == "/":
                            target = "/" + target
                        else:
                            target = current_dir.rstrip("/") + "/" + target

                    if target != "/":
                        target = target.rstrip("/")

                    if target in vfs and vfs[target]["type"] == "dir":
                        current_dir = target
                        output.insert(tk.END, f"Текущая директория: {current_dir}\n")
                    else:
                        output.insert(tk.END, 
                                      f"Ошибка: нет такого файла или каталога: {target}\n")
        elif cmd == "exit":
            output.insert(tk.END, "Выход из эмулятора...\n")
            output.see(tk.END)
            output.config(state="disabled")
            root.after(400, root.destroy)
            return
        elif cmd == "uname":
            output.insert(tk.END, "UNIX Shell Emulator\n")   
        elif cmd == "rev":
            if not args:
                output.insert(tk.END, "\n")
            else:
                for arg in args:
                    output.insert(tk.END, arg[::-1] + "\n")
        elif cmd == "find":
            if not args:
                for path in sorted(vfs.keys()):
                    output.insert(tk.END, path + "\n")
            else:
                start_path = args[0]

                if not start_path.startswith("/"):
                    if current_dir == "/":
                        start_path = "/" + start_path
                    else:
                        start_path = current_dir.rstrip("/") + "/" + start_path

                if start_path != "/":
                    start_path = start_path.rstrip("/")

                found = False
                for path in sorted(vfs.keys()):
                    if path == start_path or path.startswith(start_path + "/"):
                        output.insert(tk.END, path + "\n")
                        found = True

                if not found:
                    output.insert(tk.END, f"Ошибка: путь не найден: {start_path}\n")
        elif cmd == "rm":
            if not args:
                output.insert(tk.END, "Ошибка: укажите путь\n")
            elif len(args) > 1:
                output.insert(tk.END, "Ошибка: слишком много аргументов\n")
            else:
                target = args[0]

                if not target.startswith("/"):
                    if current_dir == "/":
                        target = "/" + target
                    else:
                        target = current_dir.rstrip("/") + "/" + target
                if target != "/":
                    target = target.rstrip("/")

                if target not in vfs:
                    output.insert(tk.END, f"Ошибка: нет такого файла или каталога: {target}\n")
                elif target == "/":
                    output.insert(tk.END, "Ошибка: нельзя удалить корневую директорию\n")
                else:
                    has_children = any(
                        p != target and p.startswith(target + "/")
                        for p in vfs
                    )
                    if has_children:
                        output.insert(tk.END, f"Ошибка: директория не пуста: {target}\n")
                    else:
                        del vfs[target]
                        output.insert(tk.END, f"Удалено: {target}\n")
        elif cmd == "chown":
            if len(args) != 2:
                output.insert(tk.END, "Ошибка: использование: chown владелец путь\n")
            else:
                owner = args[0]
                target = args[1]

                if not target.startswith("/"):
                    if current_dir == "/":
                        target = "/" + target
                    else:
                        target = current_dir.rstrip("/") + "/" + target
                if target != "/":
                    target = target.rstrip("/")

                if target not in vfs:
                    output.insert(tk.END, f"Ошибка: нет такого файла или каталога: {target}\n")
                else:
                    vfs[target]["owner"] = owner
                    output.insert(tk.END, f"Владелец {target} изменён на {owner}\n")
        elif cmd == "vfs-load":
            if len(args) != 1:
                output.insert(tk.END, "Ошибка: использование: vfs-load путь\n")
            else:
                new_vfs = load_vfs_from_csv(args[0])
                if new_vfs is None:
                    output.insert(tk.END, f"Ошибка: не удалось загрузить VFS из {args[0]}\n")
                else:
                    vfs = new_vfs
                    current_dir = "/"
                    output.insert(tk.END, f"VFS успешно загружена из {args[0]}\n")
                    output.insert(tk.END, f"Объектов: {len(vfs)}\n")
                    output.insert(tk.END, f"Текущая директория сброшена в /\n")
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
    global output, command_entry, root, current_dir, vfs

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
        target = args[0] if args else current_dir

        if not target.startswith("/"):
            target = current_dir.rstrip("/") + "/" + target
        if target != "/":
            target = target.rstrip("/")

        items = []
        prefix = target if target.endswith("/") else target + "/"
        if target == "/":
            prefix = "/"

        for path in vfs:
            if path == target:
                continue
            if path.startswith(prefix):
                relative = path[len(prefix):].lstrip("/")
                if "/" not in relative and relative:
                    items.append(relative)

        if not items and target not in vfs:
            output.insert(tk.END, f"Ошибка: нет такого файла или каталога: {target}\n")
        else:
            if items:
                output.insert(tk.END, "  ".join(sorted(items)) + "\n")
            else:
                output.insert(tk.END, "\n")
    elif cmd == "cd":

        if len(args) > 1:
            output.insert(tk.END, "Ошибка: слишком много аргументов\n")
            output.insert(tk.END, "Использование: cd [путь]\n")
        else:
            if not args:
                current_dir = "/"
                output.insert(tk.END, f"Текущая директория: {current_dir}\n")
            else:
                target = args[0]

                if not target.startswith("/"):
                    if current_dir == "/":
                        target = "/" + target
                    else:
                        target = current_dir.rstrip("/") + "/" + target

                if target != "/":
                    target = target.rstrip("/")

                if target in vfs and vfs[target]["type"] == "dir":
                    current_dir = target
                    output.insert(tk.END, f"Текущая директория: {current_dir}\n")
                else:
                    output.insert(tk.END, f"Ошибка: нет такого файла или каталога: {target}\n")
    elif cmd == "exit":
        if len(args) > 0:
            output.insert(tk.END, "Ошибка: команда exit не принимает аргументы")
        else:
            output.insert(tk.END, "Выход...\n")
            output.see(tk.END)
            output.config(state="disabled")
            root.after(350, root.destroy)
            return
    elif cmd == "uname":
        output.insert(tk.END, "UNIX Shell Emulator\n")
    elif cmd == "rev":
        if not args:
            output.insert(tk.END, "\n")
        else:
            for arg in args:
                output.insert(tk.END, arg[::-1] + "\n")
    elif cmd == "find":
        if not args:
            for path in sorted(vfs.keys()):
                output.insert(tk.END, path + "\n")
        else:
            start_path = args[0]

            if not start_path.startswith("/"):
                if current_dir == "/":
                    start_path = "/" + start_path
                else:
                    start_path = current_dir.rstrip("/") + "/" + start_path

            if start_path != "/":
                start_path = start_path.rstrip("/")

            found = False
            for path in sorted(vfs.keys()):
                if path == start_path or path.startswith(start_path + "/"):
                    output.insert(tk.END, path + "\n")
                    found = True

            if not found:
                output.insert(tk.END, f"Ошибка: путь не найден: {start_path}\n")
    elif cmd == "rm":
        if not args:
            output.insert(tk.END, "Ошибка: укажите путь\n")
        elif len(args) > 1:
            output.insert(tk.END, "Ошибка: слишком много аргументов\n")
        else:
            target = args[0]

            if not target.startswith("/"):
                if current_dir == "/":
                    target = "/" + target
                else:
                    target = current_dir.rstrip("/") + "/" + target
            if target != "/":
                target = target.rstrip("/")

            if target not in vfs:
                output.insert(tk.END, f"Ошибка: нет такого файла или каталога: {target}\n")
            elif target == "/":
                output.insert(tk.END, "Ошибка: нельзя удалить корневую директорию\n")
            else:
                has_children = any(
                    p != target and p.startswith(target + "/")
                    for p in vfs
                )
                if has_children:
                    output.insert(tk.END, f"Ошибка: директория не пуста: {target}\n")
                else:
                    del vfs[target]
                    output.insert(tk.END, f"Удалено: {target}\n")
    elif cmd == "chown":
        if len(args) != 2:
            output.insert(tk.END, "Ошибка: использование: chown владелец путь\n")
        else:
            owner = args[0]
            target = args[1]

            if not target.startswith("/"):
                if current_dir == "/":
                    target = "/" + target
                else:
                    target = current_dir.rstrip("/") + "/" + target
            if target != "/":
                target = target.rstrip("/")

            if target not in vfs:
                output.insert(tk.END, f"Ошибка: нет такого файла или каталога: {target}\n")
            else:
                vfs[target]["owner"] = owner
                output.insert(tk.END, f"Владелец {target} изменён на {owner}\n")
    elif cmd == "vfs-load":
        if len(args) != 1:
            output.insert(tk.END, "Ошибка: использование: vfs-load путь\n")
        else:
            new_vfs = load_vfs_from_csv(args[0])
            if new_vfs is None:
                output.insert(tk.END, f"Ошибка: не удалось загрузить VFS из {args[0]}\n")
            else:
                vfs = new_vfs
                current_dir = "/"
                output.insert(tk.END, f"VFS успешно загружена из {args[0]}\n")
                output.insert(tk.END, f"Объектов: {len(vfs)}\n")
                output.insert(tk.END, f"Текущая директория сброшена в /\n")
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