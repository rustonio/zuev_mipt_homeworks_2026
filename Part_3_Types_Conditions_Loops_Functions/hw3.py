#!/usr/bin/env python

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
OP_SUCCESS_MSG = "Added"

DATE_PARTS = 3
MONTHS_NUM = 12
INCOME_ARGS = 3
COST_ARGS = 4
STATS_ARGS = 2
DAY_STRING_LEN = 2
MONTH_STRING_LEN = 2
YEAR_STRING_LEN = 4

Transaction = tuple[float, int, int, int, str]
IncomeList = list[Transaction]
ExpenseMap = dict[str, list[Transaction]]
ParsedDate = tuple[int, int, int]


def is_leap_year(year: int) -> bool:
    first_condition = (year % 4 == 0) and (year % 100 != 0)
    second_condition = year % 400 == 0
    return first_condition or second_condition


def get_days_in_month() -> list[int]:
    return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def validate_date_components(parts: list[str], day: int, month: int, year: int) -> bool:
    day_len_condition = len(parts[0]) == DAY_STRING_LEN
    month_len_condition = len(parts[1]) == MONTH_STRING_LEN
    year_len_condition = len(parts[2]) == YEAR_STRING_LEN
    if not (day_len_condition and month_len_condition and year_len_condition):
        return False
    if month < 1 or month > MONTHS_NUM:
        return False
    days_in_month = [0, *get_days_in_month()]
    if is_leap_year(year):
        days_in_month[2] = 29
    return not (day < 1 or day > days_in_month[month])


def parse_date(maybe_dt: str) -> ParsedDate | None:
    parts = maybe_dt.split("-")
    if len(parts) != DATE_PARTS:
        return None
    if not all(part.isdigit() for part in parts):
        return None
    day = int(parts[0])
    month = int(parts[1])
    year = int(parts[2])
    if not validate_date_components(parts, day, month, year):
        return None
    return (day, month, year)


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


def validate_category(category: str) -> bool:
    if not category:
        return False
    return not ("." in category or "," in category)


def make_transaction(amount: float, date_tuple: ParsedDate, category: str = "") -> Transaction:
    return (amount, date_tuple[0], date_tuple[1], date_tuple[2], category)


def is_date_on_or_before(trans: Transaction, target: ParsedDate) -> bool:
    trans_date = (trans[3], trans[2], trans[1])
    return trans_date <= target


def is_same_month(trans: Transaction, target: ParsedDate) -> bool:
    first_condition = trans[2] == target[1]
    second_condition = trans[3] == target[2]
    return first_condition and second_condition


def handle_income(incomes: IncomeList, args: list[str]) -> None:
    if len(args) != INCOME_ARGS:
        print(UNKNOWN_COMMAND_MSG)
        return
    amount_str = args[1]
    date_str = args[2]
    amount = parse_amount(amount_str)
    if amount is None:
        print(UNKNOWN_COMMAND_MSG)
        return
    if amount <= 0:
        print(NONPOSITIVE_VALUE_MSG)
        return
    date_tuple = parse_date(date_str)
    if date_tuple is None:
        print(INCORRECT_DATE_MSG)
        return
    incomes.append(make_transaction(amount, date_tuple))
    print(OP_SUCCESS_MSG)


def add_expense(expenses: ExpenseMap, category: str, transaction: Transaction) -> None:
    if category not in expenses:
        expenses[category] = []
    expenses[category].append(transaction)


def handle_cost(expenses: ExpenseMap, args: list[str]) -> None:
    if len(args) != COST_ARGS:
        print(UNKNOWN_COMMAND_MSG)
        return
    category = args[1]
    if not validate_category(category):
        print(UNKNOWN_COMMAND_MSG)
        return
    amount = parse_amount(args[2])
    if amount is None:
        print(UNKNOWN_COMMAND_MSG)
        return
    if amount <= 0:
        print(NONPOSITIVE_VALUE_MSG)
        return
    date_tuple = parse_date(args[3])
    if date_tuple is None:
        print(INCORRECT_DATE_MSG)
        return
    add_expense(expenses, category, make_transaction(amount, date_tuple, category))
    print(OP_SUCCESS_MSG)


def format_money_detail(val: float) -> str:
    if val.is_integer():
        return str(int(val))
    return str(val)


def sum_income(incomes: IncomeList, target: ParsedDate, target_date: ParsedDate) -> tuple[float, float]:
    total_capital_income = float(0)
    monthly_income = float(0)
    for trans in incomes:
        if is_date_on_or_before(trans, target_date):
            total_capital_income += trans[0]
            if is_same_month(trans, target):
                monthly_income += trans[0]
    return total_capital_income, monthly_income


def sum_expenses(
    expenses: ExpenseMap, target: ParsedDate, target_date: ParsedDate
) -> tuple[float, float, dict[str, float]]:
    totals = [float(0), float(0)]
    category_expenses: dict[str, float] = {}
    for category, transactions in expenses.items():
        for trans in transactions:
            if is_date_on_or_before(trans, target_date):
                totals[0] += trans[0]
                if is_same_month(trans, target):
                    totals[1] += trans[0]
                    category_expenses[category] = category_expenses.get(category, 0) + trans[0]
    return totals[0], totals[1], category_expenses


def show_monthly_balance(monthly_income: float, monthly_expense: float) -> None:
    monthly_balance = monthly_income - monthly_expense
    if monthly_balance >= 0:
        print(f"Profit for this month was {monthly_balance:.2f} rubles")
    else:
        print(f"Loss for this month was {abs(monthly_balance):.2f} rubles")


def show_expense_breakdown(category_expenses: dict[str, float]) -> None:
    print("Details (category: amount):")
    sorted_categories = sorted(category_expenses.keys())
    for index, category in enumerate(sorted_categories, 1):
        val = category_expenses[category]
        print(f"{index}. {category}: {format_money_detail(val)}")


def build_date_targets(date_tuple: ParsedDate) -> tuple[ParsedDate, ParsedDate]:
    req_day, req_month, req_year = date_tuple
    return (req_day, req_month, req_year), (req_year, req_month, req_day)


def display_statistics(
    date_str: str,
    incomes: IncomeList,
    expenses: ExpenseMap,
    targets: tuple[ParsedDate, ParsedDate],
) -> None:
    target, target_date = targets
    income_totals = sum_income(incomes, target, target_date)
    expense_totals = sum_expenses(expenses, target, target_date)
    total_capital = income_totals[0] - expense_totals[0]

    print(f"Your statistics as of {date_str}:")
    print(f"Total capital: {total_capital:.2f} rubles")
    show_monthly_balance(income_totals[1], expense_totals[1])
    print(f"Income: {income_totals[1]:.2f} rubles")
    print(f"Expenses: {expense_totals[1]:.2f} rubles")
    if expense_totals[2]:
        show_expense_breakdown(expense_totals[2])


def handle_stats(incomes: IncomeList, expenses: ExpenseMap, args: list[str]) -> None:
    if len(args) != STATS_ARGS:
        print(UNKNOWN_COMMAND_MSG)
        return
    date_tuple = parse_date(args[1])
    if date_tuple is None:
        print(INCORRECT_DATE_MSG)
        return
    targets = build_date_targets(date_tuple)
    display_statistics(args[1], incomes, expenses, targets)


def process_command(incomes: IncomeList, expenses: ExpenseMap) -> bool:
    line = input()
    parts = line.split()
    command = parts[0]
    if command == "income":
        handle_income(incomes, parts)
    elif command == "cost":
        handle_cost(expenses, parts)
    elif command == "stats":
        handle_stats(incomes, expenses, parts)
    else:
        print(UNKNOWN_COMMAND_MSG)
        return False
    return True


def main() -> None:
    incomes: IncomeList = []
    expenses: ExpenseMap = {}
    while True:
        if not process_command(incomes, expenses):
            break


if __name__ == "__main__":
    main()
