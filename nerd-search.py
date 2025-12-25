
import os
import re
import argparse
from PyPDF2 import PdfReader

def search_in_file(file_path, search_words):
    """Searches for words in a single PDF file and returns the results."""
    search_words_lower = [word.lower() for word in search_words]
    found_in_file = {}
    filename = os.path.basename(file_path)

    try:
        reader = PdfReader(file_path)
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text_lower = text.lower()
            for word in search_words_lower:
                if re.search(rf'\b{re.escape(word)}\b', text_lower):
                    if word not in found_in_file:
                        found_in_file[word] = []
                    found_in_file[word].append(page_num + 1)
    except Exception as e:
        print(f"  [!] Could not read or process {filename}. Reason: {e}")
    
    return found_in_file

def search_in_folder(folder_path, search_words):
    """Searches for words in all PDFs within a folder and returns the results."""
    all_results = {}
    pdf_files_found = False

    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.pdf'):
            pdf_files_found = True
            file_path = os.path.join(folder_path, filename)
            print(f"--- Scanning: {filename} ---")
            results = search_in_file(file_path, search_words)
            if results:
                all_results[filename] = results
    
    if not pdf_files_found:
        print(f"No PDF files found in the folder: {folder_path}")
        
    return all_results

def display_results(results):
    """Prints the final search results in a clean format."""
    print("\n===== SEARCH RESULTS =====")
    if not results:
        print("No matching words found.")
    else:
        for filename, words_found in results.items():
            print(f"\n📄 Found in: {filename}")
            for word, pages in words_found.items():
                page_list_str = ", ".join(map(str, sorted(pages)))
                print(f"   - '{word}' on page(s): {page_list_str}")
    print("========================\n")

if __name__ == "__main__":
    # --- Set up command-line argument parser ---
    parser = argparse.ArgumentParser(
        description="Search for specific words in a PDF file or all PDFs in a folder.",
        epilog="Examples:\n" \
               "  # Search a folder:\n" \
               "  python pdf_searcher.py /path/to/folder \"Epstein\" \"Trump\"\n" \
               "  # Search a single file:\n" \
               "  python pdf_searcher.py /path/to/file.pdf \"yacht\""
    )

    # Add the argument for the path (can be file or folder)
    parser.add_argument(
        "path", 
        help="The path to a PDF file or a folder containing PDF files."
    )
    # Add the argument for the words to search
    parser.add_argument(
        "words", 
        nargs='+',  # One or more words
        help="One or more words to search for (space-separated). Use quotes for phrases."
    )

    args = parser.parse_args()

    target_path = args.path
    search_words = args.words

    # --- Determine if path is a file or a directory and run the search ---
    if os.path.isfile(target_path):
        if target_path.lower().endswith('.pdf'):
            print(f"Searching single file: {target_path}\n")
            results = search_in_file(target_path, search_words)
            display_results(results)
        else:
            print(f"Error: The file '{target_path}' is not a PDF.")
    elif os.path.isdir(target_path):
        print(f"Searching in folder: {target_path}\n")
        results = search_in_folder(target_path, search_words)
        display_results(results)
    else:
        print(f"Error: The path '{target_path}' does not exist or is not a valid file/directory.")