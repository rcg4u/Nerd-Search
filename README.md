


# nerd-search

A Python script for searching specific words or phrases in all PDF files within a folder.

## Features

- Search for keywords or phrases in PDF files
- Case-insensitive search
- Finds whole words only (not partial matches)
- Outputs matching page numbers for each word in each PDF
- Handles errors gracefully if a PDF cannot be read

## Usage

1. Place `nerd-search.py` in your desired directory.
2. Run the script from the command line:

```bash
python nerd-search.py <folder> <word1> [word2] [word3] ...
```

- `<folder>`: The path to the folder containing PDF files to search.
- `<word1> [word2] ...`: One or more words or phrases to search for (use quotes for phrases).

### Example

```bash
python nerd-search.py ./pdfs Epstein Trump "yacht party"
```

## Requirements

- Python 3.x
- PyPDF2 (`pip install PyPDF2`)

## License

MIT License

---

Feel free to modify and extend this script for your own needs.
