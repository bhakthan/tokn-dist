# Task spec: arithmetic expression evaluator

Implement a module named `expr.py` in the workspace root. It must expose:

- `evaluate(text: str) -> float` evaluates an arithmetic expression string.
- `class ExprError(ValueError)` raised for any malformed or undefined input.

## Grammar

- Numbers: decimal literals such as `3`, `2.5`, `.75`. No scientific notation.
- Binary operators: `+`, `-`, `*`, `/`, `^` (power).
- Unary `+` and `-`.
- Parentheses `(` and `)`.
- Whitespace between tokens is ignored.

## Precedence and associativity

1. Parentheses
2. Unary `+` and `-`
3. `^`, right-associative: `2^3^2` is `2^(3^2)` = 512
4. `*` and `/`, left-associative
5. `+` and `-`, left-associative

Unary minus binds looser than `^`: `-2^2` is `-(2^2)` = -4.

## Errors

Raise `ExprError` for:

- empty or whitespace-only input
- an unknown character such as `a`, `#`, or `%`
- unbalanced parentheses
- a missing operand, such as `3 +` or `* 4`
- division by zero, including `1/0` and `1/(2-2)`

Do not let `ZeroDivisionError`, `SyntaxError`, or `IndexError` escape.

## Results

- `evaluate("1 + 2 * 3") == 7.0`
- `evaluate("(1 + 2) * 3") == 9.0`
- `evaluate("10 / 4") == 2.5`
- `evaluate("-2^2") == -4.0`
- `evaluate("2^3^2") == 512.0`

## Out of scope

No variables, functions, or `%` operator. No I/O. Standard library only.
