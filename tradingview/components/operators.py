operators = {
    "logical": {
        "and": lambda x, y: x and y,
        "or": lambda x, y: x or y,
        "not": lambda x: not x
    },
    "comparison": {
        "<": lambda x, y: x < y,
        ">": lambda x, y: x > y,
        "<=": lambda x, y: x <= y,
        ">=": lambda x, y: x >= y,
        "==": lambda x, y: x == y,
        "!=": lambda x, y: x != y
    },
    "conditional": {
        "if": "if_statement",
        "elif": "elif_statement",
        "else": "else_statement"
    },
    "boolean": {
        "True": True,
        "False": False
    }
}

