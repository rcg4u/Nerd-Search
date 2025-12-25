import os
import re
from PyPDF2 import PdfReader

def search_words_in_pdfs(folder_path, search_words):
    """
    Searches for a list of words in all PDF files within a given folder.

    Args:
        folder_path (str): The path to the folder containing PDF files.
        search_words (list): A list of words to search for.
    """
    # --- Configuration ---
    # Make search case-insensitive by converting all words to lowercase
    search_words_lower = [word.lower() for word in search_words]
    
    # Store results: {filename: {word: [page_numbers]}}
    results = {}

    print(f"Searching in folder: {folder_path}\n")

    # --- Loop through all files in the folder ---
    for filename in os.listdir(folder_path):
        # Check if the file is a PDF
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(folder_path, filename)
            print(f"--- Scanning: {filename} ---")
            
            try:
                # --- Open and read the PDF ---
                reader = PdfReader(file_path)
                found_in_this_file = {}

                # --- Loop through each page of the PDF ---
                for page_num, page in enumerate(reader.pages):
                    # Extract text from the page
                    text = page.extract_text() or ""
                    
                    # Make the text lowercase for case-insensitive search
                    text_lower = text.lower()

                    # --- Check for each search word on the page ---
                    for word in search_words_lower:
                        # Use regular expression to find whole words only
                        # \b is a word boundary, preventing "cat" from matching "concatenate"
                        if re.search(rf'\b{re.escape(word)}\b', text_lower):
                            if word not in found_in_this_file:
                                found_in_this_file[word] = []
                            # Add 1 to page_num because pages are 0-indexed
                            found_in_this_file[word].append(page_num + 1)

                # --- Store results if any words were found ---
                if found_in_this_file:
                    results[filename] = found_in_this_file

            except Exception as e:
                print(f"  [!] Could not read or process {filename}. Reason: {e}")
            
    # --- Display the final results ---
    print("\n===== SEARCH RESULTS =====")
    if not results:
        print("No matching words found in any PDF files.")
    else:
        for filename, words_found in results.items():
            print(f"\n📄 Found in: {filename}")
            for word, pages in words_found.items():
                # Sort pages and join them into a clean string
                page_list_str = ", ".join(map(str, sorted(pages)))
                print(f"   - '{word}' on page(s): {page_list_str}")
    print("========================\n")


# --- HOW TO USE THE SCRIPT ---

if __name__ == "__main__":
    # 1. SET THE FOLDER PATH
    #    Replace with the actual path to your folder containing PDFs.
    #    Example for Windows: r"C:\Users\YourUser\Documents\MyPDFs"
    #    Example for macOS/Linux: "/Users/YourUser/Documents/MyPDFs"
    target_folder = r"C:\path\to\your\pdfs" 

    # 2. SET THE WORDS TO SEARCH FOR
    #    Add or remove words from this list.
    words_to_find = ["Epstein", "Trump", "yacht", "infanticide"]

    # 3. RUN THE SEARCH
    if os.path.isdir(target_folder):
        search_words_in_pdfs(target_folder, words_to_find)
    else:
        print(f"Error: The folder '{target_folder}' does not exist.")
        print("Please update the 'target_folder' variable in the script.")