import datetime
import requests
import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from bs4 import BeautifulSoup
from config import TOKEN

# URL сайта для парсинга расписания
BASE_URL = "https://digital.etu.ru/schedule/"

# Инициализация бота
bot = Bot(token=TOKEN)
router = Router()

# Сохранение номера группы и курса пользователя
user_data = {}


# Функция для парсинга расписания
def fetch_schedule(course, faculty):
    """
    Парсит расписание с сайта digital.etu.ru
    :param course: Курс (1, 2, 3 и т.д.)
    :param faculty: Факультет
    :return: JSON с расписанием
    """
    params = {"course": course, "schedule": faculty}
    response = requests.get(BASE_URL, params=params)

    if response.status_code != 200:
        return {"error": "Не удалось подключиться к сайту"}

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", {"class": "table"})  # Таблица с расписанием

    if not table:
        return {"error": "Не удалось найти расписание на странице"}

    schedule_data = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) >= 4:
            schedule_data.append({
                "time": cells[0].text.strip(),
                "subject": cells[1].text.strip(),
                "teacher": cells[2].text.strip(),
                "room": cells[3].text.strip(),
            })

    return {"schedule": schedule_data}


# Команда /start
@router.message(Command(commands=["start"]))
async def start(message: Message):
    user_data[message.from_user.id] = {"course": None, "faculty": None}
    await message.answer(
        "Привет! Я бот для получения расписания ЛЭТИ.\n"
        "Введите номер вашего курса (1, 2, 3 и т.д.):"
    )


# Ввод номера курса
@router.message(lambda message: user_data.get(message.from_user.id, {}).get("course") is None)
async def handle_course_number(message: Message):
    try:
        course = int(message.text.strip())
        if course not in [1, 2, 3, 4]:  # Допустимые курсы
            raise ValueError
        user_data[message.from_user.id]["course"] = course
        await message.answer(
            "Введите название факультета (например, ИТИ, РТФ, ФЭЭ):"
        )
    except ValueError:
        await message.answer("Пожалуйста, введите корректный номер курса (1, 2, 3 или 4).")


# Ввод факультета
@router.message(lambda message: user_data.get(message.from_user.id, {}).get("faculty") is None)
async def handle_faculty_name(message: Message):
    faculty = message.text.strip().upper()  # Приводим название к верхнему регистру
    user_data[message.from_user.id]["faculty"] = faculty

    # Создаем клавиатуру
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Следующая пара")],
            [KeyboardButton(text="Расписание на день")],
            [KeyboardButton(text="Расписание на неделю")],
            [KeyboardButton(text="Расписание на завтра")],
        ],
        resize_keyboard=True
    )

    await message.answer(
        f"Курс и факультет сохранены: {user_data[message.from_user.id]['course']} курс, {faculty}.\n"
        "Выберите действие:",
        reply_markup=keyboard
    )


# Обработчик кнопки "Следующая пара"
@router.message(lambda message: message.text == "Следующая пара")
async def near_lesson(message: Message):
    user = user_data.get(message.from_user.id)
    if not user or not user.get("course") or not user.get("faculty"):
        await message.answer("Сначала введите данные с помощью команды /start.")
        return

    schedule = fetch_schedule(user["course"], user["faculty"])
    if "error" in schedule:
        await message.answer(schedule["error"])
        return

    lessons = schedule.get("schedule", [])
    if lessons:
        next_lesson = lessons[0]  # Берем первое занятие как ближайшее
        await message.answer(
            f"Ближайшее занятие:\n"
            f"{next_lesson['time']} - {next_lesson['subject']}\n"
            f"Преподаватель: {next_lesson['teacher']}\n"
            f"Аудитория: {next_lesson['room']}"
        )
    else:
        await message.answer("На сегодня занятий больше нет.")


# Обработчик кнопки "Расписание на день"
@router.message(lambda message: message.text == "Расписание на день")
async def day_schedule(message: Message):
    user = user_data.get(message.from_user.id)
    if not user or not user.get("course") or not user.get("faculty"):
        await message.answer("Сначала введите данные с помощью команды /start.")
        return

    schedule = fetch_schedule(user["course"], user["faculty"])
    if "error" in schedule:
        await message.answer(schedule["error"])
        return

    lessons = schedule.get("schedule", [])
    if lessons:
        schedule_text = "\n".join(
            [f"{lesson['time']} - {lesson['subject']} ({lesson['room']})" for lesson in lessons]
        )
        await message.answer(f"Расписание на сегодня:\n{schedule_text}")
    else:
        await message.answer("Сегодня занятий нет.")


# Обработчик кнопки "Расписание на неделю"
@router.message(lambda message: message.text == "Расписание на неделю")
async def week_schedule(message: Message):
    user = user_data.get(message.from_user.id)
    if not user or not user.get("course") or not user.get("faculty"):
        await message.answer("Сначала введите данные с помощью команды /start.")
        return

    schedule = fetch_schedule(user["course"], user["faculty"])
    if "error" in schedule:
        await message.answer(schedule["error"])
        return

    lessons = schedule.get("schedule", [])
    if lessons:
        schedule_text = "\n".join(
            [f"{lesson['time']} - {lesson['subject']} ({lesson['room']})" for lesson in lessons]
        )
        await message.answer(f"Расписание на неделю:\n{schedule_text}")
    else:
        await message.answer("На этой неделе занятий нет.")


# Обработчик кнопки "Расписание на завтра"
@router.message(lambda message: message.text == "Расписание на завтра")
async def tomorrow_schedule(message: Message):
    await message.answer("Эта функция пока в разработке.")


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
