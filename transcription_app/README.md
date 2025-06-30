# Transcription App - Modular Architecture

This directory contains the modularized version of the Whisper Transcription App, organized into logical components for better maintainability and scalability.

## Directory Structure

```
transcription_app/
├── main.py                    # Entry point for the modular app
├── config/                    # Configuration and settings
│   ├── __init__.py
│   ├── settings.py           # App configuration and environment variables
│   └── styles.py             # CSS styles and UI theming
├── database/                  # Database operations
│   ├── __init__.py
│   ├── models.py             # TranscriptionDB class and operations
│   └── connection.py         # Database connection and configuration
├── audio/                     # Audio processing and transcription
│   ├── __init__.py
│   ├── preprocessing.py      # Silence removal and compression
│   ├── transcription.py     # Whisper API integration
│   └── utils.py              # Audio utility functions
├── ui/                        # User interface components
│   ├── __init__.py
│   ├── components.py         # Reusable UI components
│   └── pages.py              # Main page rendering logic
├── utils/                     # General utilities
│   ├── __init__.py
│   ├── dependencies.py      # Dependency checking and validation
│   └── file_utils.py        # File handling utilities
└── tests/                     # Unit tests
    ├── __init__.py
    └── test_utils.py         # Utility function tests
```

## Module Descriptions

### config/
- **settings.py**: Central configuration management, environment variables, and app constants
- **styles.py**: CSS styling and UI theming functions

### database/
- **models.py**: TranscriptionDB class with all database operations (CRUD)
- **connection.py**: Database connection handling and status display

### audio/
- **preprocessing.py**: Audio processing functions (silence removal, compression)
- **transcription.py**: Whisper API integration and transcription logic
- **utils.py**: Audio-related utility functions and helpers

### ui/
- **components.py**: Reusable UI components and widgets
- **pages.py**: Main page rendering and application flow

### utils/
- **dependencies.py**: Dependency checking and system validation
- **file_utils.py**: File handling, validation, and sanitization

### tests/
- **test_utils.py**: Unit tests for utility functions
- Additional test files can be added for each module

## Benefits of Modular Architecture

1. **Maintainability**: Each module has a single responsibility
2. **Testability**: Individual components can be unit tested
3. **Reusability**: Components can be reused across the application
4. **Scalability**: Easy to add new features without affecting existing code
5. **Collaboration**: Multiple developers can work on different modules
6. **Code Organization**: Related functionality is grouped together

## Running the Modular App

From the project root directory:

```bash
# Run the modular version
streamlit run main.py

# Or run from within the transcription_app directory
cd transcription_app
streamlit run main.py
```

## Testing

Run unit tests:

```bash
# Run all tests
python -m pytest transcription_app/tests/

# Run specific test file
python -m pytest transcription_app/tests/test_utils.py

# Run with coverage
python -m pytest transcription_app/tests/ --cov=transcription_app
```

## Adding New Features

When adding new features:

1. Identify the appropriate module (config, database, audio, ui, utils)
2. Add new functions/classes to the relevant module
3. Update imports in other modules as needed
4. Add unit tests for new functionality
5. Update documentation as needed

## Migration from Monolithic Version

The original `transcription_app.py` (830 lines) has been split into focused modules:
- Configuration: ~40 lines per file
- Database: ~80-120 lines per file  
- Audio: ~50-150 lines per file
- UI: ~100-200 lines per file
- Utils: ~50-100 lines per file

This makes the codebase much more manageable and easier to understand.