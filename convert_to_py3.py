from pathlib import Path
import re
import shutil

root = Path(__file__).resolve().parent
bin_dir = root / "bin"

tac_file = bin_dir / "tac.py"
symbol_file = bin_dir / "symbolTable.py"
irgen_file = bin_dir / "irgen.py"

for file_path in [tac_file, symbol_file, irgen_file]:
    backup = file_path.with_suffix(file_path.suffix + ".backup")
    if file_path.exists() and not backup.exists():
        shutil.copy2(file_path, backup)

# ---------------- TAC TABLE PATCH ----------------

tac_text = tac_file.read_text(encoding="utf-8", errors="ignore")

new_print_code = r'''
def _format_cell(value):
    if value is None:
        return ""
    text = str(value).replace("\n", "\\n").replace("\t", "\\t")
    if len(text) > 30:
        text = text[:27] + "..."
    return text

def _print_row(values, widths):
    print("| " + " | ".join(_format_cell(v).ljust(w) for v, w in zip(values, widths)) + " |")

def _print_separator(widths):
    print("+-" + "-+-".join("-" * w for w in widths) + "-+")

def printCode():
    print("\nTHREE ADDRESS CODE (TAC)")
    print("------------------------")

    headers = ["Line", "Result", "Arg1", "Arg2", "Operator"]
    widths = [6, 18, 18, 18, 14]

    for functionName in code.keys():
        print("\nScope/Function:", functionName)
        _print_separator(widths)
        _print_row(headers, widths)
        _print_separator(widths)

        for i, quad_item in enumerate(code[functionName]):
            result, arg1, arg2, operator = quad_item
            _print_row([i, result, arg1, arg2, operator], widths)

        _print_separator(widths)
'''

tac_text = re.sub(
    r"def printCode\(\):.*?(?=\ndef merge\()",
    new_print_code + "\n",
    tac_text,
    flags=re.DOTALL
)

tac_file.write_text(tac_text, encoding="utf-8")


# ---------------- SYMBOL TABLE PATCH ----------------

symbol_text = symbol_file.read_text(encoding="utf-8", errors="ignore")

new_symbol_table = r'''
def _st_cell(value):
    if value is None:
        return ""
    text = str(value).replace("\n", "\\n").replace("\t", "\\t")
    if len(text) > 35:
        text = text[:32] + "..."
    return text

def _st_row(values, widths):
    print("| " + " | ".join(_st_cell(v).ljust(w) for v, w in zip(values, widths)) + " |")

def _st_sep(widths):
    print("+-" + "-+-".join("-" * w for w in widths) + "-+")

def printSymbolTableHistory():
    print("\nSYMBOL TABLE")
    print("------------")

    headers = ["Scope", "Variable", "Type", "Place", "Offset", "Width", "Details"]
    widths = [15, 18, 12, 15, 8, 8, 35]

    metadata_keys = set([
        "scopeName", "parentName", "type", "returnType",
        "width", "numParam"
    ])

    _st_sep(widths)
    _st_row(headers, widths)
    _st_sep(widths)

    row_count = 0

    for st in stackHistory:
        scope_name = st.get("scopeName", "program")

        for name, entry in st.items():
            if name in metadata_keys:
                continue

            if name in ["True", "False"]:
                continue

            if not isinstance(entry, dict):
                continue

            var_type = entry.get("type", "")
            offset = entry.get("offset", "")
            width = entry.get("width", "")
            place = entry.get(scope_name, entry.get("place", ""))

            detail_parts = []
            for key, value in entry.items():
                if key in ["type", "offset", "width", scope_name, "place"]:
                    continue
                detail_parts.append(str(key) + "=" + str(value))

            details = ", ".join(detail_parts)

            _st_row([scope_name, name, var_type, place, offset, width, details], widths)
            row_count += 1

    if row_count == 0:
        _st_row(["-", "No variables found", "-", "-", "-", "-", "-"], widths)

    _st_sep(widths)
'''

symbol_text = re.sub(
    r"def printSymbolTableHistory\(\):.*\Z",
    new_symbol_table + "\n",
    symbol_text,
    flags=re.DOTALL
)

symbol_file.write_text(symbol_text, encoding="utf-8")


# ---------------- IRGEN / TOKEN TABLE / WARNING SUPPRESS PATCH ----------------

irgen_text = irgen_file.read_text(encoding="utf-8", errors="ignore")

# Suppress PLY warnings and LALR debug output
irgen_text = re.sub(
    r"self\.parser\s*=\s*yacc\.yacc\([^\n]*start\s*=\s*['\"]file_input['\"][^\n]*\)",
    "self.parser = yacc.yacc(start='file_input', debug=False, errorlog=yacc.NullLogger(), write_tables=False)",
    irgen_text
)

irgen_text = re.sub(
    r"self\.parser\.parse\(\s*lexer\s*=\s*self\.mlexer\s*,\s*debug\s*=\s*True\s*\)",
    "self.parser.parse(lexer=self.mlexer, debug=False)",
    irgen_text
)

token_table_function = r'''
def _token_cell(value):
    if value is None:
        return ""
    text = str(value).replace("\n", "\\n").replace("\t", "\\t")
    if len(text) > 30:
        text = text[:27] + "..."
    return text

def _token_row(values, widths):
    print("| " + " | ".join(_token_cell(v).ljust(w) for v, w in zip(values, widths)) + " |")

def _token_sep(widths):
    print("+-" + "-+-".join("-" * w for w in widths) + "-+")

def printTokenTable(source_code):
    print("\nTOKENIZATION TABLE")
    print("------------------")

    headers = ["No.", "Lexeme", "Token", "Line"]
    widths = [5, 25, 20, 6]

    _token_sep(widths)
    _token_row(headers, widths)
    _token_sep(widths)

    token_lexer = lexer.G1Lexer()
    token_lexer.input(source_code)

    count = 1

    while True:
        tok = token_lexer.token()

        if not tok:
            break

        if tok.type == "WS":
            continue

        lexeme = tok.value

        if tok.type == "NEWLINE":
            lexeme = "\\n"
        elif tok.type == "INDENT":
            lexeme = "INDENT"
        elif tok.type == "DEDENT":
            lexeme = "DEDENT"
        elif tok.type == "ENDMARKER":
            lexeme = "EOF"

        _token_row([count, lexeme, tok.type, tok.lineno], widths)
        count += 1

    _token_sep(widths)
'''

if "def printTokenTable(source_code):" not in irgen_text:
    irgen_text = irgen_text.replace("class G1Parser(object):", token_table_function + "\nclass G1Parser(object):")

if "printTokenTable(data)" not in irgen_text:
    irgen_text = irgen_text.replace(
        "data = sourcefile.read()",
        "data = sourcefile.read()\n    printTokenTable(data)"
    )

irgen_file.write_text(irgen_text, encoding="utf-8")

print("Done: Output improved successfully.")
print("Now run:")
print(r"python bin\irgen.py test\test1.py")