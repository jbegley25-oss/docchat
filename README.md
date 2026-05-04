# docchat

An AI-powered command-line agent that chats with your files and autonomously writes code in your git repo.

![Tests](https://github.com/jbegley25-oss/docchat/actions/workflows/tests.yml/badge.svg)
![flake8](https://github.com/jbegley25-oss/docchat/actions/workflows/flake8.yml/badge.svg)
![Integration](https://github.com/jbegley25-oss/docchat/actions/workflows/integration.yml/badge.svg)

## Installation

```bash
pip install .
export GROQ_API_KEY=your_key_here
```

## Usage

```bash
chat                            # interactive REPL
chat 'what is this project?'    # single message
chat --debug 'list files'       # show tool calls
chat --provider anthropic       # use Claude via OpenRouter
chat --tts                      # speak responses aloud
chat --stt                      # voice input (press Enter to record/stop)
chat --wiggum                   # auto-retry until doctests pass
```

## Tools

| Slash command | What it does |
|---|---|
| `/ls [path]` | List directory |
| `/cat <file>` | Read a file |
| `/grep <pattern> <path>` | Search files |
| `/calculate <expr>` | Evaluate math |
| `/compact` | Summarize chat history |
| `/load_image <file>` | Load an image for vision |
| `/doctests <file>` | Run doctests on a Python file |
| `/write_file` | Write a file and commit it |
| `/rm <path>` | Delete files and commit |
| `/pip_install <pkg>` | Install a Python package |

## Examples

### Chatting with the ebay scraper project

This example shows docchat explaining a project by reading its files:

```
$ cd test_projects/ebay-scraper
$ chat
chat> what is this project about?
This project is an eBay web scraper that collects product listings and prices.
chat> /ls .
README.md
scraper.py
requirements.txt
```

### Chatting with the markdown compiler project

This example shows docchat answering questions about code structure:

```
$ cd test_projects/markdown-compiler
$ chat
chat> does this project use regular expressions?
Yes, I found uses of the re module in the Python files.
chat> /grep import *.py
import re
import sys
```

### Chatting with the personal webpage project

This example shows docchat describing a web project:

```
$ cd test_projects/webpage
$ chat
chat> what kind of website is this?
Based on the HTML files, this appears to be a personal portfolio website.
```

### Agent autonomously creating files (Project 4)

This example shows the agent creating code and committing it to git:

```
$ ls -a
.git  AGENTS.md  README.md
$ git log --oneline
c21103f (HEAD -> project04) init commit
$ chat
chat> create a python hello world script
Created hello_world.py with a simple Hello World program.
chat> ^C
$ ls -a
.git  AGENTS.md  README.md  hello_world.py
$ git log --oneline
3cfb0a6 (HEAD -> project04) [docchat] create hello world python script
c21103f init commit
```

### Ralph Wiggum loop auto-fixing doctests

This example shows the `--wiggum` flag making the agent retry until tests pass:

```
$ chat --wiggum
chat> write a calculate.py with a function that adds two numbers and has doctests
[tool] /write_file calculate.py ...
--- doctests: calculate.py ---
1 items passed all tests; 1 tests in calculate.add
chat> ^C
```
