# tRead

tRead is a lightweight terminal e-book reader for EPUB files with a clean, modular architecture.

## Why

As I have been really into using terminal user interfaces like LazyGit on my Linux PC, I wanted a quick and customizable way to read e-books in the terminal. Big fan of minimalism where it is applicable and an e-reader shouldn't do more than letting me read my books.

## Project Structure

```
tread/
├── src/
│   └── tread/
│       ├── main.py           # Main application logic
│       ├── core/            # Core business logic
│       │   ├── config.py    # Configuration management
│       │   └── reader.py    # EPUB parsing and reading
│       ├── ui/              # User interface components
│       │   ├── controller.py # Main UI controller
│       │   ├── views.py     # Display components
│       │   └── state.py     # Reading state management
│       └── utils/           # Utility functions
│           ├── terminal.py  # Terminal utilities
│           └── text.py      # Text processing utilities
├── books/                   # Book storage directory
├── config.json             # Configuration file
├── requirements.txt         # Dependencies
└── tread.py                # Entry point script
```

## How to Install and Run

### Prerequisites
- Python 3.8 or higher with pip package manager

### Installation

#### Option 1: Development Mode (Recommended for customization)
1. Clone or download this repository
2. Navigate to the project directory
3. Install dependencies: `pip install -r requirements.txt`
4. Run the program: `python tread.py`

#### Option 2: Install as Package
1. Install in development mode: `pip install -e .`
2. Run from anywhere: `tread`

### Adding Books
Put EPUB files in the `books/` folder to add them to your collection.

## Usage

The default keybindings are vim-like with `j` and `k` being used as down and up to navigate. After selecting a book with `Enter`, you can see all available keybinds by pressing `h`.

If you want to change font size, simply scale the terminal (usually `ctrl+shift+(+/-)`)

### Configuration
Edit `config.json` to customize:
- Keybindings for all actions
- Text formatting options (spacing, indentation, etc.)
- Display preferences

### Development
The modular structure makes it easy to:
- Add new features by extending existing modules
- Modify UI behavior in the `ui/` package
- Customize EPUB parsing in `core/reader.py`
- Add new utilities in the `utils/` package



# Issues

- [ ] When loading some books some paragraphs are duplicated but with differing format? example: Table of contents and Part 1 text for Red Rising
- [ ] When on really big screens (or really zoomed out), it doesn't really make sense to fill page with new lines until the next chapter. Option to display next chapter with just some new lines should be available.