import json
import os
import urllib.request
import urllib.error
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

DATA_FILE = "favorites.json"
GITHUB_API_URL = "https://api.github.com/search/users?q="
GITHUB_USER_URL = "https://api.github.com/users/"

# Глобальные переменные
favorites = []
current_results = []
search_entry = None
results_tree = None
favorites_tree = None
info_text = None
status_label = None

def load_favorites():
    """Загрузка избранных из JSON"""
    global favorites
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                favorites = []
                for i, fav in enumerate(data, 1):
                    fav["id"] = i
                    favorites.append(fav)
        except:
            favorites = []

def save_favorites():
    """Сохранение избранных в JSON"""
    global favorites
    try:
        to_save = []
        for fav in favorites:
            to_save.append({
                "login": fav["login"],
                "type": fav["type"],
                "url": fav["url"],
                "added_date": fav["added_date"]
            })
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=4, ensure_ascii=False)
    except:
        messagebox.showerror("Ошибка", "Не удалось сохранить избранное")

def refresh_favorites_display():
    """Обновление таблицы избранных"""
    global favorites_tree, favorites
    for row in favorites_tree.get_children():
        favorites_tree.delete(row)

    for idx, fav in enumerate(favorites, 1):
        favorites_tree.insert("", tk.END, values=(idx, fav["login"], fav["type"],
                                                  fav.get("added_date", "Неизвестно"), "Удалить"))

def remove_from_favorites(login):
    """Удаление из избранного"""
    global favorites
    if messagebox.askyesno("Подтверждение", f"Удалить {login} из избранного?"):
        favorites = [f for f in favorites if f["login"] != login]
        save_favorites()
        refresh_favorites_display()
        messagebox.showinfo("Успех", f"{login} удалён из избранного")

def add_to_favorites(login, user_type, user_url):
    """Добавление в избранное"""
    global favorites
    existing = [f for f in favorites if f["login"] == login]
    if existing:
        messagebox.showinfo("Информация", f"{login} уже в избранном")
        return

    favorites.append({
        "login": login,
        "type": user_type,
        "url": user_url,
        "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_favorites()
    refresh_favorites_display()
    messagebox.showinfo("Успех", f"{login} добавлен в избранное!")

def show_user_info(login):
    """Показать информацию о пользователе"""
    global info_text, status_label
    info_text.delete(1.0, tk.END)
    info_text.insert(tk.END, f"Загрузка информации о {login}...\n")

    try:
        req = urllib.request.Request(GITHUB_USER_URL + login)
        req.add_header("User-Agent", "GitHub-User-Finder")

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

            info = f"""
╔════════════════════════════════════════════════════════╗
║              ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ                 ║
╚════════════════════════════════════════════════════════╝

Логин: {data.get('login', '-')}
Имя: {data.get('name', '-')}
Компания: {data.get('company', '-')}
Локация: {data.get('location', '-')}
Email: {data.get('email', '-')}

Репозиториев: {data.get('public_repos', 0)}
Подписчиков: {data.get('followers', 0)}
Подписок: {data.get('following', 0)}

Создан: {data.get('created_at', '-')[:10]}
Обновлён: {data.get('updated_at', '-')[:10]}

Профиль: {data.get('html_url', '-')}
            """
            info_text.delete(1.0, tk.END)
            info_text.insert(tk.END, info)
            status_label.config(text=f"Загружена информация о {login}")

    except Exception as e:
        info_text.delete(1.0, tk.END)
        info_text.insert(tk.END, f"Ошибка: {str(e)}")
        status_label.config(text="Ошибка загрузки")

def search_users():
    """Поиск пользователей"""
    global current_results, results_tree, search_entry, status_label

    query = search_entry.get().strip()
    if not query:
        messagebox.showwarning("Внимание", "Введите имя пользователя для поиска")
        return

    status_label.config(text=f"Поиск: {query}...")

    try:
        url = GITHUB_API_URL + urllib.parse.quote(query) + "&per_page=20"
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "GitHub-User-Finder")

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

            # Очистка таблицы
            for row in results_tree.get_children():
                results_tree.delete(row)

            current_results = []

            if "items" in data and data["items"]:
                for idx, user in enumerate(data["items"], 1):
                    login = user["login"]
                    user_type = user["type"]
                    current_results.append({
                        "id": idx,
                        "login": login,
                        "type": user_type,
                        "url": user.get("html_url", "")
                    })
                    results_tree.insert("", tk.END, values=(idx, login, user_type, "Добавить"))

                status_label.config(text=f"Найдено {len(current_results)} пользователей")
                messagebox.showinfo("Успех", f"Найдено {len(current_results)} пользователей!")
            else:
                status_label.config(text="Ничего не найдено")
                messagebox.showinfo("Результат", "Пользователи не найдены")

    except urllib.error.URLError:
        status_label.config(text="Ошибка сети")
        messagebox.showerror("Ошибка", "Нет подключения к интернету")
    except Exception as e:
        status_label.config(text="Ошибка")
        messagebox.showerror("Ошибка", str(e))

def on_results_click(event):
    """Обработка клика по таблице результатов"""
    selected = results_tree.selection()
    if not selected:
        return

    # Определяем колонку
    region = results_tree.identify_region(event.x, event.y)
    if region != "cell":
        return

    column = results_tree.identify_column(event.x, event.y)
    row_id = results_tree.identify_row(event.y)

    if not row_id:
        return

    values = results_tree.item(row_id)["values"]
    if not values or len(values) < 3:
        return

    login = values[1]

    # Проверяем, на какую ячейку нажали
    if column == "#4":  # Колонка Действие
        add_to_favorites(login, values[2], f"https://github.com/{login}")
    else:  # Нажатие на любую другую колонку - показываем инфо
        show_user_info(login)

def on_favorites_click(event):
    """Обработка клика по таблице избранных"""
    selected = favorites_tree.selection()
    if not selected:
        return

    column = favorites_tree.identify_column(event.x, event.y)
    row_id = favorites_tree.identify_row(event.y)

    if not row_id:
        return

    values = favorites_tree.item(row_id)["values"]
    if not values or len(values) < 3:
        return

    login = values[1]

    if column == "#5":  # Колонка Действие (Удалить)
        remove_from_favorites(login)
    else:
        show_user_info(login)

def clear_search():
    """Очистка результатов"""
    global results_tree, search_entry
    for row in results_tree.get_children():
        results_tree.delete(row)
    search_entry.delete(0, tk.END)

def main():
    global search_entry, results_tree, favorites_tree, info_text, status_label

    root = tk.Tk()
    root.title("GitHub User Finder")
    root.geometry("1100x700")

    load_favorites()

    # Верхняя панель
    top_frame = tk.Frame(root, bg="#24292e")
    top_frame.pack(fill="x")

    tk.Label(top_frame, text="GitHub User Finder", font=("Arial", 18, "bold"),
             fg="white", bg="#24292e").pack(pady=10)

    search_frame = tk.Frame(top_frame, bg="#24292e")
    search_frame.pack(pady=10)

    tk.Label(search_frame, text="Введите имя:", fg="white", bg="#24292e",
             font=("Arial", 11)).pack(side="left", padx=5)

    search_entry = tk.Entry(search_frame, width=30, font=("Arial", 11))
    search_entry.pack(side="left", padx=5)
    search_entry.bind("<Return>", lambda e: search_users())

    tk.Button(search_frame, text="Поиск", command=search_users, bg="#2ea44f",
              fg="white", font=("Arial", 10, "bold"), padx=15).pack(side="left", padx=5)

    tk.Button(search_frame, text="Очистить", command=clear_search, bg="#6c757d",
              fg="white", font=("Arial", 10, "bold"), padx=15).pack(side="left", padx=5)

    status_label = tk.Label(top_frame, text="Готов к поиску", fg="#c0c0c0",
                            bg="#24292e", font=("Arial", 9))
    status_label.pack(pady=5)

    # Основная панель с двумя таблицами
    main_frame = tk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Левая панель - результаты
    left_frame = tk.LabelFrame(main_frame, text="Результаты поиска", font=("Arial", 10, "bold"))
    left_frame.pack(side="left", fill="both", expand=True, padx=5)

    results_tree = ttk.Treeview(left_frame, columns=("ID", "Логин", "Тип", "Действие"),
                                 show="headings", height=20)
    results_tree.heading("ID", text="№")
    results_tree.heading("Логин", text="Логин")
    results_tree.heading("Тип", text="Тип")
    results_tree.heading("Действие", text="Действие")
    results_tree.column("ID", width=50, anchor="center")
    results_tree.column("Логин", width=200)
    results_tree.column("Тип", width=100, anchor="center")
    results_tree.column("Действие", width=100, anchor="center")

    scroll1 = ttk.Scrollbar(left_frame, orient="vertical", command=results_tree.yview)
    results_tree.configure(yscrollcommand=scroll1.set)
    results_tree.pack(side="left", fill="both", expand=True)
    scroll1.pack(side="right", fill="y")

    results_tree.bind("<ButtonRelease-1>", on_results_click)

    # Правая панель - избранное
    right_frame = tk.LabelFrame(main_frame, text="Избранные пользователи", font=("Arial", 10, "bold"))
    right_frame.pack(side="right", fill="both", expand=True, padx=5)

    favorites_tree = ttk.Treeview(right_frame, columns=("ID", "Логин", "Тип", "Дата", "Действие"),
                                   show="headings", height=20)
    favorites_tree.heading("ID", text="№")
    favorites_tree.heading("Логин", text="Логин")
    favorites_tree.heading("Тип", text="Тип")
    favorites_tree.heading("Дата", text="Дата добавления")
    favorites_tree.heading("Действие", text="Действие")
    favorites_tree.column("ID", width=50, anchor="center")
    favorites_tree.column("Логин", width=180)
    favorites_tree.column("Тип", width=80, anchor="center")
    favorites_tree.column("Дата", width=120, anchor="center")
    favorites_tree.column("Действие", width=80, anchor="center")

    scroll2 = ttk.Scrollbar(right_frame, orient="vertical", command=favorites_tree.yview)
    favorites_tree.configure(yscrollcommand=scroll2.set)
    favorites_tree.pack(side="left", fill="both", expand=True)
    scroll2.pack(side="right", fill="y")

    favorites_tree.bind("<ButtonRelease-1>", on_favorites_click)

    # Нижняя панель - информация
    info_frame = tk.LabelFrame(root, text="Информация о пользователе", font=("Arial", 10, "bold"))
    info_frame.pack(fill="x", padx=10, pady=10)

    info_text = tk.Text(info_frame, height=8, wrap=tk.WORD, font=("Courier", 9))
    info_text.pack(fill="both", expand=True, padx=5, pady=5)

    refresh_favorites_display()
    root.mainloop()

if __name__ == "__main__":
    main()
