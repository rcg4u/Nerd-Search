import os
import re
import argparse
from PyPDF2 import PdfReader
import colorama

# Initialize colorama. This call is needed to make it work on Windows.
# On other platforms, it does nothing.
colorama.init(autoreset=True)

# ANSI escape codes for formatting
# Changed from underline (\033[4m) to red background highlight (\033[41m)
HIGHLIGHT_COLOR = '\033[41m'  # Red Background Highlight
RESET_COLOR = '\033[0m'

def search_in_file(file_path, search_words):
    """Searches for words in a PDF, first checking if it's a scanned image.
    Returns results with page, line number, and context lines."""
    search_patterns = {word: re.compile(rf'\b{re.escape(word.lower())}\b') for word in search_words}
    found_in_file = {}

    try:
        reader = PdfReader(file_path)
        if reader.pages:
            first_page_text = reader.pages[0].extract_text() or ""
            if len(first_page_text.strip()) < 50:
                return {"_is_scanned_": ["This PDF appears to be a scanned image and contains no extractable text."]}

        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            lines = text.split('\n')

            for line_index, line in enumerate(lines):
                line_lower = line.lower()
                for word, pattern in search_patterns.items():
                    if pattern.search(line_lower):
                        if word not in found_in_file:
                            found_in_file[word] = []
                        
                        context_before = lines[line_index - 1].strip() if line_index > 0 else ""
                        context_line = line.strip()
                        context_after = lines[line_index + 1].strip() if line_index < len(lines) - 1 else ""

                        found_in_file[word].append(
                            (page_num + 1, line_index + 1, context_before, context_line, context_after)
                        )
    except Exception as e:
        raise Exception(f"Could not read or process file. Reason: {e}")

    return found_in_file

def highlight_word_in_text(text, word):
    """Highlights all occurrences of a word in a text, ignoring case."""
    return re.sub(
        rf'({re.escape(word)})',
        lambda match: f"{HIGHLIGHT_COLOR}{match.group(1)}{RESET_COLOR}",
        text,
        flags=re.IGNORECASE
    )

def strip_ansi_codes(text):
    """Removes ANSI escape codes from a string."""
    return re.sub(r'\x1b$$[0-9;]*m', '', text)

def format_results_for_console(results, search_words):
    """Formats the full result dictionary into a clean, multi-line string for console output."""
    output_lines = ["===== SEARCH RESULTS ====="]
    if not results:
        output_lines.append("No matching words found.")
    else:
        for filename, words_found in results.items():
            if "_is_scanned_" in words_found:
                output_lines.append(f"\n🖼️ Skipped: {filename}")
                for message in words_found["_is_scanned_"]:
                    output_lines.append(f"   > {message}")
                continue

            output_lines.append(f"\n📄 Found in: {filename}")
            for word in search_words:
                if word in words_found:
                    output_lines.append(f"\n   - Word: '{word}'")
                    sorted_matches = sorted(list(set(words_found[word])), key=lambda x: (x[0], x[1]))
                    for page, line, before, match_line, after in sorted_matches:
                        output_lines.append(f"     > Page {page}, Line {line}:")
                        if before:
                            output_lines.append(f"       {before}")
                        
                        # Highlight the word in the context line
                        highlighted_line = highlight_word_in_text(match_line, word)
                        output_lines.append(f"     >>> {highlighted_line}")
                        
                        if after:
                            output_lines.append(f"       {after}")
                        output_lines.append("-" * 20)
    output_lines.append("========================\n")
    return "\n".join(output_lines)

def run_search(target_path, search_words):
    """Main function to orchestrate the search."""
    final_results = {}
    if os.path.isfile(target_path):
        if target_path.lower().endswith('.pdf'):
            try:
                file_results = search_in_file(target_path, search_words)
                if file_results:
                    filename = os.path.basename(target_path)
                    final_results[filename] = file_results
            except Exception as e:
                print(f"  [!] Error processing {os.path.basename(target_path)}. {e}")
        else:
            return f"Error: The file '{target_path}' is not a PDF."
    elif os.path.isdir(target_path):
        pdf_files_found = False
        for filename in os.listdir(target_path):
            if filename.lower().endswith('.pdf'):
                pdf_files_found = True
                file_path = os.path.join(target_path, filename)
                try:
                    file_results = search_in_file(file_path, search_words)
                    if file_results:
                        final_results[filename] = file_results
                except Exception as e:
                    print(f"  [!] Error processing {filename}. {e}")
        if not pdf_files_found:
            return f"No PDF files found in the folder: {target_path}"
    else:
        return f"Error: The path '{target_path}' does not exist or is not a valid file/directory."
    
    return format_results_for_console(final_results, search_words)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Nerd-Search: Find words in PDFs with context.",
        epilog="Examples:\n" \
               "  python nerd-search.py /path/to/folder \"Epstein\" \"Trump\"\n" \
               "  python nerd-search.py /path/to/file.pdf \"yacht\""
    )
    parser.add_argument("path", help="The path to a PDF file or a folder containing PDF files.")
    parser.add_argument("words", nargs='+', help="One or more words to search for.")
    args = parser.parse_args()

    if not args.words:
        print("\n[!] Missing search words.")
        parser.print_help()
        exit()

    print(f"Searching: {args.path}\n")
    results_string = run_search(args.path, args.words)
    print(results_string)