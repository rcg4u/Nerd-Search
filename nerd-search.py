import os
import re
import argparse
import sys
import subprocess
import importlib
from PyPDF2 import PdfReader
import colorama
from tqdm import tqdm

# --- Setup and Requirement Checking ---
REQUIRED_LIBRARIES = {
    "PyPDF2": "PyPDF2",
    "tqdm": "tqdm",
    "colorama": "colorama"
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

# --- Initialize colorama for cross-platform formatting (for console output) ---
# We do this after the setup check, in case colorama was just installed.
try:
    import colorama
    colorama.init(autoreset=True)
    ANSI_HIGHLIGHT_COLOR = '\033[41m' # Red Background Highlight
    ANSI_RESET_COLOR = '\033[0m'
except ImportError:
    # Fallback if colorama is somehow still not imported
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

def count_total_pages(pdf_files):
    """Counts the total number of pages across all PDF files to be processed."""
    total_pages = 0
    print("Counting pages for progress bar...")
    try:
        from tqdm import tqdm
        for file_path in tqdm(pdf_files, desc="Scanning files"):
            try:
                reader = PdfReader(file_path)
                total_pages += len(reader.pages)
            except Exception:
                continue
    except ImportError:
        print("tqdm not found, cannot show progress for this step.")
        for file_path in pdf_files:
            try:
                reader = PdfReader(file_path)
                total_pages += len(reader.pages)
            except Exception:
                continue
    return total_pages

def find_pdf_files(directory, recursive, exclude_patterns):
    """Generates a list of PDF file paths, respecting exclusion and recursion options."""
    pdf_files = []
    if recursive:
        for root, _, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith('.pdf'):
                    file_path = os.path.join(root, filename)
                    if not any(re.search(pattern, filename) for pattern in exclude_patterns):
                        pdf_files.append(file_path)
    else:
        for filename in os.listdir(directory):
            if filename.lower().endswith('.pdf'):
                file_path = os.path.join(directory, filename)
                if not any(re.search(pattern, filename) for pattern in exclude_patterns):
                    pdf_files.append(file_path)
    return pdf_files

# --- Core Search Logic ---
def search_in_file(file_path, search_words, case_sensitive, whole_word, use_regex, pbar):
    """Searches for words in a single PDF file and updates the progress bar."""
    try:
        reader = PdfReader(file_path)
        if not reader.pages:
            return None
        
        first_page_text = reader.pages[0].extract_text() or ""
        if len(first_page_text.strip()) < 50:
            pbar.update(len(reader.pages))
            return {"_is_scanned_": ["This PDF appears to be a scanned image and contains no extractable text."]}

        search_patterns = {}
        flags = 0 if case_sensitive else re.IGNORECASE
        for word in search_words:
            if use_regex:
                search_patterns[word] = re.compile(word, flags=flags)
            else:
                escaped_word = re.escape(word)
                pattern_str = rf'\b{escaped_word}\b' if whole_word else escaped_word
                search_patterns[word] = re.compile(pattern_str, flags=flags)

        found_in_file = {}
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            lines = text.split('\n')
            for line_index, line in enumerate(lines):
                for word, pattern in search_patterns.items():
                    if pattern.search(line):
                        if word not in found_in_file:
                            found_in_file[word] = []
                        context_before = lines[line_index - 1].strip() if line_index > 0 else ""
                        context_line = line.strip()
                        context_after = lines[line_index + 1].strip() if line_index < len(lines) - 1 else ""
                        found_in_file[word].append(
                            (page_num + 1, line_index + 1, context_before, context_line, context_after)
                        )
        pbar.update(1)
        return found_in_file if found_in_file else None
    except Exception as e:
        try:
            reader = PdfReader(file_path)
            pbar.update(len(reader.pages))
        except:
            pbar.update(1)
        return f"Could not read or process file. Reason: {e}"

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
        output_lines = [filename for filename, data in results.items() if data and not isinstance(data, str)]
        return "\n".join(output_lines)

    output_lines = ["===== SEARCH RESULTS ====="]
    if not results:
        output_lines.append("No matching words found in any files.")
    else:
        for filename, file_data in results.items():
            if filter_no_results and (file_data is None or isinstance(file_data, str)):
                continue

            if isinstance(file_data, str):
                output_lines.append(f"\n[!] Error in {filename}: {file_data}")
                continue
            
            # This block is now only reached if file_data is not None and not a string,
            # meaning it must be a dictionary with matches.
            output_lines.append(f"\n📄 Found in: {filename}")
            
            # Only show the summary line if the filter is NOT active.
            if not filter_no_results:
                total_occurrences = sum(len(matches) for matches in file_data.values())
                unique_words_found = len(file_data)
                output_lines.append(f" -> Total: {total_occurrences} occurrences of {unique_words_found} unique words.")
            
            for word in search_words:
                if word in file_data:
                    matches = file_data[word]
                    count = len(matches)
                    output_lines.append(f"\n - Word: '{word}' (Found {count} times)")
                    sorted_matches = sorted(list(set(matches)), key=lambda x: (x[0], x[1]))
                    for page, line, before, match_line, after in sorted_matches:
                        output_lines.append(f" > Page {page}, Line {line}:")
                        if before: output_lines.append(f"  {before}")
                        highlighted_line = highlight_word_in_text(match_line, word, use_regex, for_html=False)
                        output_lines.append(f" >>> {highlighted_line}")
                        if after: output_lines.append(f"  {after}")
                        output_lines.append("-" * 20)
    
    output_lines.append("========================\n")
    return "\n".join(output_lines)

def format_results_for_html(results, search_words, quiet_mode, use_regex, filter_no_results, base_url):
    """Formats results for HTML output with CSS highlighting. All tags are properly closed."""
    html_parts = [f"<html><head><title>Nerd-Search Results</title>{HTML_STYLES}</head><body>"]
    html_parts.append('<div class="container"><h1>Nerd-Search Results</h1>')
    
    if not results:
        html_parts.append("<p>No matching words found in any files.</p>")
    else:
        for filename, file_data in results.items():
            if filter_no_results and (file_data is None or isinstance(file_data, str)):
                continue

            html_parts.append('<div class="file-section">')
            if isinstance(file_data, str) or not file_data:
                status = "error" if isinstance(file_data, str) else "skipped"
                message = file_data if isinstance(file_data, str) else "No matches found."
                html_parts.append(f'<p class="{status}">File: {filename} - {message}</p>')
                html_parts.append('</div>')
                continue

            # MODIFIED: Add hyperlink to filename if base_url is provided
            if base_url:
                # Ensure the base URL ends with a slash to avoid issues like example.comfile.pdf
                if not base_url.endswith('/'):
                    base_url += '/'
                file_url = f'{base_url}{filename}'
                html_parts.append(f'<div class="file-title">📄 <a href="{file_url}" target="_blank">{filename}</a></div>')
            else:
                html_parts.append(f'<div class="file-title">📄 {filename}</div>')

            # Only show the summary line if the filter is NOT active.
            if not filter_no_results:
                total_occurrences = sum(len(matches) for matches in file_data.values())
                unique_words_found = len(file_data)
                html_parts.append(f'<div class="file-summary">Total: {total_occurrences} occurrences of {unique_words_found} unique words.</div>')
            
            for word in search_words:
                if word in file_data:
                    matches = file_data[word]
                    count = len(matches)
                    html_parts.append(f'<div class="word-section">')
                    html_parts.append(f'<div class="word-title">Word: \'{word}\' (Found {count} times)</div>')
                    sorted_matches = sorted(list(set(matches)), key=lambda x: (x[0], x[1]))
                    for page, line, before, match_line, after in sorted_matches:
                        html_parts.append('<div class="match">')
                        html_parts.append(f'<strong>Page {page}, Line {line}:</strong>')
                        context_parts = []
                        if before: context_parts.append(before.strip())
                        if match_line: context_parts.append(highlight_word_in_text(match_line, word, use_regex, for_html=True))
                        if after: context_parts.append(after.strip())
                        full_context = "\n".join(context_parts)
                        html_parts.append(f'<div class="match-details">{full_context}</div>')
                        html_parts.append('</div>')
                    html_parts.append('</div>')
            html_parts.append('</div>')

    html_parts.append('</div></body></html>')
    return "".join(html_parts)

# --- Main Execution ---
def run_search(target_path, args):
    """Main function to orchestrate the search."""
    pdf_files_to_process = []
    if os.path.isfile(target_path):
        if target_path.lower().endswith('.pdf'):
            pdf_files_to_process.append(target_path)
        else:
            return f"Error: The file '{target_path}' is not a PDF."
    elif os.path.isdir(target_path):
        pdf_files_to_process = find_pdf_files(target_path, args.recursive, args.exclude)
        if not pdf_files_to_process:
            return f"No PDF files found in the folder: {target_path}"
    else:
        return f"Error: The path '{target_path}' does not exist or is not a valid file/directory."

    total_pages = count_total_pages(pdf_files_to_process)
    if total_pages == 0:
        print("No pages found to search in the provided PDFs.")
        return "No pages found to search."

    final_results = {}
    from tqdm import tqdm
    with tqdm(total=total_pages, desc="Processing Pages", unit="page") as pbar:
        for file_path in pdf_files_to_process:
            filename = os.path.basename(file_path)
            result = search_in_file(file_path, args.words, args.case_sensitive, args.whole_word, args.regex, pbar)
            # Always add the file to the results. `None` means no matches.
            final_results[filename] = result
    return final_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Nerd-Search: Find words in PDFs with context and advanced options.",
        epilog="Examples:\n" \
        " python nerd-search.py /path/to/folder \"Epstein\" \"Trump\" --html-output results.html\n" \
        " python nerd-search.py /path/to/file.pdf \"yacht\" --case-sensitive\n" \
        " python nerd-search.py /path/to/logs --recursive --regex \"error \\d{4}\""
    )

    # Special action argument
    parser.add_argument("--setup", action='store_true', help="Check and install required libraries (PyPDF2, tqdm, colorama).")
    
    parser.add_argument("path", nargs='?', help="The path to a PDF file or a folder containing PDF files.", default=None)
    parser.add_argument("words", nargs='*', help="One or more words to search for.", default=None)

    # Search options
    parser.add_argument("--case-sensitive", action='store_true', help="Make the search case-sensitive.")
    parser.add_argument("--whole-word", action='store_true', default=True, help="Match whole words only (default: True). Disable to find substrings.")
    parser.add_argument("--regex", action='store_true', help="Treat search words as regular expressions.")

    # File handling options
    parser.add_argument("--recursive", action='store_true', help="Search recursively in subdirectories.")
    parser.add_argument("--exclude", nargs='*', default=[], help="Exclude files matching these regex patterns (e.g., '*glossary*').")
    
    # Output options (mutually exclusive)
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("-o", "--output", metavar="FILE", help="Save results to a plain text file.")
    output_group.add_argument("--html-output", metavar="FILE", help="Save results to a styled HTML file.")
    
    # MODIFIED: Added the new --filter-no-results argument
    parser.add_argument("--filter-no-results", action='store_true', help="Only show files that contain at least one match. Hide files with no results and their summary lines.")

    # NEW: Added the new --base-url argument
    parser.add_argument("--base-url", metavar="URL", help="A base URL to create hyperlinks for each file in the HTML output. E.g., https://example.com/pdfs/")

    parser.add_argument("-q", "--quiet", action='store_true', help="Quiet mode. Only show filenames with matches (affects console output).")
    
    args = parser.parse_args()

    # Handle the --setup flag first
    if args.setup:
        check_and_install_requirements()
        sys.exit(0)

    # Validate normal arguments
    if not args.path or not args.words:
        print("\n[!] Missing path or search words.", file=sys.stderr)
        parser.print_help()
        print("\n[!] Hint: If this is your first time, run 'python nerd-search.py --setup' to install dependencies.")
        exit()

    # Check for requirements before running the main search
    if not check_and_install_requirements():
        sys.exit(1)

    print(f"Searching: {args.path}\n")
    results_data = run_search(args.path, args)

    # --- Output Handling ---
    if args.html_output:
        # MODIFIED: Pass the new base_url argument to the formatter
        html_string = format_results_for_html(results_data, args.words, args.quiet, args.regex, args.filter_no_results, args.base_url)
        try:
            with open(args.html_output, 'w', encoding='utf-8') as f:
                f.write(html_string)
            print(f"\nResults successfully saved to {args.html_output}")
        except IOError as e:
            print(f"\n[!] Error writing to HTML file: {e}", file=sys.stderr)
    elif args.output:
        text_string = format_results_for_console(results_data, args.words, args.quiet, args.regex, args.filter_no_results)
        clean_text = strip_ansi_codes(text_string)
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(clean_text)
            print(f"\nResults successfully saved to {args.output}")
        except IOError as e:
            print(f"\n[!] Error writing to text file: {e}", file=sys.stderr)
    else:
        console_string = format_results_for_console(results_data, args.words, args.quiet, args.regex, args.filter_no_results)
        print(console_string)