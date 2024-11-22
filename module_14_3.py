from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

# Токен вашего бота
api = "7797606853:AAH0FVb0LqXiF23Kw02zc29LBi5nQW1OPTA"
bot = Bot(token=api)
dp = Dispatcher(bot, storage=MemoryStorage())

# Определяем состояния
class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()

# Список продуктов
products = [
    {"name": "Познать этот Мир", "desc": "Котёнок Рома", "price": 100, "image": "1.png"},
    {"name": "Живая Вода", "desc": 'Вода "Sant Anna" 1,5 л', "price": 200, "image": "2.png"},
    {"name": "Зима", "desc": "Закат", "price": 300, "image": "3.png"},
    {"name": "Символ", "desc": "Цель Жизни", "price": 400, "image": "4.png"}
]

# Обычное меню
def get_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Рассчитать", "Информация", "Купить"]
    keyboard.add(*buttons)
    return keyboard

# Inline-меню для продуктов
def get_inline_product_keyboard():
    keyboard = InlineKeyboardMarkup()
    buttons = [
        InlineKeyboardButton(text=product["name"], callback_data="product_buying")
        for product in products
    ]
    keyboard.add(*buttons)
    return keyboard

# Inline-меню для рассчёта калорий
def get_inline_keyboard():
    keyboard = InlineKeyboardMarkup()
    button_calories = InlineKeyboardButton(
        text="Рассчитать норму калорий", callback_data="calories"
    )
    button_formulas = InlineKeyboardButton(
        text="Формулы расчёта", callback_data="formulas"
    )
    keyboard.add(button_calories, button_formulas)
    return keyboard

# Хэндлер команды /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        "Привет! Я бот, помогающий твоему здоровью.\n"
        "Выберите одну из опций ниже:",
        reply_markup=get_main_keyboard()
    )

# Хэндлер для кнопки "Рассчитать"
@dp.message_handler(text="Рассчитать")
async def main_menu(message: types.Message):
    await message.answer("Выберите опцию:", reply_markup=get_inline_keyboard())

# Хэндлер для информации
@dp.message_handler(text="Информация")
async def info(message: types.Message):
    await message.answer(
        "Этот бот помогает рассчитать вашу норму калорий. "
        "Используйте кнопку 'Рассчитать', чтобы начать расчет."
    )

# Хэндлер для кнопки "Купить"
@dp.message_handler(text="Купить")
async def buying(message: types.Message):
    await get_buying_list(message)

# Функция для вывода списка продуктов
async def get_buying_list(message: types.Message):
    for product in products:
        text = f"Название: {product['name']} | Описание: {product['desc']} | Цена: {product['price']} руб."
        try:
            with open(f'files/{product["image"]}', "rb") as img:
                await message.answer_photo(photo=img, caption=text)
        except FileNotFoundError:
            await message.answer(f"Изображение для {product['name']} не найдено!")
    await message.answer("Выберите продукт для покупки:", reply_markup=get_inline_product_keyboard())

# Callback-хэндлер для покупки продуктов
@dp.callback_query_handler(lambda c: c.data == "product_buying")
async def send_confirm_message(call: types.CallbackQuery):
    await call.message.answer("Вы успешно приобрели продукт!")
    await call.answer()

# Хэндлер для формул расчета
@dp.callback_query_handler(text="formulas")
async def get_formulas(call: types.CallbackQuery):
    formula_text = (
        "Формула Миффлина-Сан Жеора для женщин:\n"
        "10 * вес (кг) + 6.25 * рост (см) - 5 * возраст (лет) - 161"
    )
    await call.message.answer(formula_text)
    await call.answer()

# Хэндлер для начала расчета калорий
@dp.callback_query_handler(text="calories")
async def set_age(call: types.CallbackQuery):
    await call.message.answer("Введите свой возраст:")
    await UserState.age.set()
    await call.answer()

# Хэндлер для ввода возраста
@dp.message_handler(state=UserState.age)
async def set_growth(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Возраст должен быть числом. Попробуйте еще раз:")
        return
    await state.update_data(age=int(message.text))
    await message.answer("Введите свой рост в сантиметрах:")
    await UserState.growth.set()

# Хэндлер для ввода роста
@dp.message_handler(state=UserState.growth)
async def set_weight(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Рост должен быть числом. Попробуйте еще раз:")
        return
    await state.update_data(growth=int(message.text))
    await message.answer("Введите свой вес в килограммах:")
    await UserState.weight.set()

# Хэндлер для ввода веса и расчета калорий
@dp.message_handler(state=UserState.weight)
async def send_calories(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Вес должен быть числом. Попробуйте еще раз:")
        return
    await state.update_data(weight=int(message.text))
    data = await state.get_data()

    # Формула Миффлина - Сан Жеора для женщин:
    bmr = 10 * data['weight'] + 6.25 * data['growth'] - 5 * data['age'] - 161
    await message.answer(f"Ваша норма калорий: {bmr:.2f}")

    # Завершаем состояние
    await state.finish()

if __name__ == "__main__":
    # Убедитесь, что папка files содержит изображения (1.png, 2.png, и т.д.)
    os.makedirs("files", exist_ok=True)  # Создаем папку для файлов, если её нет
    executor.start_polling(dp, skip_updates=True)