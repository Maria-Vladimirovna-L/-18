import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
import json
import webbrowser
import os

# --- Настройки ---
FAVORITES_FILE = 'favorites.json'
GITHUB_API_URL = 'https://api.github.com/search/users'

# --- Функции работы с избранным ---
def load_favorites():
    """Загружает избранных пользователей из JSON."""
    try:
        with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_favorites(favorites):
    """Сохраняет избранных пользователей в JSON."""
    with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
        json.dump(favorites, f, ensure_ascii=False, indent=2)

# --- Функции поиска и интерфейса ---
def search_users():
    """Ищет пользователей по введенному запросу."""
    query = search_entry.get().strip()
    if not query:
        messagebox.showerror('Ошибка', 'Поле поиска не должно быть пустым')
        return

    try:
        response = requests.get(GITHUB_API_URL, params={'q': query})
        response.raise_for_status()  # Проверка на ошибки HTTP
        data = response.json()
        users = data.get('items', [])
        update_search_results(users)
    except requests.exceptions.RequestException as e:
        messagebox.showerror('Ошибка сети', f'Не удалось подключиться к GitHub API: {e}')
    except Exception as e:
        messagebox.showerror('Ошибка', f'Произошла непредвиденная ошибка: {e}')

def update_search_results(users):
    """Обновляет список результатов поиска в интерфейсе."""
    # Очищаем текущие результаты
    for i in results_tree.get_children():
        results_tree.delete(i)
    
    # Добавляем новых пользователей
    for user in users:
        login = user.get('login', '')
        avatar_url = user.get('avatar_url', '')
        html_url = user.get('html_url', '')
        
        # Проверяем, есть ли пользователь в избранном (для отображения кнопки)
        is_favorite = login in [fav['login'] for fav in favorites]
        
        results_tree.insert('', 'end', 
                           values=(login, avatar_url, html_url), 
                           tags=('favorite' if is_favorite else 'not_favorite'))

def on_user_click(event):
    """Обработчик двойного клика по пользователю (открывает профиль)."""
    item = results_tree.identify('item', event.x, event.y)
    if not item:
        return
    
    values = results_tree.item(item, 'values')
    if not values:
        return
    
    html_url = values[2]
    if html_url:
        webbrowser.open(html_url)

def toggle_favorite(event):
    """Добавляет или удаляет пользователя из избранного."""
    item = results_tree.identify('item', event.x, event.y)
    if not item:
        return

    values = results_tree.item(item, 'values')
    if not values:
        return

    login = values[0]
    
    # Ищем пользователя в глобальном списке избранного
    found_index = -1
    for i, fav in enumerate(favorites):
        if fav.get('login') == login:
            found_index = i
            break

    if found_index != -1:
        # Удаляем из избранного
        del favorites[found_index]
        messagebox.showinfo('Успех', f'Пользователь {login} удален из избранного.')
    else:
        # Добавляем в избранное (нужно получить полные данные)
        try:
            user_data = requests.get(f'https://api.github.com/users/{login}').json()
            favorites.append(user_data)
            messagebox.showinfo('Успех', f'Пользователь {login} добавлен в избранное.')
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось добавить в избранное: {e}')
            return

    save_favorites(favorites)
    update_search_results(get_current_search_results()) # Обновляем вид кнопок

def get_current_search_results():
    """Возвращает текущие данные в таблице результатов (для обновления статуса избранного)."""
    items = []
    for child in results_tree.get_children():
        values = results_tree.item(child, 'values')
        if values:
            login, avatar_url, html_url = values
            items.append({'login': login, 'avatar_url': avatar_url, 'html_url': html_url})
    return items

# --- Инициализация приложения ---
root = tk.Tk()
root.title('GitHub User Finder')
root.geometry('800x600')

# Загружаем избранное при старте
favorites = load_favorites()

# Поле поиска и кнопка
top_frame = ttk.Frame(root)
top_frame.pack(pady=10, fill='x')

search_entry = ttk.Entry(top_frame, width=50)
search_entry.pack(side='left', padx=5, expand=True, fill='x')

search_btn = ttk.Button(top_frame, text='Поиск', command=search_users)
search_btn.pack(side='left', padx=5)

# Таблица результатов поиска
results_tree = ttk.Treeview(root, columns=('Login', 'Avatar URL', 'Profile URL'), show='headings')
results_tree.heading('Login', text='Логин')
results_tree.column('Login', width=150)
results_tree.heading('Avatar URL', text='Аватар')
results_tree.column('Avatar URL', width=200)
results_tree.heading('Profile URL', text='Ссылка')
results_tree.column('Profile URL', width=200)
results_tree.pack(padx=10, pady=10, fill='both', expand=True)

# Настройка стилей для избранного (значок звезды)
style = ttk.Style()
style.configure('favorite.Treeview', background='#FFFACD') # Светло-желтый для избранных

# Привязка событий (клик и двойной клик)
results_tree.tag_configure('favorite', background='#FFFACD')
results_tree.tag_configure('not_favorite', background='white')
results_tree.bind('<Double-1>', on_user_click)  # Двойной клик открывает профиль
results_tree.bind('<Button-3>', toggle_favorite) # Правый клик добавляет/убирает из избранного

root.mainloop()
