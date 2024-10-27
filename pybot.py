from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from crud_functions import initiate_db, get_all_products

api = ""
bot = Bot(token=api)
dp = Dispatcher(bot, storage=MemoryStorage())

kb = ReplyKeyboardMarkup(resize_keyboard=True)
button1 = KeyboardButton(text='Рассчитать')
button2 = KeyboardButton(text='Информация')
button3 = KeyboardButton(text='Купить')
kb.add(button1).add(button2).add(button3)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Привет!", reply_markup=kb)

@dp.message_handler(text='Информация')
async def inform(message: types.Message):
    await message.answer('Привет! Я бот, помогающий твоему здоровью.')

@dp.message_handler(text='Купить')
async def buy(message: types.Message):
    await get_buying_list(message)

async def get_buying_list(message: types.Message):
    products = get_all_products()

    for product in products:
        await message.answer(
            f'Название: {product[1]} | Описание: {product[2]} | Цена: {product[3]}')

    markup = InlineKeyboardMarkup()
    for product in products:
        button = InlineKeyboardButton(product[1], callback_data="product_buying")
        markup.add(button)

    markup.add(InlineKeyboardButton("Назад", callback_data="back_to_catalog"))

    await message.answer('Выберите продукт для покупки:', reply_markup=markup)

@dp.callback_query_handler(text='product_buying')
async def send_confirm_message(call: types.CallbackQuery):
    await call.message.answer("Вы успешно приобрели продукт!")
    await call.answer()

class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()

@dp.message_handler(text='Рассчитать')
async def buttons(message: types.Message):
    markup = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton('Рассчитать норму калорий', callback_data='calories')
    button2 = InlineKeyboardButton('Формулы расчёта', callback_data='formulas')
    markup.add(button1, button2)
    await message.answer('Выберите опцию:', reply_markup=markup)

@dp.callback_query_handler(text='formulas')
async def get_formulas(call: types.CallbackQuery):
    await bot.send_message(call.message.chat.id,
                           'Формула Миффлина-Сан Жеора: 10 * вес (кг) + 6,25 * рост (см) - 5 * возраст (г) - 161')

@dp.callback_query_handler(text='calories')
async def set_age(call: types.CallbackQuery):
    await call.message.answer('Введите свой возраст:')
    await UserState.age.set()

@dp.message_handler(state=UserState.age)
async def set_growth(message: types.Message, state: FSMContext):
    if message.text.isdigit() and 0 < int(message.text) < 120:
        await state.update_data(age=int(message.text))
        await message.answer('Введите свой рост (в см):')
        await UserState.growth.set()
    else:
        await message.answer('Пожалуйста, введите корректный возраст.')

@dp.message_handler(state=UserState.growth)
async def set_weight(message: types.Message, state: FSMContext):
    if message.text.isdigit() and 0 < int(message.text) < 300:
        await state.update_data(growth=int(message.text))
        await message.answer('Введите свой вес (в кг):')
        await UserState.weight.set()
    else:
        await message.answer('Пожалуйста, введите корректный рост.')

@dp.message_handler(state=UserState.weight)
async def send_calories(message: types.Message, state: FSMContext):
    if message.text.isdigit() and 0 < int(message.text) < 500:
        await state.update_data(weight=int(message.text))
        data = await state.get_data()
        calories = 10 * data['weight'] + 6.25 * data['growth'] - 5 * data['age']
        await message.answer(f'Ваша норма калорий: {calories:.2f}')
        await state.finish()
    else:
        await message.answer('Пожалуйста, введите корректный вес.')

if __name__ == "__main__":
    initiate_db()
    executor.start_polling(dp, skip_updates=True)
