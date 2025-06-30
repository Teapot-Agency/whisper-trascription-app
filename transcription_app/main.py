"""Main entry point for the Whisper Transcription App."""

from config.settings import configure_streamlit
from ui.pages import render_main_page

def main():
    """Main application entry point."""
    # Configure Streamlit
    configure_streamlit()
    
    # Render the main page
    render_main_page()

if __name__ == "__main__":
    main()