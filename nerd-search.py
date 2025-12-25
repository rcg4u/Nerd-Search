import os
import re
import argparse
from PyPDF2 import PdfReader

def search_in_file(file_path, search_words):
    """
    Searches for words in a PDF, first checking if it's a scanned image.
    Returns results with page, line number, and context lines.
    """
    # Pre-compile the regular expressions for a significant speed boost
    search_patterns = {word: re.compile(rf'\b{re.escape(word.lower())}\b') for word in search_words}
    found_in_file = {}

    try:
        reader = PdfReader(file_path)
        
        # --- Check if the PDF is likely a scanned image ---
        if reader.pages:
            first_page_text = reader.pages[0].extract_text() or ""
            if len(first_page_text.strip()) < 50:
                return {"_is_scanned_": ["This PDF appears to be a scanned image and contains no extractable text."]}

        # --- If not scanned, proceed with the search ---
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            lines = text.split('\n')
            
            # Enumerate lines to get the line index and number (starting from 1)
            for line_index, line in enumerate(lines):
                line_num = line_index + 1
                line_lower = line.lower()
                
                for word, pattern in search_patterns.items():
                    if pattern.search(line_lower):
                        if word not in found_in_file:
                            found_in_file[word] = []
                        
                        # --- Get context lines ---
                        # The line before (if it exists)
                        context_before = lines[line_index - 1].strip() if line_index > 0 else ""
                        # The line itself
                        context_line = line.strip()
                        # The line after (if it exists)
                        context_after = lines[line_index + 1].strip() if line_index < len(lines) - 1 else ""
                        
                        # Store a tuple with all the necessary information
                        found_in_file[word].append(
                            (page_num + 1, line_num, context_before, context_line, context_after)
                        )
                        
    except Exception as e:
        raise Exception(f"Could not read or process file. Reason: {e}")
    
    return found_in_file

def display_results(results):
    """
    Prints the final search results with context lines.
    """
    print("\n===== SEARCH RESULTS =====")
    if not results:
        print("No matching words found.")
    else:
        for filename, words_found in results.items():
            # --- Check for the special scanned key ---
            if "_is_scanned_" in words_found:
                print(f"\n🖼️ Skipped: {filename}")
                for message in words_found["_is_scanned_"]:
                    print(f"   > {message}")
                continue # Move to the next file

            print(f"\n📄 Found in: {filename}")
            for word, matches in words_found.items():
                print(f"\n   - Word: '{word}'")
                # Sort matches by page, then by line number for a clean output
                sorted_matches = sorted(list(set(matches)), key=lambda x: (x[0], x[1]))
                for page, line, before, match_line, after in sorted_matches:
                    print(f"     > Page {page}, Line {line}:")
                    if before:
                        print(f"       {before}")
                    print(f"     >>> {match_line}") # Highlight the matching line
                    if after:
                        print(f"       {after}")
                    print("-" * 20) # Add a separator for clarity
    print("========================\n")

if __name__ == "__main__":
    # --- Set up command-line argument parser ---
    parser = argparse.ArgumentParser(
        description="Search for specific words in a PDF file or all PDFs in a folder and show the surrounding text.",
        epilog="Examples:\n" \
               "  # Search a folder:\n" \
               "  python pdf_searcher.py /path/to/folder \"Epstein\" \"Trump\"\n" \
               "  # Search a single file:\n" \
               "  python pdf_searcher.py /path/to/file.pdf \"yacht\""
    )

    parser.add_argument("path", help="The path to a PDF file or a folder containing PDF files.")
    parser.add_argument("words", nargs='+', help="One or more words to search for (space-separated). Use quotes for phrases.")
    args = parser.parse_args()

    # --- Check for correct number of arguments for a friendly error message ---
    if not hasattr(args, 'words') or not args.words:
        print("\n[!] Missing search words.")
        print("You must provide at least one word to search for.\n")
        parser.print_help()
        exit()

    target_path = args.path
    search_words = args.words
    final_results = {}

    # --- Determine if path is a file or a directory and run the search ---
    if os.path.isfile(target_path):
        if target_path.lower().endswith('.pdf'):
            print(f"Searching single file: {target_path}\n")
            try:
                file_results = search_in_file(target_path, search_words)
                if file_results:
                    filename = os.path.basename(target_path)
                    final_results[filename] = file_results
            except Exception as e:
                print(f"  [!] Error processing {os.path.basename(target_path)}. {e}")
        else:
            print(f"Error: The file '{target_path}' is not a PDF.")
            
    elif os.path.isdir(target_path):
        print(f"Searching in folder: {target_path}\n")
        pdf_files_found = False
        for filename in os.listdir(target_path):
            if filename.lower().endswith('.pdf'):
                pdf_files_found = True
                file_path = os.path.join(target_path, filename)
                print(f"--- Scanning: {filename} ---")
                try:
                    file_results = search_in_file(file_path, search_words)
                    if file_results:
                        final_results[filename] = file_results
                except Exception as e:
                    print(f"  [!] Error processing {filename}. {e}")

        if not pdf_files_found:
            print(f"No PDF files found in the folder: {target_path}")
            
    else:
        print(f"Error: The path '{target_path}' does not exist or is not a valid file/directory.")

    # --- Display the collected results ---
    display_results(final_results)