#!/usr/bin/env python3

import random

from lark import Lark
from datetime import datetime

dice_formula_ebnf = r"""
// NON-TERMINALS
expression : subtraction
			| addition
			| division
			| multiplication
			| exponent
			| parenthesis
			| positive
			| negative
			| NUMBER
			| explode_dice
			| fudge_dice
			| basic_dice
addition : expression "+" expression
subtraction : expression "-" expression
multiplication : expression "*" expression
division : expression "/" expression
exponent: expression "^" expression
positive: "+" expression
negative: "-" expression
parenthesis: "(" expression ")"
basic_dice : NUMBER "d" NUMBER
fudge_dice : NUMBER "df"
explode_dice : NUMBER "d" NUMBER "t" NUMBER
// TERMINALS
NUMBER : ("0".."9")+
// LARK IMPORTS
%import common.WS
%ignore WS
"""

_dice_formula_parser = Lark(dice_formula_ebnf, start="expression")


# MAIN
def _main():
    _do_unit_tests()


# PUBLIC API
def get_dice_formula_result(formula_string, seed=None):
    _seed_rng(datetime.now() if not seed else seed)
    parsed = _parse_dice_formula(formula_string)
    result = _resolve_expression(parsed)
    # print('Result was: {}'.format(result))
    return result


# DICE FORMULA FUNCTIONS
def _parse_dice_formula(formula_string):
    return _dice_formula_parser.parse(formula_string)


def _resolve_expression(expression):
    # If this is a terminal, just return the value of the terminal
    if hasattr(expression.children[0], "type"):
        if expression.children[0].type == "NUMBER":
            return {"total": int(expression.children[0]), "individual": []}

    # Resolve the operation child of this expression
    for child in expression.children:
        operation = child.data
        if operation == "basic_dice":
            return _roll_dice(int(child.children[0]), int(child.children[1]))
        elif operation == "fudge_dice":
            return _roll_fudge_dice(int(child.children[0]))
        elif operation == "explode_dice":
            return _roll_explode_dice(
                int(child.children[0]), int(child.children[1]), int(child.children[2])
            )
        elif operation == "parenthesis":
            return _resolve_expression(child.children[0])
        elif operation == "negative":
            val = _resolve_expression(child.children[0])
            return {"total": -1 * val["total"], "individual": val["individual"]}
        elif operation == "positive":
            val = _resolve_expression(child.children[0])
            return {"total": abs(val["total"]), "individual": val["individual"]}
        elif operation == "exponent":
            val1 = _resolve_expression(child.children[0])
            val2 = _resolve_expression(child.children[1])
            return {
                "total": val1["total"] ** val2["total"],
                "individual": val1["individual"] + val2["individual"],
            }
        elif operation == "division":
            val1 = _resolve_expression(child.children[0])
            val2 = _resolve_expression(child.children[1])
            return {
                "total": val1["total"] / val2["total"],
                "individual": val1["individual"] + val2["individual"],
            }
        elif operation == "multiplication":
            val1 = _resolve_expression(child.children[0])
            val2 = _resolve_expression(child.children[1])
            return {
                "total": val1["total"] * val2["total"],
                "individual": val1["individual"] + val2["individual"],
            }
        elif operation == "subtraction":
            val1 = _resolve_expression(child.children[0])
            val2 = _resolve_expression(child.children[1])
            return {
                "total": val1["total"] - val2["total"],
                "individual": val1["individual"] + val2["individual"],
            }
        elif operation == "addition":
            val1 = _resolve_expression(child.children[0])
            val2 = _resolve_expression(child.children[1])
            return {
                "total": val1["total"] + val2["total"],
                "individual": val1["individual"] + val2["individual"],
            }


# DICE ROLLING FUNCTIONS
def _roll_dice(number, sides):
    # print('Rolling {}d{}'.format(number,sides))
    individual = []
    total = 0
    for i in range(number):
        roll = random.randint(1, sides)
        if roll == 20:
            roll = "**20**"
        individual.append(str(roll))
        if roll == "**20**":
            roll = 20
        total += roll
    # print('Rolled {} ({})'.format(total, individual))
    return {"total": total, "individual": individual}


def _roll_fudge_dice(number):
    # print('Rolling {}df'.format(number))
    individual = []
    total = 0
    for i in range(number):
        roll = _fudge_mapping(random.randint(1, 6))
        total += roll["value"]
        if roll["symbol"]:
            individual.append(roll["symbol"])
    # print('Rolled {} ({})'.format(total, individual))
    return {"total": total, "individual": individual}


def _fudge_mapping(number):
    # 1,2 = + , 3,4 = -, 5,6 = 0
    value = 0
    symbol = "."
    if number == 1 or number == 2:
        value = 1
        symbol = "+"
    elif number == 3 or number == 4:
        value = -1
        symbol = "-"
    return {"value": value, "symbol": symbol}


def _roll_explode_dice_explode(sides):
    roll = random.randint(1, sides)
    if roll == sides and sides != 1:
        return roll + _roll_explode_dice_explode(sides)
    else:
        return roll


def _roll_explode_dice(number, sides, target):
    # print('Rolling {}d{}t{}'.format(number, sides, target))
    individual = []
    total = 0
    successes = 0
    for i in range(number):
        roll = _roll_explode_dice_explode(sides)
        rollstr = str(roll)
        if roll > sides:
            rollstr = "**" + str(roll) + "**"
        if roll >= target:
            successes += 1
        individual.append(rollstr)
        total += roll
    # print('Rolled {} ({})'.format(total, individual))
    return {"total": total, "individual": individual, "successes": successes}


def _seed_rng(seed):
    random.seed(seed)


# UNIT TESTING FUNCTIONS
def _do_test_case(formula, expected, seed):
    print("Doing test case {}".format(formula))
    result = get_dice_formula_result(formula, seed)
    if result != expected:
        print(
            "Error on unit test {}: actual value {} is not expected value {}".format(
                formula, result, expected
            )
        )
        return False
    return True


def _do_unit_tests():
    cases = [
        {"formula": "1d20", "expected": {"individual": ["15"], "total": 15}},
        {"formula": "1d20 + 10", "expected": {"individual": ["15"], "total": 25}},
        {
            "formula": "2d6 + 1d20",
            "expected": {"individual": ["4", "4", "1"], "total": 9},
        },
        {"formula": "2*1d8 + 3", "expected": {"individual": ["8"], "total": 19}},
        {"formula": "3df", "expected": {"individual": ["-", "-", "+"], "total": -1}},
        {
            "formula": "10df + 1d10",
            "expected": {
                "individual": ["-", "-", "+", "+", ".", ".", "-", "+", "+", "+", "3"],
                "total": 5,
            },
        },
        {
            "formula": "(1d2*3) + (1d3*4)",
            "expected": {"individual": ["2", "2"], "total": 14},
        },
        {"formula": "-1d8", "expected": {"individual": ["8"], "total": -8}},
        {
            "formula": "3d6t3",
            "expected": {"individual": ["4", "4", "1"], "total": 9, "successes": 2},
        },
        {
            "formula": "8d6t5",
            "expected": {
                "individual": ["4", "4", "1", "1", "**16**", "2", "1", "1"],
                "total": 30,
                "successes": 1,
            },
        },
        {
            "formula": "10d6t20",
            "expected": {
                "individual": ["4", "4", "1", "1", "**16**", "2", "1", "1", "2", "5"],
                "total": 37,
                "successes": 0,
            },
        },
        {
            "formula": "4d2t3",
            "expected": {
                "individual": ["**5**", "1", "**3**", "1"],
                "total": 10,
                "successes": 2,
            },
        },
    ]

    seed = "zangu"  # use a known seed
    for case in cases:
        if not _do_test_case(case["formula"], case["expected"], seed):
            print("Unit tests failed")
            return
    print("Unit tests passed")


# MAIN HOOK
if __name__ == "__main__":
    _main()
