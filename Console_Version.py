"""Решатель японских кроссвордов
аргументом можно указать файл с кроссвордом
или после запуска выбрать его в открывшемся диалоговом окне"""

import sys
import os
import tkinter
import copy
from tkinter import filedialog
from functools import wraps
from time import time


def elapsed_time(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time()
        result = f(*args, **kwargs)
        end = time()
        print('Затрачено времени: {0:.2f} секунд ({1:.1f} минут)'.format(end - start, (end - start) / 60))
        return result

    return wrapper


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def inner_process_rules(field, rules, length, row=True):
    for offset, line in enumerate(rules):
        line_length = sum(line) + len(line) - 1
        lost_positions = length - line_length
        if max(line) < lost_positions:
            continue
        current_line_offset = 0
        for i in line:
            if i <= lost_positions:
                current_line_offset += i + 1
            else:
                current_line_offset += lost_positions
                found_count = i - lost_positions
                for j in range(found_count):
                    if row:
                        field[offset][current_line_offset + j] = 1
                    else:
                        field[current_line_offset + j][offset] = 1
                current_line_offset += found_count + 1


def inner_block_count(row):
    block_count = 0
    for i in range(len(row)):
        if row[i] == 1:
            if i == 0 or row[i - 1] == 0:
                block_count += 1
    return block_count


def inner_check_full_line(row, rule):
    if sum(row) != sum(rule):
        return False
    if inner_block_count(row) > len(rule):
        return False
    return True


def inner_check_rule(columns, column_rules, end_of_check, begin, end):
    for p in range(begin, end):
        rule, row = column_rules[p], columns[p]
        if len(rule) == 0:
            return False
        if sum(row) > sum(rule):
            return False
        elif sum(row) == sum(rule):
            block_count = 0
            for i in range(len(row)):
                if row[i] == 1:
                    if i == 0 or row[i - 1] == 0:
                        block_count += 1
                if block_count > len(rule):
                    return False
        elif inner_block_count(row) > len(rule):
            still_have = sum(rule) - sum(row)
            try:
                next_one = row.index(1, end_of_check + 1)
            except ValueError:
                return False
            required = next_one - end_of_check - 1
            if required > still_have:
                return False
        try:
            pos = row.index(1) + 1
        except ValueError:
            continue
        rule_pos = 0
        current_length = 1
        for i in range(pos, end_of_check + 1):
            if row[i] == 0:
                if current_length != 0:
                    if rule[rule_pos] != current_length:
                        return False
                if row[i - 1] == 1:
                    rule_pos += 1
                current_length = 0
            else:
                current_length += 1
                if rule_pos >= len(rule) or rule[rule_pos] < current_length:
                    return False
    return True


def inner_recursive_solver(offset, row_offset, rule_offset, field, line_rules, column_rules):
    if len(column_rules) - offset < line_rules[row_offset][rule_offset]:
        return False
    for i in range(offset, len(column_rules)):
        if len(column_rules) - i < line_rules[row_offset][rule_offset]:
            break
        copy_field = copy.deepcopy(field)
        for j in range(i, i + line_rules[row_offset][rule_offset]):
            copy_field[row_offset][j] = 1
        print_statement(copy_field)
        if i + line_rules[row_offset][rule_offset] + 1 >= len(column_rules):
            end_check = i + line_rules[row_offset][rule_offset]
        else:
            end_check = i + line_rules[row_offset][rule_offset] + 1
        if not inner_check_rule(
            list(zip(*copy_field)),
            column_rules,
            row_offset,
            0,
            end_check
        ):
            continue
        if rule_offset + 1 == len(line_rules[row_offset]):
            if not inner_check_full_line(copy_field[row_offset], line_rules[row_offset]):
                continue
            if not inner_check_rule(
                list(zip(*copy_field)),
                column_rules,
                row_offset,
                0,
                len(column_rules)
            ):
                continue
            if row_offset + 1 == len(line_rules):
                return True
            if inner_recursive_solver(0, row_offset + 1, 0, copy_field, line_rules, column_rules):
                return True
        elif inner_recursive_solver(
            i + line_rules[row_offset][rule_offset] + 1,
            row_offset,
            rule_offset + 1,
            copy_field,
            line_rules,
            column_rules
        ):
            return True
    return False


@elapsed_time
def solve(field, line_rules, column_rules):
    still_not_found = sum(map(sum, line_rules)) - sum([sum(i) for i in field])
    if not still_not_found:
        print_statement(field)
        print("Решение найдено!")
        return
    inner_recursive_solver(0, 0, 0, field, line_rules, column_rules)
    print("Решение найдено!")


def print_statement(field):
    """Вывод текущего состояния решения на экран"""
    cls()
    print()
    for row in field:
        print(''.join(map(lambda i: "X" if i != 0 else " ", row)), sep="")


def create_fixed_positions(field, line_rules, column_rules):
    """Обсчет фиксированных позиций, которые на 100% на своем месте
    в самом начале решения кроссворда"""
    inner_process_rules(field, line_rules, len(column_rules))
    inner_process_rules(field, column_rules, len(line_rules), False)


def read_file(cross_file):
    """Получение кроссворда из файла
    в первой строке файла указывается два числа: количество строк(n) и столбцов(m).
    Следом идут n строк с данными строк (сверху-вниз),
    затем m строк с данными столбцов (слева-направо)"""
    with open(cross_file) as openedFile:
        n, m = map(int, openedFile.readline().split())
        line_rules = [tuple(map(int, openedFile.readline().split())) for _ in range(n)]
        column_rules = [tuple(map(int, openedFile.readline().split())) for _ in range(m)]
    return line_rules, column_rules


def get_cross_file():
    """Получение пути файла из аргумента или из диалогового окна"""
    if len(sys.argv) > 1:
        cross_file = sys.argv[1]
    else:
        root = tkinter.Tk()
        root.withdraw()
        cross_file = filedialog.askopenfilename()
    return cross_file


def main():
    cross_file = get_cross_file()
    if not cross_file:
        sys.exit()
    line_rules, column_rules = read_file(cross_file)
    field = [[0 for _ in range(len(column_rules))] for _ in range(len(line_rules))]
    create_fixed_positions(field, line_rules, column_rules)
    solve(field, line_rules, column_rules)


if __name__ == "__main__":
    main()
