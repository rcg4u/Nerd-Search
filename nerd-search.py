import os
import re
import argparse
import sys
import subprocess
import importlib
import json
import configparser
from multiprocessing import Pool, cpu_count
import itertools
from pathlib import Path

# --- Core Libraries ---
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None
try:
    from tqdm import tqdm
except ImportError:
    tqdm = None
try:
    from colorama import init, Fore, Style
except ImportError:
    Fore, Style = None, None
try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None
try:
    from thefuzz import fuzz
except ImportError:
    fuzz = None

# --- Setup and Requirement Checking ---
REQUIRED_LIBRARIES = {
    "PyPDF2": "PyPDF2",
    "tqdm": "tqdm",
    "colorama": "colorama",
    "thefuzz": "thefuzz"
}

CONFIG_FILE_NAME = ".nerdsearchrc"
CONFIG_DEFAULTS = {
    'general': {
        'recursive': 'False',
        'whole_word': 'True',
        'case_sensitive': 'False',
        'context_lines': '1',
        'fuzzy_threshold': '80'
    },
    'output': {
        'quiet': 'False',
        'filter_no_results': 'False'
    }
}

def check_and_install_requirements():
    """Checks for required libraries and prompts to install them if missing."""
    missing_libs = []
    for lib_name, pip_name in REQUIRED_LIBRARIES.items():
        try:
            importlib.import_module(lib_name)
        except ImportError:
            missing_libs.append(pip_name)

    if not missing_libs:
        print("All required libraries are installed.")
        return True

    print("[!] The following required libraries are missing:")
    for lib in missing_libs:
        print(f" - {lib}")

    try:
        choice = input("Would you like to install them now? [y/N]: ").strip().lower()
        if choice == 'y':
            print("Attempting to install missing libraries...")
            for lib in missing_libs:
                try:
                    print(f" -> Installing {lib}...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
                    print(f" [+] {lib} installed successfully.")
                except subprocess.CalledProcessError:
                    print(f" [!] Failed to install {lib}. Please install it manually with 'pip install {lib}'.")
                    return False
            print("\nAll libraries installed. Please run the script again.")
            return False # Exit so the user can re-run
        else:
            print("Setup cancelled. Please install the missing libraries manually.")
            return False
    except KeyboardInterrupt:
        print("\nSetup cancelled.")
        return False

# --- Initialize colorama for cross-platform formatting ---
if Fore and Style:
    init(autoreset=True)
    ANSI_HIGHLIGHT_COLOR = Fore.RED + Style.BRIGHT
    ANSI_RESET_COLOR = Style.RESET_ALL
else:
    ANSI_HIGHLIGHT_COLOR = ''
    ANSI_RESET_COLOR = ''

# --- CSS and HTML for HTML export ---
HTML_STYLES = """
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; background-color: #f4f4f9; color: #333; margin: 20px; }
h1, h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
.container { max-width: 900px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
.file-section { margin-bottom: 25px; border: 1px solid #e0e0e0; padding: 15px; border-radius: 5px; }
.file-title { font-size: 1.5em; font-weight: bold; color: #2980b9; }
.file-title a { color: #2980b9; text-decoration: none; }
.file-title a:hover { text-decoration: underline; }
.file-summary { font-style: italic; color: #555; margin-top: 5px; }
.word-section { margin-top: 15px; }
.word-title { font-size: 1.2em; font-weight: bold; color: #c0392b; }
.match { margin-left: 20px; margin-bottom: 10px; }
.match-details { font-family: 'Courier New', Courier, monospace; background-color: #ecf0f1; padding: 10px; border-radius: 4px; white-space: pre-wrap; border-left: 4px solid #3498db; }
.highlight { background-color: #ffcccc; font-weight: bold; padding: 2px 4px; border-radius: 3px; }
.error, .skipped { color: #e74c3c; font-weight: bold; }
.quiet-list li { background-color: #eafaf1; padding: 8px; margin-bottom: 5px; list-style-type: none; border-radius: 4px; }
</style>
"""

# --- Utility Functions ---
def strip_ansi_codes(text):
    """Removes ANSI escape codes from a string."""
    return re.sub(r'\x1b$$[0-9;]*m', '', text)

def load_config():
    """Loads configuration from a .nerdsearchrc file."""
    config = configparser.ConfigParser()
    # Set defaults first
    for section, options in CONFIG_DEFAULTS.items():
        config.add_section(section)
        for key, value in options.items():
            config.set(section, key, value)

    config_path = Path.cwd() / CONFIG_FILE_NAME
    if not config_path.exists():
        # Create a default config file if it doesn't exist
        with open(config_path, 'w') as f:
            config.write(f)
        print(f"[+] Created default config file at '{config_path}'")
    else:
        config.read(config_path)
    return config

def find_documents(directory, recursive, exclude_patterns):
    """Generates a list of document paths, respecting exclusion and recursion options."""
    doc_files = []
    extensions = ('.pdf', '.txt', '.docx')
    if recursive:
        for root, _, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith(extensions):
                    file_path = os.path.join(root, filename)
                    if not any(re.search(pattern, filename, re.IGNORECASE) for pattern in exclude_patterns):
                        doc_files.append(file_path)
    else:
        for filename in os.listdir(directory):
            if filename.lower().endswith(extensions):
                file_path = os.path.join(directory, filename)
                if not any(re.search(pattern, filename, re.IGNORECASE) for pattern in exclude_patterns):
                    doc_files.append(file_path)
    return doc_files

def extract_text_from_file(file_path):
    """Extracts text from a PDF, TXT, or DOCX file."""
    try:
        if file_path.lower().endswith('.pdf'):
            if not PdfReader: raise ImportError("PyPDF2 is not installed.")
            reader = PdfReader(file_path)
            return "\n".join([page.extract_text() or "" for page in reader.pages])
        elif file_path.lower().endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        elif file_path.lower().endswith('.docx'):
            if not DocxDocument: raise ImportError("python-docx is not installed.")
            doc = DocxDocument(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"Could not read or process file. Reason: {e}"
    return "" # Should not be reached

# --- Core Search Logic (for multiprocessing) ---
def search_single_file(args_tuple):
    """Searches for words in a single file. This function is designed for multiprocessing."""
    file_path, search_words, case_sensitive, whole_word, use_regex, fuzzy, fuzzy_threshold, context_lines = args_tuple
    filename = os.path.basename(file_path)
    
    full_text = extract_text_from_file(file_path)
    if "Could not read or process file" in full_text:
        return {filename: full_text}

    if len(full_text.strip()) < 50:
        return {filename: {"_is_scanned_": ["This document appears to be empty or a scanned image and contains no extractable text."]}}
        
    lines = full_text.split('\n')
    
    search_patterns = {}
    flags = 0 if case_sensitive else re.IGNORECASE
    for word in search_words:
        if use_regex:
            try:
                search_patterns[word] = re.compile(word, flags=flags)
            except re.error as e:
                return {filename: f"Invalid regular expression for '{word}': {e}"}
        else:
            escaped_word = re.escape(word)
            pattern_str = rf'\b{escaped_word}\b' if whole_word else escaped_word
            search_patterns[word] = re.compile(pattern_str, flags=flags)

    found_in_file = {}
    for line_index, line in enumerate(lines):
        for word, pattern in search_patterns.items():
            matches = []
            if fuzzy:
                # For fuzzy search, we iterate through words in the line
                line_words = re.findall(r'\b\w+\b', line)
                for i, line_word in enumerate(line_words):
                    ratio = fuzz.ratio(word.lower(), line_word.lower())
                    if ratio >= fuzzy_threshold:
                        start_pos = line.find(line_word)
                        if start_pos != -1:
                            matches.append((start_pos, start_pos + len(line_word)))
            else:
                for match in pattern.finditer(line):
                    matches.append((match.start(), match.end()))

            if matches:
                if word not in found_in_file:
                    found_in_file[word] = []
                
                # Determine page number (approximate for non-PDFs)
                page_num = 1 # Default
                if PdfReader and file_path.lower().endswith('.pdf'):
                    try:
                        reader = PdfReader(file_path)
                        lines_per_page = len(full_text.split('\n')) / len(reader.pages)
                        page_num = int(line_index / lines_per_page) + 1
                    except: # Fallback if PDF reading fails
                        page_num = 1

                # Get context
                start_idx = max(0, line_index - context_lines)
                end_idx = min(len(lines), line_index + context_lines + 1)
                context = lines[start_idx:end_idx]
                
                # Highlight the match line
                match_line_index = line_index - start_idx
                context[match_line_index] = f">>> {context[match_line_index]}"
                
                found_in_file[word].append((page_num, line_index + 1, "\n".join(context)))

    return {filename: found_in_file if found_in_file else None}

# --- Output Formatters ---
def highlight_word_in_text(text, word, use_regex, for_html=False):
    """Highlights a word in text, either with ANSI codes or HTML span."""
    if use_regex:
        return text
    escaped_word = re.escape(word)
    if for_html:
        return re.sub(rf'({escaped_word})', r'<span class="highlight">\1</span>', text, flags=re.IGNORECASE)
    else:
        return re.sub(rf'({escaped_word})', lambda match: f"{ANSI_HIGHLIGHT_COLOR}{match.group(1)}{ANSI_RESET_COLOR}", text, flags=re.IGNORECASE)

def format_results_for_console(results, search_words, quiet_mode, use_regex, filter_no_results):
    """Formats results for console output with ANSI highlighting."""
    if quiet_mode:
        output_lines = [filename for filename, data in results.items() if data and not isinstance(data, str) and "_is_scanned_" not in data]
        return "\n".join(output_lines)

    output_lines = ["===== SEARCH RESULTS ====="]
    if not any(results.values()):
        output_lines.append("No matching words found in any files.")
    else:
        for filename, file_data in results.items():
            if filter_no_results and (file_data is None or isinstance(file_data, str) or "_is_scanned_" in file_data):
                continue
            
            output_lines.append(f"\n📄 Found in: {filename}")
            
            if isinstance(file_data, str):
                output_lines.append(f" [!] {file_data}")
                continue
            if "_is_scanned_" in file_data:
                output_lines.append(f" [!] {file_data['_is_scanned_'][0]}")
                continue
            if not file_data:
                continue

            total_occurrences = sum(len(matches) for matches in file_data.values())
            unique_words_found = len(file_data)
            output_lines.append(f" -> Total: {total_occurrences} occurrences of {unique_words_found} unique words.")

            for word in search_words:
                if word in file_data:
                    matches = file_data[word]
                    count = len(matches)
                    output_lines.append(f"\n - Word: '{word}' (Found {count} times)")
                    # Use set to remove duplicate context blocks if a word appears twice in one context
                    for page, line, context in sorted(list(set(matches)), key=lambda x: (x[0], x[1])):
                        output_lines.append(f" > Page {page}, Line {line}:")
                        highlighted_context = highlight_word_in_text(context, word, use_regex, for_html=False)
                        output_lines.append(f" {highlighted_context}")
                        output_lines.append("-" * 20)
    output_lines.append("========================\n")
    return "\n".join(output_lines)

def format_results_for_html(results, search_words, quiet_mode, use_regex, filter_no_results, base_url):
    """Formats results for HTML output with CSS highlighting."""
    html_parts = [f"<html><head><title>Nerd-Search Results</title>{HTML_STYLES}</head><body>"]
    html_parts.append('<div class="container"><h1>Nerd-Search Results</h1>')

    if not any(results.values()):
        html_parts.append("<p>No matching words found in any files.</p>")
    else:
        for filename, file_data in results.items():
            if filter_no_results and (file_data is None or isinstance(file_data, str) or "_is_scanned_" in file_data):
                continue
            
            html_parts.append('<div class="file-section">')
            if isinstance(file_data, str) or not file_data or "_is_scanned_" in file_data:
                status = "error" if isinstance(file_data, str) else "skipped"
                message = file_data if isinstance(file_data, str) else file_data.get("_is_scanned_", ["No matches found."])[0]
                html_parts.append(f'<p class="{status}">File: {filename} - {message}</p>')
                html_parts.append('</div>')
                continue

            if base_url:
                if not base_url.endswith('/'): base_url += '/'
                file_url = f'{base_url}{filename}'
                html_parts.append(f'<div class="file-title">📄 <a href="{file_url}" target="_blank">{filename}</a></div>')
            else:
                html_parts.append(f'<div class="file-title">📄 {filename}</div>')

            total_occurrences = sum(len(matches) for matches in file_data.values())
            unique_words_found = len(file_data)
            html_parts.append(f'<div class="file-summary">Total: {total_occurrences} occurrences of {unique_words_found} unique words.</div>')

            for word in search_words:
                if word in file_data:
                    matches = file_data[word]
                    count = len(matches)
                    html_parts.append(f'<div class="word-section">')
                    html_parts.append(f'<div class="word-title">Word: \'{word}\' (Found {count} times)</div>')
                    for page, line, context in sorted(list(set(matches)), key=lambda x: (x[0], x[1])):
                        html_parts.append('<div class="match">')
                        html_parts.append(f'<strong>Page {page}, Line {line}:</strong>')
                        highlighted_context = highlight_word_in_text(context, word, use_regex, for_html=True)
                        html_parts.append(f'<div class="match-details">{highlighted_context}</div>')
                        html_parts.append('</div>')
                    html_parts.append('</div>')
            html_parts.append('</div>')
    html_parts.append('</div></body></html>')
    return "".join(html_parts)

def format_results_for_json(results):
    """Formats results as a JSON string, ensuring all data is serializable."""
    serializable_results = {}
    for filename, data in results.items():
        if isinstance(data, str):
            serializable_results[filename] = {"error": data}
        elif isinstance(data, dict) and "_is_scanned_" in data:
            serializable_results[filename] = {"skipped": data["_is_scanned_"][0]}
        elif data:
            # Convert tuples to lists for JSON compatibility
            serializable_data = {}
            for word, matches in data.items():
                serializable_data[word] = [list(match) for match in matches]
            serializable_results[filename] = serializable_data
        else:
            serializable_results[filename] = None # Represents no matches
            
    return json.dumps(serializable_results, indent=4)


# --- Main Execution ---
def run_search(target_path, args):
    """Main function to orchestrate the search using multiprocessing."""
    doc_files_to_process = []
    if os.path.isfile(target_path):
        if target_path.lower().endswith(('.pdf', '.txt', '.docx')):
            doc_files_to_process.append(target_path)
        else:
            return f"Error: The file '{target_path}' is not a supported format."
    elif os.path.isdir(target_path):
        doc_files_to_process = find_documents(target_path, args.recursive, args.exclude)
        if not doc_files_to_process:
            return f"No supported documents found in the folder: {target_path}"
    else:
        return f"Error: The path '{target_path}' does not exist or is not a valid file/directory."

    if not doc_files_to_process:
        return "No documents found to search."

    # --- MODIFIED WORKER LOGIC ---
    cpu_cores = cpu_count()
    # Determine the number of workers to use
    if args.workers is None:
        # No --workers flag provided, use the optimal number (CPU cores)
        num_workers = cpu_cores
        print(f"[Info] No --workers specified. Using {num_workers} workers (your CPU's core count) for maximum speed.")
    else:
        # --workers flag provided, validate and use it
        if args.workers <= 0:
            return f"Error: --workers must be a positive integer. You provided {args.workers}."
        num_workers = args.workers
        if num_workers > cpu_cores:
            print(f"[Warning] You specified {num_workers} workers, but your system only has {cpu_cores} CPU cores. Using more than {cpu_cores} may slow down the search.")
    
    # Prepare arguments for the multiprocessing pool
    search_args = [
        (file_path, args.words, args.case_sensitive, args.whole_word, args.regex, args.fuzzy, args.fuzzy_threshold, args.context_lines)
        for file_path in doc_files_to_process
    ]

    final_results = {}
    
    print(f"Processing {len(doc_files_to_process)} files using {num_workers} worker(s)...")

    with Pool(processes=num_workers) as pool:
        # Use tqdm to show progress over the imap_unordered results
        results_iterator = pool.imap_unordered(search_single_file, search_args)
        if tqdm:
            results_iterator = tqdm(results_iterator, total=len(doc_files_to_process), desc="Searching Files", unit="file")
        
        for result_dict in results_iterator:
            final_results.update(result_dict)
            
    return final_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Nerd-Search: Find words in documents (PDF, TXT, DOCX) with context and advanced options.",
        epilog="Examples:\n" \
        " python nerd-search.py /path/to/folder \"Epstein\" \"Trump\" --html-output results.html\n" \
        " python nerd-search.py /path/to/file.pdf \"yacht\" --case-sensitive\n" \
        " python nerd-search.py /path/to/logs --recursive --regex \"error \\d{4}\""
    )

    # Special action argument
    parser.add_argument("--setup", action='store_true', help="Check and install required libraries.")
    
    parser.add_argument("path", nargs='?', help="The path to a document file or a folder.", default=None)
    parser.add_argument("words", nargs='*', help="One or more words to search for.", default=None)

    # Search options
    parser.add_argument("--case-sensitive", action='store_true', help="Make the search case-sensitive.")
    parser.add_argument("--whole-word", action='store_true', help="Match whole words only.")
    parser.add_argument("--regex", action='store_true', help="Treat search words as regular expressions.")
    parser.add_argument("--fuzzy", action='store_true', help="Enable fuzzy searching (approximate matches).")
    parser.add_argument("--fuzzy-threshold", type=int, default=80, help="Threshold for fuzzy matching (0-100, default: 80).")

    # File handling options
    parser.add_argument("--recursive", action='store_true', help="Search recursively in subdirectories.")
    parser.add_argument("--exclude", nargs='*', default=[], help="Exclude files matching these regex patterns.")

    # Output options
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("-o", "--output", metavar="FILE", help="Save results to a plain text file.")
    output_group.add_argument("--html-output", metavar="FILE", help="Save results to a styled HTML file.")
    output_group.add_argument("--json-output", metavar="FILE", help="Save results to a JSON file.")

    parser.add_argument("--base-url", metavar="URL", help="A base URL to create hyperlinks in HTML output.")
    parser.add_argument("-q", "--quiet", action='store_true', help="Quiet mode. Only show filenames with matches.")
    parser.add_argument("--filter-no-results", action='store_true', help="Only show files that contain at least one match.")
    parser.add_argument("--context-lines", type=int, default=1, help="Number of context lines before/after a match (default: 1).")
    
    # --- ADD THIS NEW ARGUMENT ---
    parser.add_argument(
        "--workers", 
        type=int, 
        default=None, 
        help="Set the number of parallel worker processes for searching. Defaults to the number of CPU cores for maximum speed."
    )

    args = parser.parse_args()

    # Handle the --setup flag first
    if args.setup:
        check_and_install_requirements()
        sys.exit(0)

    # Load config and apply defaults
    config = load_config()
    if not args.case_sensitive and config.getboolean('general', 'case_sensitive'): args.case_sensitive = True
    if not args.whole_word and config.getboolean('general', 'whole_word'): args.whole_word = True
    if not args.recursive and config.getboolean('general', 'recursive'): args.recursive = True
    if not args.quiet and config.getboolean('output', 'quiet'): args.quiet = True
    if not args.filter_no_results and config.getboolean('output', 'filter_no_results'): args.filter_no_results = True
    if args.context_lines == 1: args.context_lines = config.getint('general', 'context_lines')
    if args.fuzzy_threshold == 80: args.fuzzy_threshold = config.getint('general', 'fuzzy_threshold')

    # Validate normal arguments
    if not args.path or not args.words:
        print("\n[!] Missing path or search words.", file=sys.stderr)
        parser.print_help()
        print("\n[!] Hint: If this is your first time, run 'python nerd-search.py --setup' to install dependencies.")
        sys.exit(1)

    # Check for requirements before running the main search
    if not check_and_install_requirements():
        sys.exit(1)
        
    print(f"Searching: {args.path}\n")
    results_data = run_search(args.path, args)

    # --- Output Handling ---
    try:
        if args.json_output:
            json_string = format_results_for_json(results_data)
            with open(args.json_output, 'w', encoding='utf-8') as f:
                f.write(json_string)
            print(f"\nResults successfully saved to {args.json_output}")
        elif args.html_output:
            html_string = format_results_for_html(results_data, args.words, args.quiet, args.regex, args.filter_no_results, args.base_url)
            with open(args.html_output, 'w', encoding='utf-8') as f:
                f.write(html_string)
            print(f"\nResults successfully saved to {args.html_output}")
        elif args.output:
            text_string = format_results_for_console(results_data, args.words, args.quiet, args.regex, args.filter_no_results)
            clean_text = strip_ansi_codes(text_string)
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(clean_text)
            print(f"\nResults successfully saved to {args.output}")
        else:
            console_string = format_results_for_console(results_data, args.words, args.quiet, args.regex, args.filter_no_results)
            print(console_string)
    except IOError as e:
        print(f"\n[!] Error writing to output file: {e}", file=sys.stderr)