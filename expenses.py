""" Работа с расходами — их добавление, удаление, статистики"""
import datetime
import re
from typing import List, NamedTuple, Optional

import pytz

import db
import exceptions
from categories import Categories
from categories import Users


class Message(NamedTuple):
    """Структура распаршенного сообщения о новом расходе"""
    amount: int
    category_text: str


class Expense(NamedTuple):
    """Структура добавленного в БД нового расхода"""
    id: Optional[int]
    amount: int
    category_name: str
    user_userid: int


class User(NamedTuple):
    """Структура добавленного в БД нового расхода"""
    user_id: int
    name: str
    budjet: int


def add_user(user_id: int, name: str, budjet: int) -> User:
    """Добавляет новое сообщение.
    Принимает на вход текст сообщения, пришедшего в бот."""
    inserted_row_id = db.insert("user", {
        "user_id": user_id,
        "name": name,
        "budjet": budjet,
    })
    return User(user_id=user_id,
                name=name,
                budjet=budjet)


def add_expense(raw_message: str, user_id: int) -> Expense:
    """Добавляет новое сообщение.
    Принимает на вход текст сообщения, пришедшего в бот."""
    parsed_message = _parse_message(raw_message)
    category = Categories().get_category(
        parsed_message.category_text)
    inserted_row_id = db.insert("expense", {
        "amount": parsed_message.amount,
        "created": _get_now_formatted(),
        "category_codename": category.codename,
        "raw_text": raw_message,
        "user_userid": user_id
    })
    return Expense(id=None,
                   amount=parsed_message.amount,
                   category_name=category.name,
                   user_userid=user_id)


def get_today_statistics(a: int) -> str:
    """Возвращает строкой статистику расходов за сегодня"""
    cursor = db.get_cursor()
    cursor.execute("select sum(amount) "
                   "from expense where "
                   "date(created)=date('now', 'localtime') "
                   "and user_userid = {}".format(a))
    result = cursor.fetchone()
    if not result[0]:
        return "Сегодня ещё нет расходов"
    all_today_expenses = result[0]
    cursor.execute("select sum(amount) "
                   "from expense where "
                   "date(created)=date('now', 'localtime') "
                   "and category_codename in (select codename "
                   "from category where is_base_expense=true) "
                   "and user_userid={}".format(a))
    result = cursor.fetchone()
    base_today_expenses = result[0] if result[0] else 0
    return (f"Расходы сегодня:\n"
            f"{base_today_expenses} грн. из {_get_budget_limit(a)} грн.\n\n"
            f"За текущий месяц: /month")


def get_month_statistics(a: int) -> str:
    """Возвращает строкой статистику расходов за текущий месяц"""

    now = _get_now_datetime()
    first_day_of_month = f'{now.year:04d}-{now.month:02d}-01'
    cursor = db.get_cursor()
    cursor.execute(f"select sum(amount) "
                   f"from expense where date(created) >= '{first_day_of_month}' "
                   "and user_userid={}".format(a))
    result = cursor.fetchone()
    if not result[0]:
        return "В этом месяце ещё нет расходов"
    all_today_expenses = result[0]
    cursor.execute(f"select sum(amount) "
                   f"from expense where date(created) >= '{first_day_of_month}' "
                   f"and category_codename in (select codename "
                   f"from category where is_base_expense=true) "
                   "and user_userid={}".format(a))
    result = cursor.fetchone()
    base_today_expenses = result[0] if result[0] else 0
    return (f"Расходы в текущем месяце:\n"
           
            f"{base_today_expenses} грн. из "
            f"{now.day * _get_budget_limit(a)} грн.")


def last(a: int) -> List[Expense]:
    """Возвращает последние несколько расходов"""
    cursor = db.get_cursor()
    cursor.execute(
        "select e.id, e.amount, c.name, e.user_userid "
        "from expense e left join category c "
        "on c.codename=e.category_codename "
        "where e.user_userid={} LIMIT 5".format(a)
    )
    rows = cursor.fetchall()
    last_expenses = [Expense(id=row[0], amount=row[1], category_name=row[2], user_userid=row[3]) for row in rows]
    return last_expenses


def delete_expense(row_id: int) -> None:
    """Удаляет сообщение по его идентификатору"""
    db.delete("expense", row_id)


def get_user(raw_message: int) -> str:
    """Возвращает строкой статистику расходов за сегодня"""
    cursor = db.get_cursor()
    cursor.execute("select user_id "
                   "from user where user_id={}".format(raw_message))
    result = cursor.fetchone()
    if result is None:
        return "a"

        return "b"


def _parse_message(raw_message: str) -> Message:
    """Парсит текст пришедшего сообщения о новом расходе."""
    regexp_result = re.match(r"([\d ]+) (.*)", raw_message)
    if not regexp_result or not regexp_result.group(0) \
            or not regexp_result.group(1) or not regexp_result.group(2):
        raise exceptions.NotCorrectMessage(
            "Не могу понять сообщение.")

    amount = regexp_result.group(1).replace(" ", "")
    category_text = regexp_result.group(2).strip().lower()
    return Message(amount=amount, category_text=category_text)


def _get_now_formatted() -> str:
    """Возвращает сегодняшнюю дату строкой"""
    return _get_now_datetime().strftime("%Y-%m-%d %H:%M:%S")


def _get_now_datetime() -> datetime.datetime:
    """Возвращает сегодняшний datetime с учётом времненной зоны Мск."""
    tz = pytz.timezone("Europe/Moscow")
    now = datetime.datetime.now(tz)
    return now


def _get_budget_limit(raw_message: int) -> int:
    cursor = db.get_cursor()
    cursor.execute("select budjet "
                   "from user where user_id={}".format(raw_message))
    result = cursor.fetchone()
    return result[0]
