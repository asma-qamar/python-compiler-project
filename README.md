# Mini Python Compiler

A fully functional educational compiler developed in Python 3 that demonstrates the complete compilation pipeline for a subset of the Python programming language. This project was designed as a Compiler Construction term project to simulate how modern compilers analyze, validate, optimize, and transform high-level source code into structured intermediate representations.

The compiler performs multiple classical compiler phases including lexical analysis, syntax analysis, semantic analysis, symbol table generation, intermediate code generation, optimization, and intelligent error handling. It accepts Python-like source programs containing variable assignments, arithmetic expressions, conditional statements, comparison operators, and print statements.

Unlike basic academic parsers, this compiler provides phase-wise visualization directly in the terminal, allowing users to observe how source code flows through each internal compiler stage. The system uses Python’s built-in `tokenize` and `ast` modules combined with custom semantic validation and optimization logic to emulate real compiler behavior.

## Features

* Lexical Analysis using Python tokenizer
* Token and Lexeme table generation
* Syntax Analysis using Abstract Syntax Trees (AST)
* Readable Parse Tree visualization
* Semantic Analysis and validation
* Undeclared variable detection
* Type mismatch detection
* Symbol Table generation with scope, width, offsets, and line numbers
* Three Address Code (TAC) generation
* Intermediate code optimization
* Constant Folding
* Common Subexpression Elimination
* Dead Code Elimination
* Detailed error reporting with line numbers and suggestions
* Command-line based compiler execution

## Technologies Used

* Python 3
* tokenize module
* ast module
* Command Prompt / Terminal
* VS Code

## Compiler Phases

### 1. Lexical Analysis

Converts source code into tokens, lexemes, keywords, operators, literals, and identifiers.

### 2. Syntax Analysis

Builds and validates the program structure using Python AST representations and parse tree formatting.

### 3. Semantic Analysis

Checks semantic correctness including variable declarations, usage validation, and expression compatibility.

### 4. Symbol Table Management

Stores metadata of identifiers such as variable names, types, scope levels, offsets, widths, and assigned values.

### 5. Intermediate Code Generation

Transforms expressions and statements into Three Address Code (TAC) representation.

### 6. Code Optimization

Optimizes generated TAC using compiler optimization techniques to reduce redundancy and improve efficiency.

### 7. Error Handling

Displays meaningful compiler errors with exact line numbers and correction suggestions.

## Sample Supported Constructs

```python
x = 10
y = 20
z = x + y * 2

if z > 30:
    print(z)
```

## Project Objective

The objective of this project is to bridge theoretical compiler construction concepts with practical implementation by simulating the internal working of a real compiler using Python.

## Future Enhancements

* Loop handling (`while`, `for`)
* Function declaration and parameter checking
* GUI-based compiler interface
* Assembly / MIPS code generation
* PDF or HTML report export
* Advanced optimization techniques
* Live syntax highlighting

## Educational Value

This project demonstrates how compilers internally process source code through multiple transformation phases. It is particularly useful for students studying Compiler Construction, Programming Language Design, and Intermediate Code Generation.

## Author

Asma Qamar
BS Computer Science — Compiler Construction Project
