from sympy import symbols, Eq, solve, I, simplify, expand, diff, integrate, log, sin, cos, sqrt, pi, E, latex
from sympy.parsing.sympy_parser import parse_expr
import re
import matplotlib.pyplot as plt
from io import BytesIO
from sympy import pretty
def insert_multiplication_signs(expr: str) -> str:
    expr = re.sub(r'(\d)([a-zA-Z\(])', r'\1*\2', expr)
    expr = re.sub(r'(\))(\d)', r'\1*\2', expr)
    return expr

def format_solution(solutions):
    if not solutions:
        return "Решений нет."
    
    formatted = []
    for i, sol in enumerate(solutions, start=1):
        simplified = simplify(sol)
        s = str(simplified)
        s = s.replace("I", "i").replace("*", "")  # без умножения и латинская i
        s = s.replace("sqrt", "√")
        formatted.append(f"x{i} = {s}")

    if any(I in sol.free_symbols for sol in solutions):
        return "Комплексные корни:\n" + "\n".join(formatted)
    return "Решение:\n" + "\n".join(formatted)

def solve_equation(expr: str):
    x = symbols('x')
    expr = expr.replace("^", "**")
    expr = insert_multiplication_signs(expr)
    try:
        if "=" in expr:
            left, right = expr.split("=")
            left_expr = parse_expr(left.strip())
            right_expr = parse_expr(right.strip())
            equation = Eq(left_expr, right_expr)
            solutions = solve(equation, x)
            return format_solution(solutions)
        elif "x" in expr:
            parsed = parse_expr(expr)
            equation = Eq(parsed, 0)
            solutions = solve(equation, x)
            return format_solution(solutions)
        else:
            result = eval(expr)
            return f"Ответ: {result}"
    except ZeroDivisionError:
        return "Ошибка: деление на ноль недопустимо."
    except Exception as e:
        return f"Ошибка: {e}"

def compute_operation(operation: str, expression: str):
    x = symbols('x')
    expression = expression.replace("^", "**")
    expression = insert_multiplication_signs(expression)
    try:
        if operation == "log":
            parts = expression.strip().split()
            if len(parts) == 2:
                try:
                    base, arg = map(parse_expr, parts)
                    # Символьная форма
                    symbolic = f"log({arg})/log({base})"
                    # Числовое значение
                    numeric = log(float(arg), float(base))
                    return f"Логарифм по основанию {base}: {symbolic}\nОтвет: {numeric:.5f}"
                except Exception:
                    return "Ошибка: для логарифма укажите два числа или выражения через пробел, например: 2 8"
            elif len(parts) == 1:
                try:
                    arg = parse_expr(parts[0])
                    symbolic = f"log({arg})"
                    numeric = log(float(arg))
                    return f"Натуральный логарифм: {symbolic}\nОтвет: {numeric:.5f}"
                except Exception:
                    return "Ошибка: для натурального логарифма просто введите число, например: 10"
            else:
                return "Ошибка: введите через пробел основание и аргумент, например: 2 8"

        parsed = parse_expr(expression)
        if operation == "integrate":
            return f"Интеграл: {str(integrate(parsed, x)).replace('**', '^')}"
        elif operation == "diff":
            return f"Производная: {str(diff(parsed, x)).replace('**', '^')}"
        elif operation == "expand":
            return f"Раскрыто: {str(expand(parsed)).replace('**', '^')}"
        elif operation == "simplify":
            return f"Упрощено: {str(simplify(parsed)).replace('**', '^')}"
        elif operation == "solve":
            return solve_equation(expression)
        else:
            return "Неизвестная операция."
    except Exception as e:
        return f"Ошибка при вычислении: {e}"


