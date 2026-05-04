# docchat

An AI-powered command-line agent that lets you ask questions about the files in your current directory.

![Tests](https://github.com/jbegley25-oss/docchat/actions/workflows/tests.yml/badge.svg)
![flake8](https://github.com/jbegley25-oss/docchat/actions/workflows/flake8.yml/badge.svg)
![Integration](https://github.com/jbegley25-oss/docchat/actions/workflows/integration.yml/badge.svg)

## Installation

```bash
pip install .
```

Set your Groq API key:

```bash
export GROQ_API_KEY=your_key_here
```

## Usage

```bash
chat                        # interactive REPL
chat 'what is this project?'  # single message
chat --debug 'list files'   # show tool calls
```

## Examples

### Chatting with the ebay scraper project

This example shows how docchat can explain what a project does by reading its files:

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

This example shows how docchat can answer questions about code structure:

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

This example shows how docchat can describe a web project:

```
$ cd test_projects/webpage
$ chat
chat> what kind of website is this?
Based on the HTML files, this appears to be a personal portfolio website.
chat> /cat index.html
<!DOCTYPE html>
...
```
