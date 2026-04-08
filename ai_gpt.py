import os
import asyncio
from fsm import AI_fsm, Conspector_fsm
from aiogram.types import Message, CallbackQuery
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from keyboards import ai_modals
from keyboards import ai_keyboard, conspector_keyboard, KBsave_ai_response
from huggingface_hub import AsyncInferenceClient
from aiogram.filters import StateFilter
from conspector import parse_tegs, conspect_preview
from database import ConspectDataBase

ai_clients = {}
ai_lock = asyncio.Lock()

MAX_MESSAGES_TOTAL = 40
KEEP_LAST = 24

ai_router = Router()


async def save_ai_response_conspect(callback: CallbackQuery, state: FSMContext, ai_answer: str):

    await callback.answer("Сохраняем...")

    if not ai_answer or not ai_answer.strip():
        await callback.message.edit_text("Нет ответа для сохранения 😕")
        return

    if await ConspectDataBase.is_limit_reached(callback.from_user.id):
        await callback.message.edit_text("⚠️ Лимит исчерпан. Удалите старые конспекты.")
        return

    content, tags = await parse_tegs(ai_answer)

    await ConspectDataBase.save_conspect(
        user_id=callback.from_user.id,
        content=content,
        content_type="text",
        file_id=None,
        tags=tags
    )

    response_text = conspect_preview("text", content, tags)
    await callback.message.edit_text(response_text)

@ai_router.callback_query(F.data == "save_ai_response")
async def save_ai(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    history = data.get("history", [])

    if history and len(history) >= 2:
        ai_answer = history[-1]["content"]
        await save_ai_response_conspect(callback, state, ai_answer)
    else:
        await callback.message.edit_text("Нет ответа для сохранения 😕")

@ai_router.message(F.text == "🧠 AI")
async def switch_ai(message: Message, state: FSMContext):
    await state.set_state(AI_fsm.qwenHF)
    await state.update_data(model="Qwen/Qwen2.5-7B-Instruct")
    await message.answer(
        "Режим AI активирован, теперь можешь задать любой вопрос ИИ\n"
        "Изначально отвечает Qwen, при желании можешь поменять модель\n",
        reply_markup=ai_keyboard
    )

@ai_router.message(F.text == "📚 Конспектор")
async def switch_conspector(message: Message, state: FSMContext):
    await state.set_state(Conspector_fsm.conspector)
    await message.answer("Вы вернулись в режим конспектора",
                         reply_markup=conspector_keyboard)


@ai_router.message(F.text == "🧠Выбрать модель")
async def startAImodels(message: Message):
    await message.answer(
        "Давай выберем кто тебе будет отвечать", reply_markup=ai_modals)
    
async def load_model():
    if "universal" in ai_clients:
        return ai_clients["universal"]
    
   
    client = AsyncInferenceClient(
        token=os.getenv("HF_KEY")
    )
    
    ai_clients["universal"] = client
    return client

async def generate_with_model(model: str, messages: list[dict]):
    client = await load_model()

    async with ai_lock:
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=512,
                temperature=0.7,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Ошибка Hugging face API {model}: {e}")
            raise

@ai_router.message(StateFilter(AI_fsm.qwenHF, AI_fsm.llamaHF), F.text == "🗑 Сбросить контекст")
async def reset_context(message: Message, state: FSMContext):
    history = [{
        "role": "system",
        "content": "Ты полезный и точный помощник. Отвечай точно на любом языке в зависимости от которого спрашивает пользователь"
    }]
    await state.update_data(history=history)
    await message.answer("Контекст сброшен, давай начнем новый чат")

@ai_router.message(StateFilter(AI_fsm.qwenHF, AI_fsm.llamaHF))
async def ai_response(message: Message, state: FSMContext):
    if message.text == "🗑 Сбросить контекст":
        return
    
    text = (message.text or "").strip()
    if not text:
        return
    
    data = await state.get_data()
    history = data.get("history", [])
    model = data.get("model")

    if not model:
        await message.answer("Модель не выбрана")
        return 
    
    if not history: 
            history = [{
                "role": "system",
                "content": "Ты полезный и точный помощник."
            }]

    history.append({"role": "user", "content": text})

    if len(history) > MAX_MESSAGES_TOTAL:
            history = [history[0]] + history[-KEEP_LAST:]

    thinking = await message.reply("Думаю...")

    try: 
            answer = await generate_with_model(model, history)
            history.append({"role": "assistant", "content": answer})

            await state.update_data(history=history)
            await thinking.edit_text(answer, reply_markup=KBsave_ai_response)

    except Exception as e:
                await thinking.edit_text("Не получилось ответить, попробуйте еще раз")
                print(f"Ошибка в работе модели {model}: {e}")



@ai_router.callback_query(F.data == "qwen")
async def qwenAnswer(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Qwen')
    await state.set_state(AI_fsm.qwenHF)
    await state.update_data(model="Qwen/Qwen2.5-7B-Instruct")

    await callback.message.edit_text(
        'Теперь тебе будет отвечать Qwen'
    )


@ai_router.callback_query(F.data == "llama")
async def geminiAnswer(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Llama')
    await state.set_state(AI_fsm.llamaHF)
    await state.update_data(model="meta-llama/Meta-Llama-3-8B-Instruct")

    await callback.message.edit_text(
        'Теперь тебе будет отвечать Llama')
    

