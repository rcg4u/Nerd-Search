# In your future nerd_gui.py file:
import importlib.util

# --- Load the nerd-search.py module ---
spec = importlib.util.spec_from_file_location("nerd_search_engine", "d:/sources/nerd-search/nerd-search.py")
nerd_search = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nerd_search)

# --- Now you can call its functions ---
# ... inside your GUI's "search" button click event ...
target_path = "D:\path\to\your\pdfs"
search_words = ["Epstein", "Trump"]

# Call the main function from your imported module
formatted_results = nerd_search.run_search(target_path, search_words)

# Now, display `formatted_results` in a text box in your GUI