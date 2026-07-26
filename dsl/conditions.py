"""
Condition Expression Parser

Parses DSL signal conditions into an AST for Pine Script generation
or local evaluation.

Grammar (simple recursive descent):

  expr        → term (("AND" | "OR") term)*
  term        → NOT term | comparison
  comparison  → value ((">" | "<" | ">=" | "<=" | "==" | "!=") value)?
  value       → IDENTIFIER | NUMBER | "(" expr ")"

Identifiers can be:
  - indicator/compound ids (ema_fast, alignment)
  - price references (close, open, high, low, volume)
  - pattern names (hammer, doji)
  - session names (session_ny, session_london)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Union, Set
import re


# ── AST Nodes ───────────────────────────────────────────────────────────────

@dataclass
class Identifier:
    name: str

@dataclass
class Number:
    value: float

@dataclass
class Compare:
    op: str           # > < >= <= == !=
    left: Node
    right: Node

@dataclass
class LogicOp:
    op: str           # AND OR
    left: Node
    right: Node

@dataclass
class Not:
    operand: Node

Node = Union[Identifier, Number, Compare, LogicOp, Not]


# ── Lexer ───────────────────────────────────────────────────────────────────

TOKEN_SPEC = [
    ("AND",      r"\bAND\b"),
    ("OR",       r"\bOR\b"),
    ("NOT",      r"\bNOT\b"),
    ("OP",       r">=|<=|!=|==|>|<"),
    ("NUMBER",   r"-?\d+\.?\d*"),
    ("LPAREN",   r"\("),
    ("RPAREN",   r"\)"),
    ("IDENT",    r"[a-zA-Z_][a-zA-Z0-9_]*"),
    ("SKIP",     r"[ \t]+"),
    ("MISMATCH", r"."),
]


@dataclass
class Token:
    kind: str
    value: str


def tokenize(text: str) -> List[Token]:
    tokens = []
    pos = 0
    while pos < len(text):
        match = None
        for kind, pattern in TOKEN_SPEC:
            m = re.match(pattern, text[pos:])
            if m:
                match = m
                if kind != "SKIP":
                    tokens.append(Token(kind=kind, value=m.group(0)))
                pos += m.end()
                break
        if not match:
            raise SyntaxError(f"Unexpected character at position {pos}: {text[pos]!r}")
    return tokens


# ── Parser ──────────────────────────────────────────────────────────────────

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Optional[Token]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, kind: str) -> Token:
        tok = self.peek()
        if tok is None or tok.kind != kind:
            got = tok.value if tok else "EOF"
            raise SyntaxError(f"Expected {kind}, got {got!r}")
        self.pos += 1
        return tok

    def parse(self) -> Node:
        return self._expr()

    # expr → term (("AND" | "OR") term)*
    def _expr(self) -> Node:
        left = self._term()
        while self.peek() and self.peek().kind in ("AND", "OR"):
            op = self.consume(self.peek().kind).value
            right = self._term()
            left = LogicOp(op=op, left=left, right=right)
        return left

    # term → NOT term | comparison
    def _term(self) -> Node:
        if self.peek() and self.peek().kind == "NOT":
            self.consume("NOT")
            operand = self._term()
            return Not(operand=operand)
        return self._comparison()

    # comparison → value ((">" | "<" | ">=" | "<=" | "==" | "!=") value)?
    def _comparison(self) -> Node:
        left = self._value()
        if self.peek() and self.peek().kind == "OP":
            op = self.consume("OP").value
            right = self._value()
            return Compare(op=op, left=left, right=right)
        return left

    # value → IDENTIFIER | NUMBER | "(" expr ")"
    def _value(self) -> Node:
        tok = self.peek()
        if tok is None:
            raise SyntaxError("Unexpected end of expression")
        if tok.kind == "NUMBER":
            self.consume("NUMBER")
            return Number(value=float(tok.value))
        if tok.kind == "IDENT":
            self.consume("IDENT")
            return Identifier(name=tok.value)
        if tok.kind == "LPAREN":
            self.consume("LPAREN")
            node = self._expr()
            self.consume("RPAREN")
            return node
        raise SyntaxError(f"Unexpected token {tok.kind}: {tok.value!r}")


# ── Public API ──────────────────────────────────────────────────────────────

def parse_condition(expr: str) -> Node:
    """Parse a condition expression string into an AST."""
    tokens = tokenize(expr)
    parser = Parser(tokens)
    ast = parser.parse()
    if parser.pos < len(tokens):
        raise SyntaxError(
            f"Unexpected token after expression: {tokens[parser.pos].value!r}"
        )
    return ast


# ── Visitors ────────────────────────────────────────────────────────────────

def collect_identifiers(node: Node) -> Set[str]:
    """Collect all identifier names referenced in a condition AST."""
    refs = set()
    def walk(n: Node):
        if isinstance(n, Identifier):
            refs.add(n.name)
        elif isinstance(n, Compare):
            walk(n.left)
            walk(n.right)
        elif isinstance(n, LogicOp):
            walk(n.left)
            walk(n.right)
        elif isinstance(n, Not):
            walk(n.operand)
    walk(node)
    return refs


def to_pine_condition(node: Node) -> str:
    """Render a condition AST as a Pine Script v5 boolean expression."""
    def render(n: Node) -> str:
        if isinstance(n, Identifier):
            return n.name
        elif isinstance(n, Number):
            return str(n.value)
        elif isinstance(n, Compare):
            # Patterns (hammer, doji, etc.) are already boolean — strip redundant > 0, != 0 comparisons
            from dsl.indicators import PATTERN_MAP
            if (isinstance(n.left, Identifier) and n.left.name in PATTERN_MAP
                    and isinstance(n.right, Number) and n.right.value == 0):
                return render(n.left)
            return f"{render(n.left)} {n.op} {render(n.right)}"
        elif isinstance(n, LogicOp):
            op_lower = n.op.lower()
            return f"({render(n.left)} {op_lower} {render(n.right)})"
        elif isinstance(n, Not):
            return f"not ({render(n.operand)})"
        raise ValueError(f"Unknown node: {n}")
    return render(node)
