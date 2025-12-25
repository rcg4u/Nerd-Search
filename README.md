# nerd-search

**Summary:** `nerd-search` is a powerful and versatile Python command-line tool for searching specific words, phrases, or regular expressions in PDF files. It can search a single file or recursively traverse entire directories, providing detailed, context-rich results with highlighted matches and occurrence counts.

---

## Features

-   **Advanced Search Capabilities:**
    -   Search for single or multiple keywords/phrases.
    -   **Case-sensitive search** with the `--case-sensitive` flag.
    -   **Whole-word matching** (default) or **substring matching** with `--no-whole-word`.
    -   Full **regular expression (regex)** support with the `--regex` flag for complex pattern matching.
-   **Flexible File Handling:**
    -   Search a single PDF file or all PDFs in a specified directory.
    -   **Recursive directory search** with the `--recursive` flag to scan subfolders.
    -   **File exclusion patterns** to skip files matching specific names (e.g., `--exclude "*glossary*"`).
    -   Gracefully handles **scanned PDFs** by detecting and reporting them as having no extractable text.
-   **Rich and Formatted Output:**
    -   Reports the exact **page and line number** for each match.
    -   Provides **context lines** (before and after) for each match.
    -   **Highlighted search terms** in console output for easy visibility.
    -   Displays a **count of occurrences** for each word found.
    -   **Quiet mode (`-q`)** to only list filenames that contain matches.
-   **Export Options:**
    -   Save results to a **plain text file** with `-o` or `--output`.
    -   Export results to a **styled HTML file** with `--html-output`, perfect for sharing and archiving.
-   **User Experience:**
    -   **Page-based progress bar** (`tqdm`) for real-time feedback during large searches.
    -   **Automatic dependency checking** and a `--setup` flag for easy installation of required libraries.
    -   **Parallel processing** (in previous versions, now sequential for page-based progress accuracy) for performance.

---

## Requirements

-   Python 3.6+
-   PyPDF2 (`pip install PyPDF2`)
-   tqdm (`pip install tqdm`)
-   colorama (`pip install colorama`)

> **Easy Setup:** Run `python nerd-search.py --setup` to automatically check for and install missing dependencies.

---

## Usage

### First-Time Setup

If you're running the script for the first time, you can use the built-in setup command to install all necessary libraries:

```bash
python nerd-search.py --setup
```

The script will prompt you to install any missing dependencies.

### General Syntax

```bash
python nerd-search.py <path> <word1> [word2] ... [options]
```

-   `<path>`: The path to a PDF file or a folder containing PDF files.
-   `<word1> [word2] ...`: One or more words or phrases to search for (use quotes for phrases).

### Command-Line Options

#### Search Options
-   `--case-sensitive`: Make the search case-sensitive.
-   `--whole-word`: Match whole words only (default: True). Use `--no-whole-word` to find substrings.
-   `--regex`: Treat search words as regular expressions.

#### File Handling Options
-   `--recursive`: Search recursively in subdirectories.
-   `--exclude [PATTERN ...]`: Exclude files matching these regex patterns.

#### Output Options
-   `-o <FILE>`, `--output <FILE>`: Save results to a plain text file.
-   `--html-output <FILE>`: Save results to a styled HTML file.
-   `-q`, `--quiet`: Quiet mode. Only show filenames with matches.

### Examples

#### Basic Search
Search for two words in all PDFs within a folder:
```bash
python nerd-search.py ./documents "Epstein" "Trump"
```

#### Advanced Search
Perform a case-sensitive, recursive search for a phrase, excluding any files with "draft" in the name:
```bash
python nerd-search.py ./logs "Project Apollo" --case-sensitive --recursive --exclude "*draft*"
```

#### Regular Expression Search
Find any instance of the word "error" followed by a 4-digit number:
```bash
python nerd-search.py ./server_logs --regex "error \d{4}"
```

#### Exporting Results
Save a highlighted HTML report of a search:
```bash
python nerd-search.py ./legal_docs "liability" --html-output liability_report.html
```

Save a clean text report to a file:
```bash
python nerd-search.py ./research.pdf "AI" --output ai_findings.txt
```

#### Quiet Mode
Quickly find which files in a directory contain the word "confidential":
```bash
python nerd-search.py ./archive "confidential" -q
```

---

## Change Log

### 2025-12-25 (Major Feature Update)
-   **Added `--setup` flag** for automatic dependency checking and installation.
-   **Added HTML export** with `--html-output` for styled, shareable reports.
-   **Added progress bar** (`tqdm`) that updates based on pages processed.
-   **Added case-sensitive search** (`--case-sensitive`).
-   **Added whole-word toggle** (`--whole-word` / `--no-whole-word`).
-   **Added regular expression support** (`--regex`).
-   **Added recursive directory search** (`--recursive`).
-   **Added file exclusion patterns** (`--exclude`).
-   **Added quiet mode** (`-q`).
-   **Added occurrence counts** for each searched word per file.
-   **Refactored code** for better modularity and cross-platform compatibility.

### 2025-12-24
-   Added support for searching both a single PDF file and all PDFs in a folder.
-   Improved error handling and output formatting.
-   Updated usage instructions and examples.
-   Modularized code for easier maintenance.
-   Now displays the exact line(s) where the search text is found in the summary output.
-   Detects and reports scanned PDFs with no extractable text.
-   Performance improved by pre-compiling search patterns.

---

## License

MIT License