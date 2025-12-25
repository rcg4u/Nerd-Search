import os
import re
import argparse
import sys
from PyPDF2 import PdfReader
import colorama
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# --- Initialize colorama for cross-platform formatting ---
colorama.init(autoreset=True)

# --- ANSI escape codes for formatting ---
HIGHLIGHT_COLOR = '\033[41m'  # Red Background Highlight
RESET_COLOR = '\033[0m'

def search_in_file(file_path, search_words, case_sensitive, whole_word, use_regex):
    """Searches for words in a single PDF file.
    Returns a dictionary of results or a special message for scanned files.
    """
    try:
        reader = PdfReader(file_path)
        if not reader.pages:
            return None # Skip empty files

        # Basic check for scanned image PDFs
        first_page_text = reader.pages[0].extract_text() or ""
        if len(first_page_text.strip()) < 50:
            return {"_is_scanned_": ["This PDF appears to be a scanned image and contains no extractable text."]}

        # Build search patterns based on user options
        search_patterns = {}
        flags = 0 if case_sensitive else re.IGNORECASE
        
        for word in search_words:
            if use_regex:
                # User-provided regex, no escaping or word boundaries
                search_patterns[word] = re.compile(word, flags=flags)
            else:
                # Normal word search, with escaping and optional word boundaries
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
        return found_in_file if found_in_file else None

    except Exception as e:
        # Return error as a string to be handled by the main thread
        return f"Could not read or process file. Reason: {e}"

def highlight_word_in_text(text, word, use_regex):
    """Highlights all occurrences of a word in a text."""
    if use_regex:
        # For regex, we can't easily reconstruct the word to highlight
        # So we will not highlight if regex is used to avoid complex matching.
        return text
    
    return re.sub(
        rf'({re.escape(word)})',
        lambda match: f"{HIGHLIGHT_COLOR}{match.group(1)}{RESET_COLOR}",
        text,
        flags=re.IGNORECASE
    )

def strip_ansi_codes(text):
    """Removes ANSI escape codes from a string."""
    return re.sub(r'\x1b$$[0-9;]*m', '', text)

def format_results_for_console(results, search_words, quiet_mode, use_regex):
    """Formats the full result dictionary into a clean, multi-line string for console output."""
    if quiet_mode:
        # In quiet mode, only print filenames with matches
        output_lines = [filename for filename, data in results.items() if data and not isinstance(data, str)]
        return "\n".join(output_lines)

    output_lines = ["===== SEARCH RESULTS ====="]
    if not results:
        output_lines.append("No matching words found in any files.")
    else:
        for filename, file_data in results.items():
            if isinstance(file_data, str):
                output_lines.append(f"\n[!] Error in {filename}: {file_data}")
                continue
            if not file_data:
                continue

            output_lines.append(f"\n📄 Found in: {filename}")
            
            # Calculate and display total counts for the file
            total_occurrences = sum(len(matches) for matches in file_data.values())
            unique_words_found = len(file_data)
            output_lines.append(f"   -> Total: {total_occurrences} occurrences of {unique_words_found} unique words.")

            for word in search_words:
                if word in file_data:
                    matches = file_data[word]
                    count = len(matches)
                    output_lines.append(f"\n   - Word: '{word}' (Found {count} times)")
                    
                    # Use a set to remove duplicate line occurrences
                    sorted_matches = sorted(list(set(matches)), key=lambda x: (x[0], x[1]))
                    for page, line, before, match_line, after in sorted_matches:
                        output_lines.append(f"     > Page {page}, Line {line}:")
                        if before:
                            output_lines.append(f"       {before}")
                        
                        highlighted_line = highlight_word_in_text(match_line, word, use_regex)
                        output_lines.append(f"     >>> {highlighted_line}")
                        
                        if after:
                            output_lines.append(f"       {after}")
                        output_lines.append("-" * 20)
    output_lines.append("========================\n")
    return "\n".join(output_lines)

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

def run_search(target_path, args):
    """Main function to orchestrate the search using parallel processing."""
    final_results = {}
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

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor() as executor:
        # Submit all search tasks to the executor
        future_to_filename = {
            executor.submit(
                search_in_file, 
                file_path, 
                args.words, 
                args.case_sensitive, 
                args.whole_word, 
                args.regex
            ): os.path.basename(file_path)
            for file_path in pdf_files_to_process
        }

        # Use tqdm to display a progress bar as tasks complete
        for future in tqdm(as_completed(future_to_filename), total=len(pdf_files_to_process), desc="Searching PDFs"):
            filename = future_to_filename[future]
            try:
                result = future.result()
                if result:
                    final_results[filename] = result
            except Exception as e:
                final_results[filename] = f"An unexpected error occurred: {e}"

    return format_results_for_console(final_results, args.words, args.quiet, args.regex)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Nerd-Search: Find words in PDFs with context and advanced options.",
        epilog="Examples:\n" \
               "  python nerd-search.py /path/to/folder \"Epstein\" \"Trump\" -o results.txt\n" \
               "  python nerd-search.py /path/to/file.pdf \"yacht\" --case-sensitive\n" \
               "  python nerd-search.py /path/to/logs --recursive --regex \"error \\d{4}\""
    )
    parser.add_argument("path", help="The path to a PDF file or a folder containing PDF files.")
    parser.add_argument("words", nargs='+', help="One or more words to search for.")

    # Search options
    parser.add_argument("--case-sensitive", action='store_true', help="Make the search case-sensitive.")
    parser.add_argument("--whole-word", action='store_true', default=True, help="Match whole words only (default: True). Disable to find substrings.")
    parser.add_argument("--regex", action='store_true', help="Treat search words as regular expressions.")
    
    # File handling options
    parser.add_argument("--recursive", action='store_true', help="Search recursively in subdirectories.")
    parser.add_argument("--exclude", nargs='*', default=[], help="Exclude files matching these regex patterns (e.g., '*glossary*').")

    # Output options
    parser.add_argument("-o", "--output", metavar="FILE", help="Save results to a file instead of printing to console.")
    parser.add_argument("-q", "--quiet", action='store_true', help="Quiet mode. Only show filenames with matches.")

    args = parser.parse_args()

    if not args.words:
        print("\n[!] Missing search words.", file=sys.stderr)
        parser.print_help()
        exit()

    print(f"Searching: {args.path}\n")
    results_string = run_search(args.path, args)

    if args.output:
        # Strip ANSI codes for clean text file output
        clean_results = strip_ansi_codes(results_string)
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(clean_results)
            print(f"\nResults successfully saved to {args.output}")
        except IOError as e:
            print(f"\n[!] Error writing to file: {e}", file=sys.stderr)
    else:
        print(results_string)