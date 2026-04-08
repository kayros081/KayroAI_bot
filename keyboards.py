from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

ai_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📚 Конспектор"),
     KeyboardButton(text="🧠Выбрать модель")],
    [KeyboardButton(text="🗑 Сбросить контекст")]
], resize_keyboard=True)

conspector_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="⬇️Сохранить"),
     KeyboardButton(text="🧠 AI")],
    [KeyboardButton(text="📚 Все конспекты"),
     KeyboardButton(text="🔍 Поиск")],
     [KeyboardButton(text="❌Отмена")]

], resize_keyboard=True)

types_of_notes = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📝 Ручной ввод", callback_data="manual_water")],
    [InlineKeyboardButton(text="📷 Фото конспекта", callback_data="photo_notes")],
    [InlineKeyboardButton(text="🎤 Голосовой конспект", callback_data="voice_notes")]
])

ai_modals = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Llama", callback_data="llama")],
    [InlineKeyboardButton(text="Qwen", callback_data="qwen")]
])

KBsave_ai_response = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⬇️Сохранить", callback_data="save_ai_response")]
])