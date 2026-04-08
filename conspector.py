from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from fsm import Conspector_fsm
import keyboards
from database import ConspectDataBase
from keyboards import conspector_keyboard

consp_router = Router()

@consp_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(Conspector_fsm.conspector)
    await message.answer(
                        "Я KayroAI.\n"
                        "Решаю задачи в режиме AI. Сохраняю конспекты.\n"
                        "Типы конспектов:\n"
                        "• Ручной ввод (текст)\n"
                        "• Фото конспекта\n"
                        "• Голосовой конспект\n"
                        "Команды:\n"
                        "• «Все конспекты» — показать всё\n"
                        "• /del <номер> — удалить конспект\n"
                        "• /del_all — удалить все конспекты (осторожно!)\n"
                        "• «Поиск» — найти по ключевым словам\n"
                        "При сохранение конспекта в конце сообщение можешь добавить строку Теги: и указать свои теги\n",
                         reply_markup=conspector_keyboard)


@consp_router.message(F.text == "⬇️Сохранить")
async def saveConspect_button(message: Message, state: FSMContext):
    if await ConspectDataBase.is_limit_reached(message.from_user.id):
        await message.answer(f"⚠️ Лимит исчерпан. Удалите старые конспекты.",
            reply_markup=conspector_keyboard)
    else:
      await message.answer("Выберите тип конспекта\n Максимум сохранений - 85", reply_markup=keyboards.types_of_notes)

#After processing the callback request is sent to the database and work continues in the "database" module.
@consp_router.callback_query(F.data == 'manual_water')
async def manual_water(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Отправьте конспект текстом")
    await state.set_state(Conspector_fsm.WAITING_TEXT)
    
    await callback.message.edit_text(
        "Напиши конспект текстом"
    )

@consp_router.callback_query(F.data == 'photo_notes')
async def photo_notes(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Отправьте конспект через фото")
    await state.set_state(Conspector_fsm.WAITING_PHOTO)

    await callback.message.edit_text(
        "Отправь фото конспекта 📄"
    )

@consp_router.callback_query(F.data == "voice_notes")
async def voice_notes(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Отправьте конспект голосовым сообщением")
    await state.set_state(Conspector_fsm.WAITING_VOICE)

    await callback.message.edit_text(
        "Запиши голосовое сообщение с конспектом 🎤"
    )

@consp_router.message(F.text == "❌Отмена")
@consp_router.message(Command("cancel"))
async def cancel_activ(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять")
        return
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=conspector_keyboard)

@consp_router.message(F.text == "🔍 Поиск")
async def search(message: Message, state: FSMContext):
    await state.set_state(Conspector_fsm.WAITING_SEARCH)
    await message.answer("Введите теги для поиска конспекта")

async def parse_tegs(content: str | None) -> tuple[str, str]:
    if not content or not content.strip():
        generated = await ConspectDataBase.generate_tegs("")
        return "", generated

    lines = content.splitlines()
    if not lines:
        generated = await ConspectDataBase.generate_tegs("")
        return "", generated

    last_line = lines[-1].strip()
    if last_line.lower().startswith(("теги:", "tags:")):
        tag_part = last_line.split(":", 1)[1].strip()
        user_tags = [t.strip() for t in tag_part.split(",") if t.strip()]
        if user_tags:
            body = "\n".join(lines[:-1]).rstrip()
            return body, ", ".join(user_tags)

    generated = await ConspectDataBase.generate_tegs(content)
    return content, generated


def conspect_preview(content_type: str, content: str, tags: str) -> str:
    icons = {"text": "📝 Текст:", "photo": "📸 Описание:", "voice": "🎤 Описание:"}
    prefix = icons.get(content_type, "📎")
    
    body = content or "без описания"
    if len(body) > 100:
        body = body[:100] + "..."
        
    return (
        f"✅ {content_type.capitalize()} сохранён!\n\n"
        f"{prefix}\n{body}\n\n"
        f"🏷 Теги: {tags}"
    )


async def save_conspect(message: Message, state: FSMContext, content_type: str, content: str | None = None, file_id: str | None = None):
    try:
        if await ConspectDataBase.is_limit_reached(message.from_user.id):
         return await message.answer("⚠️ Лимит исчерпан. Удалите старые конспекты.")
    
        if content_type == "text":
            if not content or not content.strip():
                return await message.answer("Пустой конспект сохранить нельзя")
            
            content = content.strip()
        
        finish_text, tags = await parse_tegs(content)
             
        await ConspectDataBase.save_conspect(
            user_id=message.from_user.id,
            content=finish_text,
            content_type=content_type,
            file_id=file_id,
            tags=tags,
        )
        response_text = conspect_preview(content_type, finish_text, tags)
        await message.answer(response_text, reply_markup=conspector_keyboard)
        
        await state.set_state(Conspector_fsm.conspector)
    
    except Exception as e:
        print(f"Error in save_conspect {content_type}: {e}")
        await message.answer("❌ Ошибка при сохранении. Попробуйте позже.")

@consp_router.message(Conspector_fsm.WAITING_TEXT)
async def waiting_text(message: Message, state: FSMContext):
    await save_conspect(message, state, content_type="text", content=message.text)

@consp_router.message(Conspector_fsm.WAITING_PHOTO, F.photo)
async def waiting_photo(message: Message, state: FSMContext):
    await save_conspect(
        message, state, 
        content_type="photo", 
        content=message.caption or "Фото конспекта", 
        file_id=message.photo[-1].file_id
    )

@consp_router.message(Conspector_fsm.WAITING_VOICE, F.voice)

async def waiting_voice(message: Message, state: FSMContext):
    await save_conspect(
        message, state, 
        content_type="voice", 
        content=message.caption or "Голосовой конспект", 
        file_id=message.voice.file_id
    )

@consp_router.message(F.text == "📚 Все конспекты")
async def show_all_tags(message: Message):
    user_id = message.from_user.id
    
    try:
        conspects = await ConspectDataBase.get_user_conspects(user_id)
        
        if not conspects:
            return await message.answer("У тебя пока нет конспектов")

        lines = ["🏷 Теги всех твоих конспектов\n\n"]
        found_any = False

        for row in conspects:
            c_id = row[0]        
            tags_str = row[4] 

            if tags_str and tags_str.strip() and tags_str != "нет тегов":
                found_any = True
                lines.append(f"#{c_id:<4} → {tags_str}\n")

        if not found_any:
            return await message.answer("🏷 У твоих конспектов пока нет тегов")

        lines.append("\nВсего конспектов: " + str(len(conspects)))
        lines.append("\n")
        lines.append("Поиск по тегу → нажми «Поиск» и введи нужный тег")

        await message.answer("".join(lines), reply_markup=conspector_keyboard)

    except Exception as e:
        print(f"Ошибка при выводе тегов: {e}")
        await message.answer("❌ Не удалось загрузить теги")


@consp_router.message(Conspector_fsm.WAITING_SEARCH)
async def waiting_search(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        search_term = message.text.lower()

        found = await ConspectDataBase.search_conspects(user_id, search_term)

        if not found:
            await message.answer(
                f"🔍 По запросу {search_term} ничего не найдено",
                reply_markup=conspector_keyboard
            )
            return
        
        for conspect_id, content, content_type, file_id, tags in found:

            if content_type == "text":
                await message.answer(
                    f"🔍 найден текстовый конспект #{conspect_id}\n\n"
                    f"{content}\n\n"
                    f"🏷 теги: {tags or '—'}\n"
                )

            elif content_type == "photo" and file_id:
                await message.answer_photo(
                    photo=file_id,
                    caption=(
                        f"🔍 найден фото конспект #{conspect_id}\n\n"
                        f"{content or 'без описания'}\n\n"
                        f"🏷 теги: {tags or '—'}\n"
                    )
                )
            elif content_type == "voice" and file_id:
                await message.answer_voice(
                    voice=file_id,
                    caption=(
                        f"🔍 найден голосовой конспект #{conspect_id}\n\n"
                        f"{content or 'без описания'}\n\n"
                        f"🏷 теги: {tags or '—'}\n"
                    )
                )
            else:
                await message.answer(
                    f"🔍 найден конспект #{conspect_id} ({content_type})\n\n"
                    f"{content or '—'}\n\n"
                    f"🏷 теги: {tags or '—'}\n"
                )
        await state.set_state(Conspector_fsm.conspector)

    except Exception as e:
        print(f"Ошибка в waiting_search: {e}")
        await message.answer("❌ Произошла ошибка при поиске. Попробуйте позже")


@consp_router.message(Command("del"))
async def delete_conspect(message: Message):
    try:
        try:
            conspect_id = int(message.text.split()[1])
        except (IndexError, ValueError):
            await message.answer("Используй: /del <номер>\nПример: /del 1")
            return
        
        user_id = message.from_user.id
        deleted = await ConspectDataBase.delete_conspect(user_id, conspect_id)
        
        if deleted:
            await message.reply(f"✅ Конспект #{conspect_id} удалён")
        else:
            await message.reply(f"❌ Конспект #{conspect_id} не найден")
    except Exception as e:
        print(f"Ошибка в delete_conspect: {e}")
        await message.reply("❌ Не удалось удалить конспект.")


@consp_router.message(Command("del_all"))
async def delete_all_conspects(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        conspects = await ConspectDataBase.get_user_conspects(user_id)

        if not conspects:
            await message.reply("У вас нет сохранённых конспектов.")
            return
        
        await state.set_state(Conspector_fsm.DELETE_CONFIRM)
        await message.reply( f"⚠️ Вы собираетесь удалить ВСЕ ваши конспекты ({len(conspects)} штук)!\n"
                        "Это действие необратимо. Подтвердите: 'Да' или 'Нет'.")
    except Exception as e:
        print(f"Ошибка в delete_all_conspects: {e}")
        await message.reply("❌ Произошла ошибка при подготовке к удалению.")

@consp_router.message(Conspector_fsm.DELETE_CONFIRM)
async def delete_confirmation(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        text = message.text.strip().lower()

        if text in ['да', 'yes', 'y', 'д', 'удалить', 'Да']:
            deleted_count = await ConspectDataBase.delete_all_conspects(user_id)
            await message.reply(f"✅ Все {deleted_count} конспектов удалены!")
        else:
            await message.reply("❌ Удаление отменено")
        await state.clear()
    except Exception as e:
        print(f"Ошибка в delete_confirmation: {e}")
        await message.reply("❌ Ошибка при выполнении операции.")
        await state.clear()

@consp_router.errors()
async def error(event):
    print(f"Непойманная ошибка: {event.exception}")
    if event.update.message:
        try:
            await event.update.message.answer(
                "Произошла внутреняя ошибка. Попробуйте позже"
            )
        except:
            pass
        