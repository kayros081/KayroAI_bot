from aiogram.fsm.state import StatesGroup, State

class Conspector_fsm(StatesGroup):
    conspector = State()
    WAITING_TEXT = State()
    WAITING_PHOTO = State()
    WAITING_VOICE = State()
    WAITING_SEARCH = State()
    DELETE_CONFIRM = State()
    
    
class AI_fsm(StatesGroup):
    llamaHF = State()
    qwenHF = State()