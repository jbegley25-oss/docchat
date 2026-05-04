"""Arithmetic calculation tool for the docchat agent."""

SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "Evaluate a mathematical expression and return the result.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A Python math expression to evaluate.",
                }
            },
            "required": ["expression"],
        },
    },
}


def calculate(expression):
    """
    Evaluate a mathematical expression and return the result as a string.

    >>> calculate('2 + 2')
    '4'
    >>> calculate('10 * 5 - 3')
    '47'
    >>> calculate('2 ** 10')
    '1024'
    >>> calculate('9 / 2')
    '4.5'
    >>> calculate('100 // 7')
    '14'
    """
    result = eval(expression)
    return str(result)
