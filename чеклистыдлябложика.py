import json
import os
import asyncio
import signal
import sys
import nest_asyncio
nest_asyncio.apply()
from datetime import datetime
from pathlib import Path
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
BOT_TOKEN = "ЗДЕСЬ МОГЛА БЫТЬ ВАША РЕКЛАМА, А ЛУЧШЕ ТОКЕН" #СЮДА ВСТАВЛЯЕМ ТОКЕН ИЗ БОТА @BotFather
CHECKLISTS_FILE = "checklists_data.json"
ACTIVE_CHECKLISTS_FILE = "active_checklists.json"
def load_checklists():
    """Загрузить чек-листы из файла"""
    try:
        if os.path.exists(CHECKLISTS_FILE):
            with open(CHECKLISTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}
def save_checklists(checklists):
    """Сохранить чек-листы в файл"""
    try:
        with open(CHECKLISTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(checklists, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False
def load_active_checklists():
    """Загрузить состояния вычеркивания"""
    try:
        if os.path.exists(ACTIVE_CHECKLISTS_FILE):
            with open(ACTIVE_CHECKLISTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}
def save_active_checklists(active_checklists):
    """Сохранить состояния вычеркивания"""
    try:
        with open(ACTIVE_CHECKLISTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(active_checklists, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def add_checklist(name, items):
    """Добавить новый чек-лист"""
    checklists = load_checklists()
    checklists[name] = {
        'items': items,
        'created_at': datetime.now().strftime("%d.%m.%Y %H:%M"),
        'updated_at': datetime.now().strftime("%d.%m.%Y %H:%M")
    }
    
    active_checklists = load_active_checklists()
    if name not in active_checklists:
        active_checklists[name] = [False] * len(items)
        save_active_checklists(active_checklists)
    
    return save_checklists(checklists)

def update_checklist(old_name, new_name=None, items=None):
    """Обновить чек-лист"""
    checklists = load_checklists()
    
    if old_name not in checklists:
        return False
    
    checklist = checklists[old_name]
    
    if new_name and new_name != old_name:
        checklists[new_name] = checklist
        del checklists[old_name]
        active_checklists = load_active_checklists()
        if old_name in active_checklists:
            active_checklists[new_name] = active_checklists[old_name]
            del active_checklists[old_name]
            save_active_checklists(active_checklists)
        
        old_name = new_name

    if items is not None:
        checklists[old_name]['items'] = items
        checklists[old_name]['updated_at'] = datetime.now().strftime("%d.%m.%Y %H:%M")

        active_checklists = load_active_checklists()
        if old_name in active_checklists:
            active_checklists[old_name] = [False] * len(items)
            save_active_checklists(active_checklists)
    
    return save_checklists(checklists)

def delete_checklist(name):
    """Удалить чек-лист"""
    checklists = load_checklists()
    if name in checklists:
        del checklists[name]
        
        active_checklists = load_active_checklists()
        if name in active_checklists:
            del active_checklists[name]
            save_active_checklists(active_checklists)
        
        return save_checklists(checklists)
    return False

def delete_checklist_item(checklist_name, item_index):
    """Удалить пункт из чек-листа"""
    checklists = load_checklists()
    
    if checklist_name not in checklists:
        return False
    
    items = checklists[checklist_name]['items']
    if item_index < 0 or item_index >= len(items):
        return False

    items.pop(item_index)
    checklists[checklist_name]['items'] = items
    checklists[checklist_name]['updated_at'] = datetime.now().strftime("%d.%m.%Y %H:%M")

    active_checklists = load_active_checklists()
    if checklist_name in active_checklists:
        if item_index < len(active_checklists[checklist_name]):
            active_checklists[checklist_name].pop(item_index)
            save_active_checklists(active_checklists)
    
    return save_checklists(checklists)

def add_checklist_item(checklist_name, item_text):
    """Добавить пункт в чек-лист"""
    checklists = load_checklists()
    
    if checklist_name not in checklists:
        return False
    
    items = checklists[checklist_name]['items']
    items.append(item_text)
    checklists[checklist_name]['items'] = items
    checklists[checklist_name]['updated_at'] = datetime.now().strftime("%d.%m.%Y %H:%M")

    active_checklists = load_active_checklists()
    if checklist_name in active_checklists:
        active_checklists[checklist_name].append(False)
        save_active_checklists(active_checklists)
    
    return save_checklists(checklists)

def get_checklists_list():
    """Получить список всех чек-листов"""
    checklists = load_checklists()
    return list(checklists.keys())

def get_checklist(name):
    """Получить конкретный чек-лист"""
    checklists = load_checklists()
    return checklists.get(name)

def toggle_checklist_item(checklist_name, item_index):
    """Переключить состояние пункта чек-листа"""
    active_checklists = load_active_checklists()
    
    if checklist_name not in active_checklists:
        checklist = get_checklist(checklist_name)
        if checklist:
            active_checklists[checklist_name] = [False] * len(checklist['items'])
    
    if item_index < len(active_checklists[checklist_name]):
        active_checklists[checklist_name][item_index] = not active_checklists[checklist_name][item_index]
        save_active_checklists(active_checklists)
        return True
    
    return False

def reset_checklist(checklist_name):
    """Сбросить все вычеркивания для чек-листа"""
    active_checklists = load_active_checklists()
    
    if checklist_name in active_checklists:
        checklist = get_checklist(checklist_name)
        if checklist:
            active_checklists[checklist_name] = [False] * len(checklist['items'])
            save_active_checklists(active_checklists)
            return True
    
    return False

def main_menu_keyboard():
    """Клавиатура главного меню"""
    keyboard = [
        [InlineKeyboardButton("📁 Мои чек-листы", callback_data="view")],
        [InlineKeyboardButton("➕ Создать чек-лист", callback_data="create")],
        [InlineKeyboardButton("✏️ Редактировать чек-лист", callback_data="edit")],
        [InlineKeyboardButton("🗑️ Удалить чек-лист", callback_data="delete")],
    ]
    return InlineKeyboardMarkup(keyboard)

def checklists_keyboard(action="show"):
    """Клавиатура со списком чек-листов"""
    checklists = get_checklists_list()
    keyboard = []
    
    for checklist_name in checklists:
        checklist = get_checklist(checklist_name)
        item_count = len(checklist['items']) if checklist else 0
        
        if action == "show":
            keyboard.append([
                InlineKeyboardButton(
                    f"📄 {checklist_name} ({item_count} шт)",
                    callback_data=f"show_{checklist_name}"
                )
            ])
        elif action == "edit":
            keyboard.append([
                InlineKeyboardButton(
                    f"✏️ {checklist_name}",
                    callback_data=f"edit_menu_{checklist_name}"
                )
            ])
        elif action == "delete":
            keyboard.append([
                InlineKeyboardButton(
                    f"🗑️ {checklist_name}",
                    callback_data=f"del_{checklist_name}"
                )
            ])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)

def checklist_items_keyboard(checklist_name, mode="toggle"):
    """Клавиатура с пунктами чек-листа"""
    checklist = get_checklist(checklist_name)
    if not checklist:
        return None
    
    keyboard = []
    
    for i, item in enumerate(checklist['items']):
        if mode == "toggle":
            active_checklists = load_active_checklists()
            completed = active_checklists.get(checklist_name, [False] * len(checklist['items']))
            status = "✅" if i < len(completed) and completed[i] else "⬜"
            keyboard.append([
                InlineKeyboardButton(
                    f"{status} {item}",
                    callback_data=f"toggle_{checklist_name}_{i}"
                )
            ])
        elif mode == "delete_item":
            keyboard.append([
                InlineKeyboardButton(
                    f"❌ {item}",
                    callback_data=f"delete_item_{checklist_name}_{i}"
                )
            ])
    
    if mode == "toggle":
        keyboard.append([
            InlineKeyboardButton("🔙 В список чек-листов", callback_data="view")
        ])
    
    return InlineKeyboardMarkup(keyboard)

def edit_menu_keyboard(checklist_name):
    """Клавиатура меню редактирования"""
    keyboard = [
        [InlineKeyboardButton("📝 Изменить название", callback_data=f"rename_{checklist_name}")],
        [InlineKeyboardButton("➕ Добавить пункт", callback_data=f"add_item_{checklist_name}")],
        [InlineKeyboardButton("🗑️ Удалить пункт", callback_data=f"delete_items_{checklist_name}")],
        [InlineKeyboardButton("🔙 В список чек-листов", callback_data="edit")],
    ]
    return InlineKeyboardMarkup(keyboard)

def confirmation_keyboard(action, checklist_name, item_index=None):
    """Клавиатура подтверждения"""
    if item_index is not None:
        callback_data = f"confirm_{action}_{checklist_name}_{item_index}"
    else:
        callback_data = f"confirm_{action}_{checklist_name}"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data=callback_data),
            InlineKeyboardButton("❌ Нет", callback_data=f"cancel_{action}_{checklist_name}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_keyboard():
    """Клавиатура только с кнопкой Назад"""
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back")]]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = (
        "👋 *Привет! Я бот для управления чек-листами*\n\n"
        "✨ *Новые возможности:*\n"
        "• ✅ Вычеркивай пункты нажатием\n"
        "• ✏️ Полное редактирование чек-листов\n"
        "• 📝 Изменение названий\n"
        "• 🔄 Автоматический сброс\n\n"
        "Выбери действие:"
    )
    
    if update.message:
        await update.message.reply_text(
            welcome_text,
            reply_markup=main_menu_keyboard(),
            parse_mode='Markdown'
        )
    else:
        await update.callback_query.edit_message_text(
            welcome_text,
            reply_markup=main_menu_keyboard(),
            parse_mode='Markdown'
        )

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /done"""
    if context.user_data.get('creating'):
        if 'name' in context.user_data:
            name = context.user_data['name']
            items = context.user_data.get('items', [])
            
            if not items:
                await update.message.reply_text(
                    "⚠️ Добавь хотя бы один пункт!\n"
                    "Отправь /cancel для отмены",
                    reply_markup=back_keyboard()
                )
                return
            
            if add_checklist(name, items):
                await update.message.reply_text(
                    f"✅ *Чек-лист создан!*\n"
                    f"Название: {name}\n"
                    f"Пунктов: {len(items)}",
                    reply_markup=main_menu_keyboard(),
                    parse_mode='Markdown'
                )
                context.user_data.clear()
            else:
                await update.message.reply_text(
                    "⚠️ Ошибка при создании!",
                    reply_markup=main_menu_keyboard()
                )
    
    # Добавляем обработку для изменения названия и добавления пунктов
    elif context.user_data.get('action') == 'renaming':
        checklist_name = context.user_data.get('checklist_name')
        new_name = update.message.text.strip()
        
        if not new_name:
            await update.message.reply_text(
                "⚠️ Название не может быть пустым!",
                reply_markup=back_keyboard()
            )
            return
        
        if update_checklist(checklist_name, new_name=new_name):
            await update.message.reply_text(
                f"✅ Чек-лист переименован!\n"
                f"Старое: {checklist_name}\n"
                f"Новое: {new_name}",
                reply_markup=main_menu_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "⚠️ Ошибка при переименовании!",
                reply_markup=main_menu_keyboard()
            )
        context.user_data.clear()
    
    elif context.user_data.get('action') == 'adding_item':
        checklist_name = context.user_data.get('checklist_name')
        new_item = update.message.text.strip()
        
        if not new_item:
            await update.message.reply_text(
                "⚠️ Пункт не может быть пустым!",
                reply_markup=back_keyboard()
            )
            return
        
        if add_checklist_item(checklist_name, new_item):
            checklist = get_checklist(checklist_name)
            await update.message.reply_text(
                f"✅ Пункт добавлен в *{checklist_name}*!\n"
                f"Теперь пунктов: {len(checklist['items'])}",
                reply_markup=main_menu_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "⚠️ Ошибка при добавлении пункта!",
                reply_markup=main_menu_keyboard()
            )
        context.user_data.clear()

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /cancel"""
    if context.user_data:
        await update.message.reply_text(
            "❌ Действие отменено.",
            reply_markup=main_menu_keyboard()
        )
        context.user_data.clear()
    else:
        await update.message.reply_text(
            "ℹ️ Нечего отменять.",
            reply_markup=main_menu_keyboard()
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Основное меню
    if data == "back":
        await query.edit_message_text(
            "📋 *Главное меню*",
            reply_markup=main_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    elif data == "view":
        checklists = get_checklists_list()
        
        if not checklists:
            await query.edit_message_text(
                "📭 *У тебя пока нет чек-листов*\n\n"
                "Создай первый чек-лист!",
                reply_markup=back_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "📂 *Твои чек-листы:*\n"
                "Выбери для просмотра:",
                reply_markup=checklists_keyboard("show"),
                parse_mode='Markdown'
            )
    
    elif data == "create":
        context.user_data['creating'] = True
        context.user_data['items'] = []
        
        await query.edit_message_text(
            "📝 *Создание нового чек-листа*\n\n"
            "Пришли мне название:",
            reply_markup=back_keyboard(),
            parse_mode='Markdown'
        )
    
    elif data == "edit":
        checklists = get_checklists_list()
        
        if not checklists:
            await query.edit_message_text(
                "📭 *Нет чек-листов для редактирования*",
                reply_markup=back_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "✏️ *Редактирование чек-листа*\n\n"
                "Выбери чек-лист для редактирования:",
                reply_markup=checklists_keyboard("edit"),
                parse_mode='Markdown'
            )
    
    elif data == "delete":
        checklists = get_checklists_list()
        
        if not checklists:
            await query.edit_message_text(
                "📭 *Нет чек-листов для удаления*",
                reply_markup=back_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "🗑️ *Удаление чек-листа*\n\n"
                "Выбери чек-лист:",
                reply_markup=checklists_keyboard("delete"),
                parse_mode='Markdown'
            )

    elif data.startswith("show_"):
        checklist_name = data[5:]
        checklist = get_checklist(checklist_name)
        
        if not checklist:
            await query.edit_message_text(
                "⚠️ Чек-лист не найден!",
                reply_markup=main_menu_keyboard()
            )
            return
        
        reset_checklist(checklist_name)
        
        message = (
            f"📋 *{checklist_name}*\n"
            f"🕒 Обновлен: {checklist['updated_at']}\n"
            f"📊 Пунктов: {len(checklist['items'])}\n\n"
            f"*Нажми на пункт чтобы вычеркнуть:*"
        )
        
        keyboard = checklist_items_keyboard(checklist_name, mode="toggle")
        if keyboard:
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
    
    elif data.startswith("toggle_"):
        parts = data.split("_")
        if len(parts) >= 3:
            checklist_name = parts[1]
            item_index = int(parts[2])
            
            if toggle_checklist_item(checklist_name, item_index):
                keyboard = checklist_items_keyboard(checklist_name, mode="toggle")
                if keyboard:
                    await query.edit_message_reply_markup(reply_markup=keyboard)
            else:
                await query.answer("⚠️ Ошибка!", show_alert=True)
    
    elif data.startswith("edit_menu_"):
        checklist_name = data[10:]
        
        checklist = get_checklist(checklist_name)
        if not checklist:
            await query.edit_message_text(
                "⚠️ Чек-лист не найден!",
                reply_markup=main_menu_keyboard()
            )
            return
        
        message = (
            f"✏️ *Редактирование чек-листа*\n\n"
            f"📋 *{checklist_name}*\n"
            f"🕒 Создан: {checklist['created_at']}\n"
            f"📊 Пунктов: {len(checklist['items'])}\n\n"
            f"Выбери действие:"
        )
        
        await query.edit_message_text(
            message,
            reply_markup=edit_menu_keyboard(checklist_name),
            parse_mode='Markdown'
        )
    
    elif data.startswith("rename_"):
        checklist_name = data[7:]
        context.user_data['action'] = 'renaming'
        context.user_data['checklist_name'] = checklist_name
        
        await query.edit_message_text(
            f"📝 *Переименование чек-листа*\n\n"
            f"Текущее название: *{checklist_name}*\n\n"
            f"Пришли мне новое название:",
            reply_markup=back_keyboard(),
            parse_mode='Markdown'
        )
    
    elif data.startswith("add_item_"):
        checklist_name = data[9:]
        context.user_data['action'] = 'adding_item'
        context.user_data['checklist_name'] = checklist_name
        
        await query.edit_message_text(
            f"➕ *Добавление пункта*\n\n"
            f"Чек-лист: *{checklist_name}*\n\n"
            f"Пришли мне текст нового пункта:",
            reply_markup=back_keyboard(),
            parse_mode='Markdown'
        )
    
    elif data.startswith("delete_items_"):
        checklist_name = data[13:]
        
        checklist = get_checklist(checklist_name)
        if not checklist or not checklist['items']:
            await query.edit_message_text(
                f"📭 *В чек-листе нет пунктов для удаления*\n\n"
                f"Чек-лист: *{checklist_name}*",
                reply_markup=edit_menu_keyboard(checklist_name),
                parse_mode='Markdown'
            )
            return
        
        message = (
            f"🗑️ *Удаление пункта из чек-листа*\n\n"
            f"Чек-лист: *{checklist_name}*\n"
            f"Выбери пункт для удаления:"
        )
        
        keyboard = checklist_items_keyboard(checklist_name, mode="delete_item")
        if keyboard:
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
    
    elif data.startswith("delete_item_"):
        parts = data.split("_")
        if len(parts) >= 4:
            checklist_name = parts[2]
            item_index = int(parts[3])
            
            checklist = get_checklist(checklist_name)
            if checklist and item_index < len(checklist['items']):
                item_text = checklist['items'][item_index]
                
                await query.edit_message_text(
                    f"⚠️ *Подтверждение удаления пункта*\n\n"
                    f"Чек-лист: *{checklist_name}*\n"
                    f"Пункт: *{item_text}*\n\n"
                    f"Точно удалить этот пункт?",
                    reply_markup=confirmation_keyboard("delete_item", checklist_name, item_index),
                    parse_mode='Markdown'
                )
    
    elif data.startswith("del_"):
        checklist_name = data[4:]
        await query.edit_message_text(
            f"⚠️ *Подтверждение удаления*\n\n"
            f"Точно удалить чек-лист *{checklist_name}*?",
            reply_markup=confirmation_keyboard("delete", checklist_name),
            parse_mode='Markdown'
        )
    elif data.startswith("confirm_delete_") and not data.startswith("confirm_delete_item_"):
        checklist_name = data[15:]
        
        if delete_checklist(checklist_name):
            await query.edit_message_text(
                f"✅ Чек-лист *{checklist_name}* удален!",
                reply_markup=main_menu_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "⚠️ Ошибка при удалении!",
                reply_markup=main_menu_keyboard()
            )
    
    elif data.startswith("confirm_delete_item_"):
        parts = data.split("_")
        if len(parts) >= 5:
            checklist_name = parts[3]
            item_index = int(parts[4])
            
            if delete_checklist_item(checklist_name, item_index):
                checklist = get_checklist(checklist_name)
                await query.edit_message_text(
                    f"✅ Пункт удален из *{checklist_name}*!\n"
                    f"Осталось пунктов: {len(checklist['items'])}",
                    reply_markup=edit_menu_keyboard(checklist_name),
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    "⚠️ Ошибка при удалении пункта!",
                    reply_markup=main_menu_keyboard()
                )
    
    elif data.startswith("cancel_"):
        parts = data.split("_")
        if len(parts) >= 3:
            action = parts[1]
            checklist_name = parts[2]
            
            if action in ["delete", "delete_item"]:
                await query.edit_message_text(
                    f"❌ Удаление отменено.",
                    reply_markup=edit_menu_keyboard(checklist_name),
                    parse_mode='Markdown'
                )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    text = update.message.text.strip()
    
    if text.startswith('/'):
        return
    
    if context.user_data.get('creating'):
        if 'name' not in context.user_data:
            context.user_data['name'] = text
            context.user_data['items'] = []
            
            await update.message.reply_text(
                f"📝 *Создание чек-листа: {text}*\n\n"
                "Теперь присылай пункты по одному.\n"
                "Когда закончишь - отправь команду */done*\n"
                "Для отмены - отправь */cancel*",
                reply_markup=back_keyboard(),
                parse_mode='Markdown'
            )
        else:
            context.user_data['items'].append(text)
            count = len(context.user_data['items'])
            
            await update.message.reply_text(
                f"✅ Пункт добавлен! Всего: {count}\n"
                "Присылай следующий пункт\n"
                "Или */done* для завершения",
                reply_markup=back_keyboard(),
                parse_mode='Markdown'
            )
    
    elif context.user_data.get('action') == 'renaming':
        checklist_name = context.user_data.get('checklist_name')
        new_name = text
        
        if not new_name:
            await update.message.reply_text(
                "⚠️ Название не может быть пустым!",
                reply_markup=back_keyboard()
            )
            return
        
        if update_checklist(checklist_name, new_name=new_name):
            await update.message.reply_text(
                f"✅ Чек-лист переименован!\n"
                f"Старое: {checklist_name}\n"
                f"Новое: {new_name}",
                reply_markup=main_menu_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "⚠️ Ошибка при переименовании!",
                reply_markup=main_menu_keyboard()
            )
        context.user_data.clear()
    
    elif context.user_data.get('action') == 'adding_item':
        checklist_name = context.user_data.get('checklist_name')
        new_item = text
        
        if not new_item:
            await update.message.reply_text(
                "⚠️ Пункт не может быть пустым!",
                reply_markup=back_keyboard()
            )
            return
        
        if add_checklist_item(checklist_name, new_item):
            checklist = get_checklist(checklist_name)
            await update.message.reply_text(
                f"✅ Пункт добавлен в *{checklist_name}*!\n"
                f"Теперь пунктов: {len(checklist['items'])}",
                reply_markup=main_menu_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "⚠️ Ошибка при добавлении пункта!",
                reply_markup=main_menu_keyboard()
            )
        context.user_data.clear()
    
    else:
        await update.message.reply_text(
            "Выбери действие в меню:",
            reply_markup=main_menu_keyboard()
        )

async def main():
    """Основная функция запуска бота"""
    print("🤖 Запускаю Telegram бота для чек-листов...")
    print(f"📁 Данные будут сохраняться в: {CHECKLISTS_FILE}")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("done", done))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Бот запущен и работает!")
    print("📱 Напиши /start своему боту в Telegram")
    print("🛑 Нажми Ctrl+C для остановки")
    
    await application.run_polling()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    except RuntimeError as e:
        print(f"Ошибка: {e}")
        sys.exit(1)