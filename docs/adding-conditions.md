# Recipe: Adding a New Condition Function to Forge

This guide walks through every file and every change needed to add a new
condition function — like `CROSSOVER(a, b)` — to the Forge indicator DSL.

We use **CROSSOVER** as the worked example throughout, but the same pattern
works for any function: `HIGHEST(high, 20)`, `BARS_SINCE(cond)`, etc.

---

## Architecture Overview

When you write a condition like `rsi < 30 AND CROSSOVER(ema_8, ema_5)`,
here's where it goes:

```
Condition string               Backend (Python)                  Frontend (React)
"rsi < 30 AND           →     dsl/conditions.py          →     ConditionBuilder.tsx
 CROSSOVER(ema_8, ema_5)"
                                  │                                  │
                            Lexer → tokens                    Parse string into UI rows
                            Parser → AST tree                 Serialize UI rows → string
                            Render → Pine Script              └──→ /api/dsl
                                  │
                                  ↓
                        generators/pinescript.py
                        (receives condition as string,
                         calls conditions.parse/to_pine_condition)
```

Three files to touch for a new function:

| File | What it does |
|------|-------------|
| `dsl/conditions.py` | Parses condition strings into AST, renders to Pine |
| `generators/pinescript.py` | Only if your function needs special handling (rare) |
| `web/src/components/ConditionBuilder.tsx` | UI for building conditions visually |

---

## Layer 1: AST Nodes (`dsl/conditions.py`, top)

**What is an AST node?** It's a Python data class that represents one piece
of a condition expression. The parser turns text into a tree of these nodes.

**Existing nodes:**
```python
@dataclass
class Identifier:           # rsi, ema_8, hammer, close
    name: str

@dataclass
class Number:               # 30, 50.0, -1
    value: float

@dataclass
class Compare:              # rsi < 30, ema_8 > ema_5
    op: str
    left: Node
    right: Node

@dataclass
class LogicOp:              # A AND B, A OR B
    op: str
    left: Node
    right: Node

@dataclass
class Not:                  # NOT hammer
    operand: Node
```

**Your new node** sits alongside these. Every function-like condition
(`CROSSOVER(a, b)`) needs a node with left and right arguments:

```python
@dataclass
class Crossover:            # CROSSOVER(ema_8, ema_5)
    left: Node
    right: Node

@dataclass
class Crossunder:           # CROSSUNDER(ema_8, ema_5)
    left: Node
    right: Node
```

**Then register them in the Union type** at the bottom of the AST section:

```python
# BEFORE:
Node = Union[Identifier, Number, Compare, LogicOp, Not]

# AFTER:
Node = Union[Identifier, Number, Compare, LogicOp, Not, Crossover, Crossunder]
```

This tells Python's type checker and all the visitor functions that these
are valid node types.

---

## Layer 2: Lexer (`dsl/conditions.py`, TOKEN_SPEC)

**What is the lexer?** It breaks a condition string into tokens — the smallest
meaningful pieces: `rsi`, `<`, `30`, `AND`, `CROSSOVER`, `(`, `ema_8`, `,`, `ema_5`, `)`.

The lexer uses regex patterns in order. The first one that matches wins.

**Before** — the comma was not handled:
```python
TOKEN_SPEC = [
    ("AND",      r"\bAND\b"),
    ("OR",       r"\bOR\b"),
    ("NOT",      r"\bNOT\b"),
    ("OP",       r">=|<=|!=|==|>|<"),
    ("NUMBER",   r"-?\d+\.?\d*"),
    ("LPAREN",   r"\("),
    ("RPAREN",   r"\)"),
    ("IDENT",    r"[a-zA-Z_][a-zA-Z0-9_]*"),   # ← matches CROSSOVER as IDENT
    ("SKIP",     r"[ \t]+"),
    ("MISMATCH", r"."),
]
```

**After** — add COMMA:
```python
    ("COMMA",    r","),          # ← new! needed for CROSSOVER(a, b)
```

**Why?** `CROSSOVER(ema_8, ema_5)` has a comma between arguments. Without a
COMMA token, the `,` would fall through to `MISMATCH` and crash.

**Key insight:** `CROSSOVER` and `CROSSUNDER` are NOT added as separate tokens.
They match the existing `IDENT` pattern `[a-zA-Z_][a-zA-Z0-9_]*` just like
`rsi`, `ema_8`, or `hammer`. We handle them specially in the parser instead.

---

## Layer 3: Parser (`dsl/conditions.py`, the `_value()` method)

**What is the parser?** It takes the token stream and builds the AST tree.
The grammar is:

```
expr        → term (AND/OR term)*
term        → NOT term | comparison
comparison  → value (OP value)?
value       → IDENTIFIER | NUMBER | (expr) | CROSSOVER(value, value)
```

The `_value()` method handles the bottom level — identifiers, numbers,
parenthesized sub-expressions, and now function calls.

**Before** — only handled simple values:
```python
def _value(self) -> Node:
    tok = self.peek()
    if tok.kind == "NUMBER":
        self.consume("NUMBER")
        return Number(value=float(tok.value))
    if tok.kind == "IDENT":
        name = tok.value
        self.consume("IDENT")
        return Identifier(name=name)          # ← always returned Identifier
    if tok.kind == "LPAREN":
        self.consume("LPAREN")
        node = self._expr()
        self.consume("RPAREN")
        return node
```

**After** — checks if the identifier is a function name:
```python
def _value(self) -> Node:
    tok = self.peek()
    if tok.kind == "NUMBER":
        self.consume("NUMBER")
        return Number(value=float(tok.value))
    if tok.kind == "IDENT":
        name = tok.value
        self.consume("IDENT")
        # ★ NEW: Check if this is a function call
        if name.upper() == "CROSSOVER" or name.upper() == "CROSSUNDER":
            self.consume("LPAREN")           # expect (
            left = self._expr()               # parse first argument
            self.consume("COMMA")             # expect ,
            right = self._expr()              # parse second argument
            self.consume("RPAREN")            # expect )
            if name.upper() == "CROSSOVER":
                return Crossover(left=left, right=right)
            else:
                return Crossunder(left=left, right=right)
        return Identifier(name=name)          # normal identifier
    if tok.kind == "LPAREN":
        self.consume("LPAREN")
        node = self._expr()
        self.consume("RPAREN")
        return node
```

**Walk through `CROSSOVER(ema_8, ema_5)`:**

1. `peek()` → IDENT("CROSSOVER")
2. `consume("IDENT")` → removes CROSSOVER, name = "CROSSOVER"
3. Name is "CROSSOVER" → enter function branch
4. `consume("LPAREN")` → eats `(`
5. `_expr()` → parses `ema_8` as Identifier("ema_8")
6. `consume("COMMA")` → eats `,`
7. `_expr()` → parses `ema_5` as Identifier("ema_5")
8. `consume("RPAREN")` → eats `)`
9. Returns `Crossover(left=Identifier("ema_8"), right=Identifier("ema_5"))`

---

## Layer 4: Visitor Functions (`dsl/conditions.py`)

Visitors walk through the AST to do something. There are two:

### `collect_identifiers()` — finds all referenced variable names

Used to detect if session variables are needed. Add branches for new nodes:

```python
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
    elif isinstance(n, Crossover):        # ← NEW
        walk(n.left)
        walk(n.right)
    elif isinstance(n, Crossunder):       # ← NEW
        walk(n.left)
        walk(n.right)
```

**Why?** If CROSSOVER(ema_8, ema_5) appears in a condition, the system needs to
know that `ema_8` and `ema_5` are referenced, so it generates those indicator
variables.

### `to_pine_condition()` — renders the AST to Pine Script

This is the final output. Add render cases for new nodes:

```python
def render(n: Node) -> str:
    if isinstance(n, Identifier):
        return n.name
    elif isinstance(n, Number):
        return str(n.value)
    elif isinstance(n, Compare):
        return f"{render(n.left)} {n.op} {render(n.right)}"
    elif isinstance(n, LogicOp):
        return f"({render(n.left)} {n.op.lower()} {render(n.right)})"
    elif isinstance(n, Not):
        return f"not ({render(n.operand)})"
    elif isinstance(n, Crossover):                # ← NEW
        return f"ta.crossover({render(n.left)}, {render(n.right)})"
    elif isinstance(n, Crossunder):               # ← NEW
        return f"ta.crossunder({render(n.left)}, {render(n.right)})"
```

**What happens:** `Crossover(Identifier("ema_8"), Identifier("ema_5"))`
→ `"ta.crossover(ema_8, ema_5)"` which is valid Pine Script.

**Pattern:** The node name (`Crossover`) maps to the Pine function (`ta.crossover`).
Arguments come from rendering child nodes.

---

## Layer 5: Frontend — ConditionBuilder UI

The UI (`web/src/components/ConditionBuilder.tsx`) lets users build
conditions visually. It has three parts:

### 5a. Data Model (`CondRow` interface)

Each condition row stores: which indicator on the left, what operator,
and a right value (number or another indicator ref).

For crossover, we need a second ref field:

```typescript
export interface CondRow {
  id: string
  left: string                    // first indicator (e.g. ema_8)
  op: string                      // operator (>, <, XOVER, XUNDER, etc.)
  rightType: 'value' | 'ref'     // number vs indicator on the right
  rightVal: string                // the number or ref
  crossRight: string              // ★ NEW: second argument for XOVER/XUNDER
  logic: 'AND' | 'OR'
}
```

### 5b. Parser (`parseToRows`)

This converts a condition string like `CROSSOVER(ema_8, ema_5) AND rsi > 50`
back into UI rows. Add a regex to detect the function-call pattern:

```typescript
// Try crossover: CROSSOVER(a, b)
const crossMatch = part.match(
  /^(CROSSOVER|CROSSUNDER)\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)$/i
)
if (crossMatch) {
  const [, crossType, left, right] = crossMatch
  rows.push({
    left: left.trim(),
    op: crossType === 'CROSSOVER' ? 'XOVER' : 'XUNDER',
    crossRight: right.trim(),
    // ...
  })
}
```

**Regex breakdown:** `/^(CROSSOVER|CROSSUNDER)\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)$/i`
- `^` — start of string
- `(CROSSOVER|CROSSUNDER)` — capture the function name
- `\s*\(` — optional whitespace + opening paren
- `([^,]+)` — capture everything before the comma (first arg)
- `\s*,\s*` — comma with optional whitespace
- `([^)]+)` — capture everything before the closing paren (second arg)
- `\s*\)$` — closing paren, end of string
- `/i` — case insensitive

### 5c. Serializer (`rowsToString`)

This converts UI rows back to a condition string. Add a branch for cross rows:

```typescript
if (r.op === 'XOVER' || r.op === 'XUNDER') {
  const fn = r.op === 'XOVER' ? 'CROSSOVER' : 'CROSSUNDER'
  return `${fn}(${left}, ${r.crossRight || 'close'})`
}
```

When the user picks "XOVER" in the dropdown and selects `ema_8` (left)
and `ema_5` (crossRight), this produces: `CROSSOVER(ema_8, ema_5)`.

### 5d. UI Rendering

The operator dropdown needs XOVER/XUNDER options. When one is selected,
show a second ref selector instead of the normal value/ref controls:

```tsx
<select value={row.op} onChange={...}>
  <optgroup label="Compare">
    <option value=">">&gt;</option>
    <option value="<">&lt;</option>
    ...
  </optgroup>
  <optgroup label="Cross">
    <option value="XOVER">XOVER</option>      {/* NEW */}
    <option value="XUNDER">XUNDER</option>    {/* NEW */}
  </optgroup>
</select>

{row.op === 'XOVER' || row.op === 'XUNDER' ? (
  /* Show second ref selector */
  <select value={row.crossRight} onChange={...}>
    <option value="">— cross with —</option>
    {availableRefs.filter(r => r !== row.left).map(ref => (
      <option value={ref}>{ref}</option>
    ))}
  </select>
) : (
  /* Show normal value/ref controls */
  ...
)}
```

**Key:** `availableRefs.filter(r => r !== row.left)` prevents crossing
an indicator with itself (meaningless).

---

## Checklist (Your Recipe)

When adding a new function like `HIGHEST(high, 20)` or `BARS_SINCE(cond)`:

### Backend (`dsl/conditions.py`)

- [ ] **AST node** — add new `@dataclass` class
- [ ] **Union type** — add to `Node = Union[...]`
- [ ] **Lexer** — add any new tokens (like COMMA for multi-arg functions)
- [ ] **Parser `_value()`** — add an `if name.upper() == "NEW_FN":` branch
  that consumes LPAREN, args, COMMAs, RPAREN and returns your new node
- [ ] **`collect_identifiers()`** — add `elif isinstance(n, NewNode):` branches
- [ ] **`to_pine_condition()`** — add `elif isinstance(n, NewNode):` that
  renders the Pine Script function call

### Frontend (`ConditionBuilder.tsx`)

- [ ] **`CondRow` interface** — add any new fields needed
- [ ] **`parseToRows()`** — add regex to detect the function-call pattern
- [ ] **`rowsToString()`** — add serialization branch
- [ ] **UI rendering** — add dropdown options and conditional controls

### Optional

- [ ] **Update grammar docstring** in `conditions.py` (top of file)
- [ ] **Full Pine generation test** via Python REPL
- [ ] **TypeScript compile check** — `npx tsc --noEmit` in `web/`

---

## Testing Your Changes

```python
# From the Forge project root
cd "/Users/mark/Library/Mobile Documents/com~apple~CloudDocs/VisualStudioProjects/Forge"
source venv/bin/activate

# Test parsing + Pine rendering
python3 -c "
from dsl.conditions import to_pine_condition, parse_condition
result = to_pine_condition(parse_condition('CROSSOVER(ema_8, ema_5) AND rsi > 50'))
print(result)
# → (ta.crossover(ema_8, ema_5) and rsi > 50.0)
"

# Test full Pine generation
python3 -c "
from dsl.schema import IndicatorDSL, IndicatorDef, SignalDef
from generators.pinescript import generate_pinescript
dsl = IndicatorDSL(
    name='Test', timeframe='1h',
    indicators=[IndicatorDef(id='ema_5', type='ema', params={'period': 5})],
    compounds=[], patterns=[], signals={
        'entry': SignalDef(condition='CROSSOVER(ema_8, ema_5) AND rsi > 50'),
    }, plots=[]
)
print(generate_pinescript(dsl))
"

# Frontend check
cd web && npx tsc --noEmit
```
