#!/usr/bin/env python

from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

DATE_PARTS = 3
INCOME_PARTS = 3
COST_CATEGORY_PARTS = 2
STATS_PARTS = 2
COST_PARTS = 4
MONTH_MAX = 12
CATEGORY_PARTS = 2
FEBRUARY = 2
FEB_LEAP_DAYS = 29
DAY_STRING_LEN = 2
MONTH_STRING_LEN = 2
YEAR_STRING_LEN = 4

KEY_TYPE = "type"
KEY_AMOUNT = "amount"
KEY_DATE = "date"
KEY_CATEGORY = "category"

DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

Date = tuple[int, int, int]
TransStorage = list[dict[str, Any]]

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}


financial_transactions_storage: TransStorage = []


def is_leap_year(year: int) -> bool:
    if year % 4 != 0:
        return False
    if year % 100 == 0:
        return year % 400 == 0
    return True


def get_days_in_month() -> list[int]:
    return DAYS_IN_MONTH[:]


def validate_date_components(parts: list[str], day: int, month: int, year: int) -> bool:
    day_len_condition = len(parts[0]) == DAY_STRING_LEN
    month_len_condition = len(parts[1]) == MONTH_STRING_LEN
    year_len_condition = len(parts[2]) == YEAR_STRING_LEN
    if not (day_len_condition and month_len_condition and year_len_condition):
        return False
    if month < 1 or month > MONTH_MAX:
        return False
    days_in_month = [0, *get_days_in_month()]
    if is_leap_year(year):
        days_in_month[FEBRUARY] = FEB_LEAP_DAYS
    return not (day < 1 or day > days_in_month[month])


def extract_date(maybe_dt: str) -> Date | None:
    parts = maybe_dt.split("-")
    if len(parts) != DATE_PARTS:
        return None
    if not all(p.isdigit() for p in parts):
        return None
    d, m, y = map(int, parts)
    if not validate_date_components(parts, d, m, y):
        return None
    return (d, m, y)


def is_valid_category(cat: str) -> bool:
    parts = cat.split("::")
    if len(parts) != CATEGORY_PARTS:
        return False
    common, target = parts
    return common in EXPENSE_CATEGORIES and target in EXPENSE_CATEGORIES[common]


def parse_amount(amount_str: str) -> float | None:
    if not amount_str:
        return None
    if amount_str.count(".") + amount_str.count(",") > 1:
        return None
    if "." in amount_str and "," in amount_str:
        return None
    clean_str = amount_str.replace(",", ".")
    check_str = clean_str.removeprefix("-")
    if not check_str or not check_str.replace(".", "").isdigit():
        return None
    return float(clean_str)


def income_handler(amount: float, income_date: str) -> str:
    financial_transactions_storage.append({})
    if amount <= 0:
        return NONPOSITIVE_VALUE_MSG
    date_tup = extract_date(income_date)
    if date_tup is None:
        return INCORRECT_DATE_MSG
    financial_transactions_storage[-1] = {
        KEY_TYPE: "income",
        KEY_AMOUNT: amount,
        KEY_DATE: date_tup,
    }
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    financial_transactions_storage.append({})
    if amount <= 0:
        return NONPOSITIVE_VALUE_MSG
    date_tup = extract_date(income_date)
    if date_tup is None:
        return INCORRECT_DATE_MSG
    if not is_valid_category(category_name):
        return NOT_EXISTS_CATEGORY
    financial_transactions_storage[-1] = {
        KEY_TYPE: "cost",
        KEY_AMOUNT: amount,
        KEY_DATE: date_tup,
        KEY_CATEGORY: category_name,
    }
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    lines: list[str] = []
    for common, targets in EXPENSE_CATEGORIES.items():
        lines.extend(f"{common}::{t}" for t in targets)
    return "\n".join(lines)


def compare_dates(t: dict[str, Any], target: Date) -> bool:
    t_year = int(t[KEY_DATE][2])
    t_month = int(t[KEY_DATE][1])
    t_day = int(t[KEY_DATE][0])
    return (t_year, t_month, t_day) <= (target[2], target[1], target[0])


def is_same_month(t: dict[str, Any], year: int, month: int) -> bool:
    t_year = int(t[KEY_DATE][2])
    t_month = int(t[KEY_DATE][1])
    return t_year == year and t_month == month


def sum_income(trans: TransStorage, y: int, m: int) -> tuple[float, float]:
    total = monthly = 0.0
    for t in trans:
        if t[KEY_TYPE] == "income":
            total += t[KEY_AMOUNT]
            if is_same_month(t, y, m):
                monthly += t[KEY_AMOUNT]
    return total, monthly


def sum_expenses(trans: TransStorage, y: int, m: int) -> tuple[float, float, dict[str, float]]:
    total = monthly = 0.0
    cat_exp: dict[str, float] = {}
    for t in trans:
        if t[KEY_TYPE] == "cost":
            total += t[KEY_AMOUNT]
            if is_same_month(t, y, m):
                monthly += t[KEY_AMOUNT]
                cat = t[KEY_CATEGORY]
                cat_exp[cat] = cat_exp.get(cat, 0.0) + t[KEY_AMOUNT]
    return total, monthly, cat_exp


def show_monthly_balance(inc: float, exp: float) -> str:
    profit = inc - exp
    word = "profit" if profit >= 0 else "loss"
    return f"This month, the {word} amounted to {abs(profit):.2f} rubles."


def show_expense_breakdown(cat_exp: dict[str, float]) -> list[str]:
    lines: list[str] = []
    if cat_exp:
        for i, (cat, amt) in enumerate(sorted(cat_exp.items()), 1):
            lines.append(f"{i}. {cat}: {amt:.2f}")
    return lines


def display_statistics(date_str: str, capital: tuple[float, float, float], cat_exp: dict[str, float]) -> str:
    lines = [
        f"Your statistics as of {date_str}:",
        f"Total capital: {capital[0]:.2f} rubles",
        show_monthly_balance(capital[1], capital[2]),
        f"Income: {capital[1]:.2f} rubles",
        f"Expenses: {capital[2]:.2f} rubles",
        "Details (category: amount):",
    ]
    lines.extend(show_expense_breakdown(cat_exp))
    return "\n".join(lines)


def stats_handler(report_date: str) -> str:
    date_tuple = extract_date(report_date)
    if date_tuple is None:
        return INCORRECT_DATE_MSG
    relevant = [t for t in financial_transactions_storage if t and compare_dates(t, date_tuple)]
    year = date_tuple[2]
    month = date_tuple[1]
    total_inc, monthly_inc = sum_income(relevant, year, month)
    total_exp, monthly_exp, cat_exp = sum_expenses(relevant, year, month)
    total_capital = total_inc - total_exp
    return display_statistics(report_date, (total_capital, monthly_inc, monthly_exp), cat_exp)


def handle_income_command(parts: list[str]) -> None:
    if len(parts) != INCOME_PARTS:
        print(UNKNOWN_COMMAND_MSG)
        return
    amount_str = parts[1]
    date_str = parts[2]
    amount = parse_amount(amount_str)
    if amount is None:
        print(UNKNOWN_COMMAND_MSG)
        return
    result = income_handler(amount, date_str)
    print(result)


def handle_cost_command(parts: list[str]) -> None:
    if len(parts) == COST_CATEGORY_PARTS and parts[1] == "categories":
        print(cost_categories_handler())
        return
    if len(parts) != COST_PARTS:
        print(UNKNOWN_COMMAND_MSG)
        return
    category = parts[1]
    amount_str = parts[2]
    date_str = parts[3]
    amount = parse_amount(amount_str)
    if amount is None:
        print(UNKNOWN_COMMAND_MSG)
        return
    result = cost_handler(category, amount, date_str)
    print(result)


def handle_stats_command(parts: list[str]) -> None:
    if len(parts) != STATS_PARTS:
        print(UNKNOWN_COMMAND_MSG)
        return
    date_str = parts[1]
    result = stats_handler(date_str)
    print(result)


def process_command(parts: list[str]) -> None:
    command = parts[0]
    if command == "income":
        handle_income_command(parts)
    elif command == "cost":
        handle_cost_command(parts)
    elif command == "stats":
        handle_stats_command(parts)
    else:
        print(UNKNOWN_COMMAND_MSG)


def main() -> None:
    while True:
        line = input()
        parts = line.split()
        if not parts:
            print(UNKNOWN_COMMAND_MSG)
            continue
        process_command(parts)


if __name__ == "__main__":
    main()
