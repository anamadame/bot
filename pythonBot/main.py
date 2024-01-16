import random
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

API_TOKEN = '6435404225:AAEQjablwZUodwaBnx_eE0WLOAFoybnTlGE'


# Исходный список слов с примерами
words = [
    ('быть', 'be', 'was/were', 'been'),
    ('идти', 'go', 'went', 'gone'),
    ('Понимать', 'understand', 'understood', 'understood'),
    ('Делать (выполнять)', 'do', 'did', 'done'),
    ('Делать (создавать что-то)', 'make', 'made', 'made'),
    ('Иметь', 'have', 'had', 'had'),
    ('Приходить', 'come', 'came', 'come'),
    ('Видеть', 'see', 'saw', 'seen'),
    ('Получать', 'get', 'got', 'got', 'gotten'),
    ('Покупать', 'buy', 'bought', 'bought'), ]


# Определение состояний
class TestStates(StatesGroup):
    waiting_for_first_form = State()
    waiting_for_second_form = State()
    waiting_for_third_form = State()

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Команда start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Напиши /add для добавления слова или /test для начала теста.")

# Добавление нового слова
@dp.message_handler(commands=['add'])
async def add_new_word(message: types.Message):
    await message.reply("Введите новое слово в формате: русское_слово,форма1,форма2,форма3")

    @dp.message_handler(state='*')
    async def add_word(message: types.Message):
        new_word = message.text.lower().split(',')
        if len(new_word) == 4:
            words.append(tuple(new_word))
            await message.reply("Слово добавлено!")
        else:
            await message.reply("Неверный формат. Попробуйте еще раз.")

# Команда test
@dp.message_handler(commands=['test'], state='*')
async def test(message: types.Message):
    rus, var1, var2, var3 = random.choice(words)
    await message.answer(f"Переведите слово '{rus}'. Введите первую форму:")
    await TestStates.waiting_for_first_form.set()
    async with dp.current_state(chat=message.chat.id, user=message.from_user.id).proxy() as data:
        data['answer'] = [var1, var2, var3]
        data['responses'] = []

# Обработка первой формы
@dp.message_handler(state=TestStates.waiting_for_first_form)
async def first_form(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['responses'] = [message.text.lower()]
    await message.reply("Введите вторую форму:")
    await TestStates.waiting_for_second_form.set()

# Обработка второй формы
@dp.message_handler(state=TestStates.waiting_for_second_form)
async def second_form(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['responses'].append(message.text.lower())
    await message.reply("Введите третью форму:")
    await TestStates.waiting_for_third_form.set()

# Функция, предлагающая следующие действия
async def suggest_next_action(message: types.Message):
    await message.answer("Тест завершен. Выберите следующее действие: /add, /test, /exit")

# Обработка третьей формы и завершение теста
@dp.message_handler(state=TestStates.waiting_for_third_form)
async def third_form(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['responses'].append(message.text.lower())
        if data['responses'] == data['answer']:
            await message.reply("Правильно!")
        else:
            await message.reply(f"Неправильно! Правильный ответ: {', '.join(data['answer'])}")
    await state.finish()
    await suggest_next_action(message)

# Команда exit
@dp.message_handler(commands=['exit'], state='*')
async def exit(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Вы вышли из теста. До новых встреч!')

# Команда stop
@dp.message_handler(commands=['stop'], state='*')
async def stop(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Вы вышли из теста.')

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)