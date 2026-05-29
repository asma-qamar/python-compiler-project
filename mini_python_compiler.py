import ast
import io
import keyword
import sys
import token
import tokenize
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# Beautiful Python Mini Compiler
# Supports a Python subset:
#   - assignments: a = 5
#   - arithmetic: c = a + b
#   - comparisons: if g > 20:
#   - print calls: print(g)
#
# Phases:
#   1. Lexical Analysis
#   2. Syntax Analysis / Parse Tree
#   3. Semantic Analysis
#   4. Symbol Table
#   5. Intermediate Code Generation (TAC)
#   6. Optimization
#   7. Error Handling
# ============================================================


# ---------------- Table Helpers ----------------

def cell(value: Any, max_len: int = 38) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\n", "\\n").replace("\t", "\\t")
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def print_title(title: str) -> None:
    print("\n" + "=" * 78)
    print(title.center(78))
    print("=" * 78)


def print_table(headers: List[str], rows: List[List[Any]], widths: Optional[List[int]] = None) -> None:
    if widths is None:
        widths = []
        for i, h in enumerate(headers):
            max_content = len(str(h))
            for row in rows:
                if i < len(row):
                    max_content = max(max_content, len(cell(row[i], 45)))
            widths.append(min(max(max_content, 8), 45))

    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"

    def row_line(values: List[Any]) -> str:
        padded = []
        for i, w in enumerate(widths):
            val = values[i] if i < len(values) else ""
            padded.append(cell(val, w).ljust(w))
        return "| " + " | ".join(padded) + " |"

    print(sep)
    print(row_line(headers))
    print(sep)
    if rows:
        for row in rows:
            print(row_line(row))
    else:
        print(row_line(["No data"] + [""] * (len(headers) - 1)))
    print(sep)


# ---------------- Lexical Analysis ----------------

@dataclass
class TokenInfo:
    lexeme: str
    token_type: str
    category: str
    line: int
    column: int


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens: List[TokenInfo] = []

    def classify(self, tok_type: int, tok_str: str) -> Tuple[str, str]:
        token_name = token.tok_name.get(tok_type, str(tok_type))

        if tok_type == tokenize.NAME:
            if keyword.iskeyword(tok_str):
                return "KEYWORD", "Keyword"
            if tok_str in {"print", "input", "len"}:
                return "BUILTIN", "Built-in Function"
            return "IDENTIFIER", "Identifier"

        if tok_type == tokenize.NUMBER:
            return "NUMBER", "Constant"

        if tok_type == tokenize.STRING:
            return "STRING", "Constant"

        if tok_type == tokenize.OP:
            return "OPERATOR", "Operator"

        if tok_type in {tokenize.NEWLINE, tokenize.NL}:
            return "NEWLINE", "Line Break"

        if tok_type == tokenize.INDENT:
            return "INDENT", "Indentation"

        if tok_type == tokenize.DEDENT:
            return "DEDENT", "Indentation"

        if tok_type == tokenize.ENDMARKER:
            return "EOF", "End Marker"

        return token_name, token_name.title()

    def run(self) -> List[TokenInfo]:
        self.tokens.clear()
        reader = io.StringIO(self.source).readline

        try:
            for tok in tokenize.generate_tokens(reader):
                tok_type, tok_str, start, end, line_text = tok

                if tok_type in {
                    tokenize.ENCODING,
                    tokenize.COMMENT,
                }:
                    continue

                if tok_type == tokenize.NL:
                    continue

                if tok_type == tokenize.ENDMARKER:
                    lexeme = "EOF"
                elif tok_type == tokenize.NEWLINE:
                    lexeme = "\\n"
                elif tok_type == tokenize.INDENT:
                    lexeme = "INDENT"
                elif tok_type == tokenize.DEDENT:
                    lexeme = "DEDENT"
                else:
                    lexeme = tok_str

                token_name, category = self.classify(tok_type, tok_str)
                self.tokens.append(TokenInfo(lexeme, token_name, category, start[0], start[1] + 1))

        except tokenize.TokenError as exc:
            msg, pos = exc.args
            raise SyntaxError(f"Tokenization Error near line {pos[0]}: {msg}")

        return self.tokens

    def display(self) -> None:
        print_title("1. LEXICAL ANALYSIS")

        rows = []
        for i, t in enumerate(self.tokens, 1):
            if t.token_type == "EOF":
                continue
            rows.append([i, t.lexeme, t.token_type, t.category, t.line, t.column])

        print_table(
            ["No.", "Lexeme", "Token", "Type", "Line", "Col"],
            rows,
            [5, 18, 15, 18, 6, 5],
        )

        keywords = sorted({t.lexeme for t in self.tokens if t.category == "Keyword"})
        identifiers = sorted({t.lexeme for t in self.tokens if t.category == "Identifier"})
        operators = sorted({t.lexeme for t in self.tokens if t.category == "Operator"})
        constants = sorted({t.lexeme for t in self.tokens if t.category == "Constant"})

        summary_rows = [
            ["Keywords", ", ".join(keywords) if keywords else "-"],
            ["Identifiers", ", ".join(identifiers) if identifiers else "-"],
            ["Operators", ", ".join(operators) if operators else "-"],
            ["Constants", ", ".join(constants) if constants else "-"],
        ]

        print("\nToken Summary")
        print_table(["Category", "Values"], summary_rows, [15, 58])


# ---------------- Syntax Analysis ----------------

class SyntaxAnalyzer:
    def __init__(self, source: str):
        self.source = source
        self.tree: Optional[ast.Module] = None

    def parse(self) -> ast.Module:
        try:
            self.tree = ast.parse(self.source)
            return self.tree
        except SyntaxError as e:
            print_title("SYNTAX ERROR")
            print(f"Syntax Error at line {e.lineno}, column {e.offset}: {e.msg}")
            suggestion = self.suggest(e)
            if suggestion:
                print("Suggestion:", suggestion)
            raise

    def suggest(self, e: SyntaxError) -> str:
        msg = (e.msg or "").lower()
        if "expected ':'" in msg:
            return "Colon ':' missing ho sakta hai. Example: if x > 0:"
        if "invalid syntax" in msg:
            return "Expression ya operator check karein. Example: c = a + b"
        if "unexpected eof" in msg or "was never closed" in msg:
            return "Bracket/parenthesis close karein."
        return "Line number par syntax carefully check karein."

    def display(self) -> None:
        print_title("2. SYNTAX ANALYSIS")
        print("Parse Status: SUCCESS")
        print("Parser Message: Source code has valid Python syntax.")
        print("\nParse Tree / Syntax Tree")
        print("------------------------")
        if self.tree is not None:
            lines = self.parse_tree_lines(self.tree)
            for line in lines:
                print(line)

    def expr_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return f"Identifier: {node.id}"
        if isinstance(node, ast.Constant):
            return f"Constant: {repr(node.value)}"
        if isinstance(node, ast.BinOp):
            return f"Binary Expression: {self.op_symbol(node.op)}"
        if isinstance(node, ast.Compare):
            return f"Comparison: {self.op_symbol(node.ops[0])}"
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return f"Function Call: {node.func.id}"
            return "Function Call"
        return type(node).__name__

    def op_symbol(self, op: ast.AST) -> str:
        return {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.Mod: "%",
            ast.Pow: "**",
            ast.Gt: ">",
            ast.Lt: "<",
            ast.GtE: ">=",
            ast.LtE: "<=",
            ast.Eq: "==",
            ast.NotEq: "!=",
        }.get(type(op), type(op).__name__)

    def parse_tree_lines(self, node: ast.AST, prefix: str = "", is_last: bool = True) -> List[str]:
        label = self.node_label(node)
        connector = "└── " if is_last else "├── "
        lines = [prefix + connector + label] if prefix else [label]

        child_prefix = prefix + ("    " if is_last else "│   ")
        children = self.get_children(node)

        for idx, child in enumerate(children):
            lines.extend(self.parse_tree_lines(child, child_prefix, idx == len(children) - 1))

        return lines

    def node_label(self, node: ast.AST) -> str:
        if isinstance(node, ast.Module):
            return "Program"
        if isinstance(node, ast.Assign):
            target = node.targets[0].id if isinstance(node.targets[0], ast.Name) else "target"
            return f"Assignment Statement: {target}"
        if isinstance(node, ast.Expr):
            return "Expression Statement"
        if isinstance(node, ast.If):
            return "If Statement"
        if isinstance(node, ast.While):
            return "While Statement"
        return self.expr_name(node)

    def get_children(self, node: ast.AST) -> List[ast.AST]:
        if isinstance(node, ast.Module):
            return list(node.body)
        if isinstance(node, ast.Assign):
            return [node.targets[0], node.value]
        if isinstance(node, ast.BinOp):
            return [node.left, node.right]
        if isinstance(node, ast.Compare):
            return [node.left] + list(node.comparators)
        if isinstance(node, ast.Expr):
            return [node.value]
        if isinstance(node, ast.Call):
            return list(node.args)
        if isinstance(node, ast.If):
            return [node.test] + list(node.body) + list(node.orelse)
        if isinstance(node, ast.While):
            return [node.test] + list(node.body)
        return []


# ---------------- Semantic Analysis and Symbol Table ----------------

@dataclass
class Symbol:
    name: str
    scope: str
    typ: str
    value: Any
    line: int
    offset: int
    width: int
    details: str


class SemanticAnalyzer:
    def __init__(self):
        self.symbols: Dict[str, Symbol] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.offset = 0
        self.scope = "global"

    def width_of(self, typ: str) -> int:
        return {"int": 4, "float": 8, "str": 50, "bool": 1, "unknown": 0}.get(typ, 4)

    def type_of_constant(self, value: Any) -> str:
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, str):
            return "str"
        return "unknown"

    def analyze(self, tree: ast.Module) -> None:
        for stmt in tree.body:
            self.visit_stmt(stmt)

    def visit_stmt(self, node: ast.AST) -> None:
        if isinstance(node, ast.Assign):
            self.handle_assign(node)
        elif isinstance(node, ast.Expr):
            self.infer_expr(node.value)
        elif isinstance(node, ast.If):
            test_type, _ = self.infer_expr(node.test)
            if test_type not in {"bool", "unknown"}:
                self.warnings.append(f"Line {node.lineno}: if condition should be boolean/comparison.")
            for stmt in node.body:
                self.visit_stmt(stmt)
            for stmt in node.orelse:
                self.visit_stmt(stmt)
        elif isinstance(node, ast.While):
            test_type, _ = self.infer_expr(node.test)
            if test_type not in {"bool", "unknown"}:
                self.warnings.append(f"Line {node.lineno}: while condition should be boolean/comparison.")
            for stmt in node.body:
                self.visit_stmt(stmt)
        else:
            self.errors.append(f"Line {getattr(node, 'lineno', '?')}: Unsupported statement: {type(node).__name__}")

    def handle_assign(self, node: ast.Assign) -> None:
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            self.errors.append(f"Line {node.lineno}: Only simple assignments like a = 5 are supported.")
            return

        name = node.targets[0].id
        typ, value = self.infer_expr(node.value)

        if name not in self.symbols:
            width = self.width_of(typ)
            sym = Symbol(
                name=name,
                scope=self.scope,
                typ=typ,
                value=value if value is not None else "-",
                line=node.lineno,
                offset=self.offset,
                width=width,
                details="Declared and initialized",
            )
            self.symbols[name] = sym
            self.offset += width
        else:
            old = self.symbols[name]
            if old.typ != typ and typ != "unknown":
                self.warnings.append(
                    f"Line {node.lineno}: variable '{name}' type changed from {old.typ} to {typ}."
                )
            old.typ = typ
            old.value = value if value is not None else "-"
            old.details = "Reassigned"

    def infer_expr(self, node: ast.AST) -> Tuple[str, Any]:
        if isinstance(node, ast.Constant):
            return self.type_of_constant(node.value), node.value

        if isinstance(node, ast.Name):
            if node.id not in self.symbols:
                self.errors.append(f"Line {node.lineno}: Semantic Error: Variable '{node.id}' not declared.")
                return "unknown", None
            sym = self.symbols[node.id]
            return sym.typ, None if sym.value == "-" else sym.value

        if isinstance(node, ast.BinOp):
            left_type, left_value = self.infer_expr(node.left)
            right_type, right_value = self.infer_expr(node.right)
            op = SyntaxAnalyzer("").op_symbol(node.op)

            if left_type != "unknown" and right_type != "unknown":
                if left_type != right_type:
                    self.errors.append(
                        f"Line {node.lineno}: Type Mismatch: cannot apply '{op}' between {left_type} and {right_type}."
                    )
                    return "unknown", None

                if left_type == "str" and op not in {"+", "*"}:
                    self.errors.append(
                        f"Line {node.lineno}: Type Mismatch: operator '{op}' is invalid for strings."
                    )
                    return "unknown", None

            result_type = left_type if left_type == right_type else "unknown"

            if left_value is not None and right_value is not None:
                try:
                    value = self.eval_binary(left_value, right_value, op)
                    return self.type_of_constant(value), value
                except Exception:
                    pass

            return result_type, None

        if isinstance(node, ast.Compare):
            self.infer_expr(node.left)
            for comp in node.comparators:
                self.infer_expr(comp)
            return "bool", None

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "print":
                for arg in node.args:
                    self.infer_expr(arg)
                return "unknown", None
            self.errors.append(f"Line {node.lineno}: Unsupported function call.")
            return "unknown", None

        self.errors.append(f"Line {getattr(node, 'lineno', '?')}: Unsupported expression: {type(node).__name__}")
        return "unknown", None

    def eval_binary(self, a: Any, b: Any, op: str) -> Any:
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            return a / b
        raise ValueError("Unsupported operator")

    def display(self) -> None:
        print_title("3. SEMANTIC ANALYSIS")

        if not self.errors:
            print("Semantic Status: SUCCESS")
            print("No undeclared variables or type mismatch errors found.")
        else:
            print("Semantic Status: FAILED")
            for e in self.errors:
                print(e)

        if self.warnings:
            print("\nSemantic Warnings:")
            for w in self.warnings:
                print(w)

    def display_symbol_table(self) -> None:
        print_title("4. SYMBOL TABLE")

        rows = []
        for sym in self.symbols.values():
            rows.append([sym.scope, sym.name, sym.typ, sym.value, sym.offset, sym.width, sym.line, sym.details])

        print_table(
            ["Scope", "Variable", "Type", "Value", "Offset", "Width", "Line", "Details"],
            rows,
            [10, 14, 10, 14, 8, 7, 6, 24],
        )


# ---------------- TAC Generation ----------------

@dataclass
class TACRow:
    line: int
    result: str
    arg1: str
    op: str
    arg2: str
    code: str


class TACGenerator:
    def __init__(self):
        self.rows: List[TACRow] = []
        self.temp_count = 0
        self.label_count = 0
        self.syntax = SyntaxAnalyzer("")

    def new_temp(self) -> str:
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self) -> str:
        self.label_count += 1
        return f"L{self.label_count}"

    def add(self, result: str, arg1: str, op: str, arg2: str, code: str) -> None:
        self.rows.append(TACRow(len(self.rows) + 1, result, arg1, op, arg2, code))

    def generate(self, tree: ast.Module) -> List[TACRow]:
        for stmt in tree.body:
            self.gen_stmt(stmt)
        return self.rows

    def gen_stmt(self, node: ast.AST) -> None:
        if isinstance(node, ast.Assign):
            target = node.targets[0].id
            place = self.gen_expr(node.value)
            self.add(target, place, "=", "", f"{target} = {place}")
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name) and node.value.func.id == "print":
                args = [self.gen_expr(arg) for arg in node.value.args]
                for arg in args:
                    self.add("", arg, "param", "", f"param {arg}")
                self.add("", "print", "call", str(len(args)), f"call print, {len(args)}")
        elif isinstance(node, ast.If):
            cond = self.gen_expr(node.test)
            end_label = self.new_label()
            self.add("", cond, "ifFalse", end_label, f"ifFalse {cond} goto {end_label}")
            for stmt in node.body:
                self.gen_stmt(stmt)
            self.add(end_label, "", "label", "", f"{end_label}:")
        elif isinstance(node, ast.While):
            start = self.new_label()
            end = self.new_label()
            self.add(start, "", "label", "", f"{start}:")
            cond = self.gen_expr(node.test)
            self.add("", cond, "ifFalse", end, f"ifFalse {cond} goto {end}")
            for stmt in node.body:
                self.gen_stmt(stmt)
            self.add("", "", "goto", start, f"goto {start}")
            self.add(end, "", "label", "", f"{end}:")

    def gen_expr(self, node: ast.AST) -> str:
        if isinstance(node, ast.Constant):
            return repr(node.value) if isinstance(node.value, str) else str(node.value)

        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.BinOp):
            left = self.gen_expr(node.left)
            right = self.gen_expr(node.right)
            op = self.syntax.op_symbol(node.op)
            temp = self.new_temp()
            self.add(temp, left, op, right, f"{temp} = {left} {op} {right}")
            return temp

        if isinstance(node, ast.Compare):
            left = self.gen_expr(node.left)
            right = self.gen_expr(node.comparators[0])
            op = self.syntax.op_symbol(node.ops[0])
            temp = self.new_temp()
            self.add(temp, left, op, right, f"{temp} = {left} {op} {right}")
            return temp

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                args = [self.gen_expr(arg) for arg in node.args]
                return f"{node.func.id}({', '.join(args)})"

        return "?"

    def display(self) -> None:
        print_title("5. INTERMEDIATE CODE GENERATION (TAC)")
        rows = [[r.line, r.result, r.arg1, r.op, r.arg2, r.code] for r in self.rows]
        print_table(
            ["Line", "Result", "Arg1", "Operator", "Arg2", "Three Address Code"],
            rows,
            [6, 12, 12, 10, 12, 24],
        )


# ---------------- Optimization ----------------

class Optimizer:
    def __init__(self, tac_rows: List[TACRow]):
        self.original = tac_rows
        self.optimized: List[TACRow] = []
        self.reports: List[List[str]] = []

    def is_number(self, x: str) -> bool:
        try:
            float(x)
            return True
        except Exception:
            return False

    def fold(self, a: str, op: str, b: str) -> Optional[str]:
        if not (self.is_number(a) and self.is_number(b)):
            return None
        x = float(a)
        y = float(b)
        if op == "+":
            val = x + y
        elif op == "-":
            val = x - y
        elif op == "*":
            val = x * y
        elif op == "/" and y != 0:
            val = x / y
        else:
            return None
        if val.is_integer():
            return str(int(val))
        return str(val)

    def optimize(self) -> None:
        expr_map: Dict[Tuple[str, str, str], str] = {}
        replacement: Dict[str, str] = {}

        for row in self.original:
            result, arg1, op, arg2 = row.result, row.arg1, row.op, row.arg2

            arg1 = replacement.get(arg1, arg1)
            arg2 = replacement.get(arg2, arg2)

            if op in {"+", "-", "*", "/"}:
                folded = self.fold(arg1, op, arg2)
                if folded is not None:
                    old = f"{result} = {arg1} {op} {arg2}"
                    new = f"{result} = {folded}"
                    self.reports.append(["Constant Folding", old, new])
                    replacement[result] = folded
                    self.optimized.append(TACRow(row.line, result, folded, "=", "", new))
                    continue

                key = (arg1, op, arg2)
                if key in expr_map:
                    old = f"{result} = {arg1} {op} {arg2}"
                    new = f"{result} = {expr_map[key]}"
                    self.reports.append(["Common Subexpression", old, new])
                    replacement[result] = expr_map[key]
                    self.optimized.append(TACRow(row.line, result, expr_map[key], "=", "", new))
                    continue
                expr_map[key] = result

            if op == "=":
                arg1 = replacement.get(arg1, arg1)
                code = f"{result} = {arg1}"
                self.optimized.append(TACRow(row.line, result, arg1, op, arg2, code))
            else:
                code = row.code
                for old, new in replacement.items():
                    code = code.replace(old, new)
                self.optimized.append(TACRow(row.line, result, arg1, op, arg2, code))

        self.dead_code_elimination()

    def dead_code_elimination(self) -> None:
        used = set()
        for row in self.optimized:
            for value in [row.arg1, row.arg2]:
                if value and value.isidentifier():
                    used.add(value)

        final_rows = []
        for row in self.optimized:
            # Remove simple assignments to variables that are never used and are not control/print rows.
            if row.op == "=" and row.result.isidentifier() and not row.result.startswith("t"):
                if row.result not in used:
                    self.reports.append(["Dead Code Elimination", row.code, "Removed unused assignment"])
                    continue
            final_rows.append(row)

        self.optimized = final_rows

    def display(self) -> None:
        print_title("6. OPTIMIZATION PHASE")

        print("Optimization Report")
        print_table(
            ["Technique", "Before", "After"],
            self.reports,
            [24, 25, 25],
        )

        print("\nOptimized TAC")
        rows = [[i + 1, r.result, r.arg1, r.op, r.arg2, r.code] for i, r in enumerate(self.optimized)]
        print_table(
            ["Line", "Result", "Arg1", "Operator", "Arg2", "Optimized Code"],
            rows,
            [6, 12, 12, 10, 12, 24],
        )


# ---------------- Main Driver ----------------

def run_compiler(path: str) -> int:
    source_path = path
    try:
        with open(source_path, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: Source file '{source_path}' not found.")
        return 1

    print_title("MINI PYTHON COMPILER")
    print("Source File:", source_path)
    print("Language   : Python subset")
    print("Features   : Lexer, Parser, Parse Tree, Semantic Analysis, Symbol Table, TAC, Optimization, Error Handling")

    # Lexical Analysis
    try:
        lexer = Lexer(source)
        lexer.run()
        lexer.display()
    except SyntaxError as e:
        print(str(e))
        return 1

    # Syntax Analysis
    syntax = SyntaxAnalyzer(source)
    try:
        tree = syntax.parse()
        syntax.display()
    except SyntaxError:
        return 1

    # Semantic Analysis
    semantic = SemanticAnalyzer()
    semantic.analyze(tree)
    semantic.display()
    semantic.display_symbol_table()

    # Stop TAC if semantic errors exist
    if semantic.errors:
        print_title("ERROR HANDLING")
        print("Compilation stopped because semantic errors were found.")
        print("Fix the errors shown above and run again.")
        return 1

    # TAC
    tac = TACGenerator()
    tac.generate(tree)
    tac.display()

    # Optimization
    optimizer = Optimizer(tac.rows)
    optimizer.optimize()
    optimizer.display()

    print_title("7. ERROR HANDLING")
    print("No syntax or semantic errors found.")
    print("Compilation completed successfully.")
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python mini_python_compiler.py best_python_test.py")
        return 1
    return run_compiler(sys.argv[1])


if __name__ == "__main__":
    raise SystemExit(main())
