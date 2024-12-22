import datetime
import requests
import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from config import TOKEN, API_URL

# Инициализация бота
bot = Bot(token=TOKEN)
router = Router()

# Сохранение номера группы пользователя (в упрощенном варианте)
user_group = {}

# Функция для получения расписания по API
def get_schedule(group_number, week_number=None, day=None):
    url = f"{API_URL}{group_number}/"
    params = {}

    if week_number:
        params['week'] = week_number
    if day:
        params['day'] = day

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()  # Возвращает расписание в виде JSON
    else:
        return None


@router.message(Command(commands=["start"]))
async def start(message: Message):
    user_group[message.from_user.id] = None  # Сбрасываем номер группы при новом старте

    # Исправление: передача текста через параметр text
    button_cancel = KeyboardButton(text="/cancel")

    # Создаем клавиатуру
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[button_cancel]],
        resize_keyboard=True
    )

    await message.answer(
        "Привет! Я бот для получения расписания ЛЭТИ.\nВведите номер вашей группы:",
        reply_markup=keyboard
    )


# Обработка ввода номера группы
@router.message(lambda message: user_group.get(message.from_user.id) is None)
async def handle_group_number(message: Message):
    group_number = message.text.strip()

    # Сохраняем номер группы
    user_group[message.from_user.id] = group_number

    # Создаем клавиатуру с кнопками действий
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Следующая пара")],
            [KeyboardButton(text="Расписание на день")],
            [KeyboardButton(text="Расписание на неделю")],
            [KeyboardButton(text="Расписание на завтра")]
        ],
        resize_keyboard=True
    )

    await message.answer(f"Группа {group_number} сохранена. Выберите действие:", reply_markup=keyboard)


# Обработчик кнопки "Следующая пара"
@router.message(lambda message: message.text == "Следующая пара")
async def near_lesson(message: Message):
    group_number = user_group.get(message.from_user.id)
    if not group_number:
        await message.answer("Сначала введите номер группы с помощью команды /start.")
        return

    today = datetime.date.today()
    week_number = 1 if today.isocalendar()[1] % 2 == 1 else 2

    schedule = get_schedule(group_number, week_number)
    if schedule and "next_lesson" in schedule:
        next_lesson = schedule["next_lesson"]
        await message.answer(f"Ближайшее занятие:\n{next_lesson}")
    else:
        await message.answer("Не удалось найти расписание для вашей группы.")


# Обработчик кнопки "Расписание на день"
@router.message(lambda message: message.text == "Расписание на день")
async def day_schedule(message: Message):
    group_number = user_group.get(message.from_user.id)
    if not group_number:
        await message.answer("Сначала введите номер группы с помощью команды /start.")
        return

    today = datetime.date.today().strftime("%Y-%m-%d")
    schedule = get_schedule(group_number, day=today)

    if schedule:
        lessons = schedule.get("lessons", [])
        if lessons:
            schedule_text = "\n".join([f"{lesson['time']} - {lesson['subject']}" for lesson in lessons])
            await message.answer(f"Расписание на сегодня:\n{schedule_text}")
        else:
            await message.answer("Сегодня занятий нет.")
    else:
        await message.answer("Не удалось найти расписание для вашей группы.")


# Обработчик кнопки "Расписание на неделю"
@router.message(lambda message: message.text == "Расписание на неделю")
async def week_schedule(message: Message):
    group_number = user_group.get(message.from_user.id)
    if not group_number:
        await message.answer("Сначала введите номер группы с помощью команды /start.")
        return

    today = datetime.date.today()
    week_number = 1 if today.isocalendar()[1] % 2 == 1 else 2

    schedule = get_schedule(group_number, week_number=week_number)
    if schedule:
        lessons = schedule.get("lessons", [])
        if lessons:
            schedule_text = "\n".join([f"{lesson['day']} {lesson['time']} - {lesson['subject']}" for lesson in lessons])
            await message.answer(f"Расписание на неделю:\n{schedule_text}")
        else:
            await message.answer("На этой неделе занятий нет.")
    else:
        await message.answer("Не удалось найти расписание для вашей группы.")


# Обработчик кнопки "Расписание на завтра"
@router.message(lambda message: message.text == "Расписание на завтра")
async def tomorrow_schedule(message: Message):
    group_number = user_group.get(message.from_user.id)
    if not group_number:
        await message.answer("Сначала введите номер группы с помощью команды /start.")
        return

    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    schedule = get_schedule(group_number, day=tomorrow)

    if schedule:
        lessons = schedule.get("lessons", [])
        if lessons:
            schedule_text = "\n".join([f"{lesson['time']} - {lesson['subject']}" for lesson in lessons])
            await message.answer(f"Расписание на завтра:\n{schedule_text}")
        else:
            await message.answer("Завтра занятий нет.")
    else:
        await message.answer("Не удалось найти расписание для вашей группы.")


# Обработчик команды /cancel
@router.message(Command(commands=["cancel"]))
async def cancel(message: Message):
    await message.answer("Вы отменили операцию. Для начала работы используйте /start.")


# Запуск бота
async def main():
    dp = Dispatcher()
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    asyncio.run(main())
