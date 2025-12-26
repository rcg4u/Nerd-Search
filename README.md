# nerd-search

**Summary:** `nerd-search` is a powerful and versatile Python command-line tool for searching specific words, phrases, or regular expressions across a variety of document formats. It leverages parallel processing for high-speed searches and provides detailed, context-rich results with highlighted matches and occurrence counts.

---

## Features

- **🚀 High-Performance Search:**
    - **Parallel Processing:** Utilizes multiple CPU cores to dramatically speed up searches across many files. The number of workers is automatically optimized for your system but can be manually controlled with the `--workers` flag.

- **🔍 Advanced Search Capabilities:**
    - Search for single or multiple keywords/phrases.
    - **Case-sensitive search** with the `--case-sensitive` flag.
    - **Whole-word matching** (default) or **substring matching** with `--no-whole-word`.
    - Full **regular expression (regex)** support with the `--regex` flag for complex pattern matching.
    - **Fuzzy Searching:** Find approximate matches to handle typos or OCR errors using the `--fuzzy` flag.

- **📄 Multi-Format Support:**
    - Seamlessly search inside **PDF**, **plain text (.txt)**, and **Microsoft Word (.docx)** documents.
    - Gracefully handles **scanned/image-based PDFs** by detecting and reporting them as having no extractable text.

- **📁 Flexible File Handling:**
    - Search a single document file or all supported documents in a specified directory.
    - **Recursive directory search** with the `--recursive` flag to scan subfolders.
    - **File exclusion patterns** to skip files matching specific names (e.g., `--exclude "*glossary*"`).

- **🎨 Rich and Formatted Output:**
    - Reports the exact **page and line number** for each match.
    - Provides **customizable context lines** (before and after) for each match, controlled by `--context-lines`.
    - **Highlighted search terms** in console output for easy visibility.
    - Displays a **count of occurrences** for each word found.
    - **Quiet mode (`-q`)** to only list filenames that contain matches.
    - **Filter mode (`--filter-no-results`)** to hide files that have no matches from the output.

- **💾 Export Options:**
    - Save results to a **plain text file** with `-o` or `--output`.
    - Export results to a **styled HTML file** with `--html-output`, perfect for sharing and archiving. Includes clickable links if `--base-url` is provided.
    - Export results to a **machine-readable JSON file** with `--json-output`.

- **⚙️ User Experience & Configuration:**
    - **File-based configuration:** Automatically creates a `.nerdsearchrc` file to store your default settings, so you don't have to repeat common arguments.
    - **Real-time progress bar** (`tqdm`) for feedback during large searches.
    - **Automatic dependency checking** and a `--setup` flag for easy installation of required libraries.

---

## Requirements

- Python 3.6+
- PyPDF2 (`pip install PyPDF2`)
- tqdm (`pip install tqdm`)
- colorama (`pip install colorama`)
- python-docx (`pip install python-docx`)
- thefuzz (`pip install thefuzz`)

> **Easy Setup:** Run `python nerd-search.py --setup` to automatically check for and install all missing dependencies.

---

## Usage

### First-Time Setup

If you're running the script for the first time, you can use the built-in setup command to install all necessary libraries:

```bash
python nerd-search.py --setup
```

The script will prompt you to install any missing dependencies. It will also create a default `.nerdsearchrc` configuration file in your current directory.

### General Syntax

```bash
python nerd-search.py <path> <word1> [word2] ... [options]
```

- `<path>`: The path to a document file (PDF, TXT, DOCX) or a folder containing them.
- `<word1> [word2] ...`: One or more words or phrases to search for (use quotes for phrases).

### Command-Line Options

#### Search Options
- `--case-sensitive`: Make the search case-sensitive.
- `--whole-word`: Match whole words only (default: True). Use `--no-whole-word` to find substrings.
- `--regex`: Treat search words as regular expressions.
- `--fuzzy`: Enable fuzzy searching for approximate matches.
- `--fuzzy-threshold N`: Set the sensitivity for fuzzy matching (0-100, default: 80).

#### File Handling Options
- `--recursive`: Search recursively in subdirectories.
- `--exclude [PATTERN ...]`: Exclude files matching these regex patterns.

#### Performance Options
- `--workers N`: Set the number of parallel worker processes. Defaults to your CPU's core count for maximum speed.

#### Output Options
- `-o <FILE>`, `--output <FILE>`: Save results to a plain text file.
- `--html-output <FILE>`: Save results to a styled HTML file.
- `--json-output <FILE>`: Save results to a JSON file.
- `--base-url <URL>`: A base URL to create hyperlinks for each file in the HTML output.
- `-q`, `--quiet`: Quiet mode. Only show filenames with matches.
- `--filter-no-results`: Only show files that contain at least one match.
- `--context-lines N`: Number of context lines before/after a match (default: 1).

### Examples

#### Basic Search
Search for two words in all supported documents within a folder:
```bash
python nerd-search.py ./documents "Epstein" "Trump"
```

#### High-Performance Search
Use 4 parallel workers to recursively search a large directory structure:
```bash
python nerd-search.py ./large_archive "keyword" --recursive --workers 4
```

#### Advanced Search
Perform a case-sensitive, recursive search for a phrase, excluding any files with "draft" in the name:
```bash
python nerd-search.py ./logs "Project Apollo" --case-sensitive --recursive --exclude "*draft*"
```

#### Fuzzy Search
Find words that are spelled similarly to "license" (e.g., "licence"):
```bash
python nerd-search.py ./contracts --fuzzy "license"
```

#### Exporting Results
Save a highlighted HTML report with clickable links:
```bash
python nerd-search.py ./legal_docs "liability" --html-output liability_report.html --base-url https://docs.example.com/
```

Save a machine-readable JSON report:
```bash
python nerd-search.py ./research.pdf "AI" --json-output ai_findings.json
```

#### Quiet Mode
Quickly find which files in a directory contain the word "confidential":
```bash
python nerd-search.py ./archive "confidential" -q
```

---

## Change Log

### 2025-12-26 (Major Feature Update)
- **Added Parallel Processing:** Implemented multiprocessing to use multiple CPU cores, drastically improving search speed. Added `--workers` flag for manual control.
- **Added Multi-Format Support:** Extended search capabilities to include plain text (`.txt`) and Microsoft Word (`.docx`) files.
- **Added Configuration File:** Introduced `.nerdsearchrc` for storing persistent default settings.
- **Added JSON Output:** Added `--json-output` option for machine-readable results.
- **Added Fuzzy Searching:** Implemented `--fuzzy` and `--fuzzy-threshold` flags for approximate string matching.
- **Added Configurable Context:** Added `--context-lines` to allow user control over context display.
- **Added HTML Hyperlinks:** The `--base-url` flag now creates clickable links in HTML output.
- **Added `--filter-no-results` flag:** Hides files with no matches from the output for cleaner reports.
- **Refactored Core Logic:** Restructured the search and file processing to be modular and support the new multiprocessing architecture.

### 2025-12-25
- **Added `--setup` flag** for automatic dependency checking and installation.
- **Added HTML export** with `--html-output` for styled, shareable reports.
- **Added progress bar** (`tqdm`) that updates based on pages processed.
- **Added case-sensitive search** (`--case-sensitive`).
- **Added whole-word toggle** (`--whole-word` / `--no-whole-word`).
- **Added regular expression support** (`--regex`).
- **Added recursive directory search** (`--recursive`).
- **Added file exclusion patterns** (`--exclude`).
- **Added quiet mode** (`-q`).
- **Added occurrence counts** for each searched word per file.
- **Refactored code** for better modularity and cross-platform compatibility.

### 2025-12-24
- Added support for searching both a single PDF file and all PDFs in a folder.
- Improved error handling and output formatting.
- Updated usage instructions and examples.
- Modularized code for easier maintenance.
- Now displays the exact line(s) where the search text is found in the summary output.
- Detects and reports scanned PDFs with no extractable text.
- Performance improved by pre-compiling search patterns.

---

## License

MIT License