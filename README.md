# Teditor

**Teditor** is a command line text editor similar to *nano*, built with Python 🐍

### **NOTE**: This project is Work In Progress, expect bugs.

## 🗂️ Supported Languages

- C
- C++
- C#
- Python
- Brainfuck
- CSS
- HTML
- JavaScript
- Go
- Java
- JSON
- Kotlin
- Rust
- Bash
- Vim

## 📝 To-do

- ✅ Editing Text Files  
- ✅ Saving and Opening Files  
- ✅ Syntax Highlighting  
- 🕒 Themes *(soon...)*  
- 🕒 Mouse Support *(soon...)*  
- 🕒 Searching *(soon...)*  
- 🕒 Goto *(soon...)*

## 🖼️ Screenshots

![Teditor Screenshot](https://i.imgur.com/TI3KFO9.png)

## Installation

### NOTE: Make sure that you have $HOME/.local/bin in your $PATH variable.
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Clone the project

```bash
git clone https://github.com/hamajj/teditor
cd teditor
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Install via pip
```bash
pip install -e .
```

## Usage 

### Opening a file
```bash
teditor <filename>
```

### Keybinds
- Ctrl + S ---> Save the current edited file
- Ctrl + Q ---> Quit the editor

