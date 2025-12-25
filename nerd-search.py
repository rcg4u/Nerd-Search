import os
import re
import argparse
from PyPDF2 import PdfReader

def search_in_file(file_path, search_words):
    """Searches for words in a single PDF file and returns the results with context."""
    search_words_lower = [word.lower() for word in search_words]
    # Store results as: {word: [list_of_matching_lines]}
    found_in_file = {}

    try:
        reader = PdfReader(file_path)
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            # Split the entire page text into individual lines
            lines = text.split('\n')
            
            for line in lines:
                line_lower = line.lower()
                for word in search_words_lower:
                    # Use regular expression to find whole words
                    if re.search(rf'\b{re.escape(word)}\b', line_lower):
                        if word not in found_in_file:
                            found_in_file[word] = []
                        # Store the line, stripping extra whitespace
                        found_in_file[word].append(line.strip())
                        
    except Exception as e:
        # We will let the calling function handle the error message
        raise Exception(f"Could not read or process file. Reason: {e}")
    
    return found_in_file

def display_results(results):
    """Prints the final search results with context lines."""
    print("\n===== SEARCH RESULTS =====")
    if not results:
        print("No matching words found.")
    else:
        for filename, words_found in results.items():
            print(f"\n📄 Found in: {filename}")
            for word, lines in words_found.items():
                print(f"\n   - Word: '{word}'")
                # Use a set to automatically remove duplicate lines if a word appears multiple times on one line
                unique_lines = sorted(list(set(lines)))
                for line in unique_lines:
                    # Indent the context line for readability
                    print(f"     > {line}")
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