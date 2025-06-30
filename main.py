"""Main entry point for the Whisper Transcription App - Modular Version."""

from transcription_app.config.settings import configure_streamlit
from transcription_app.ui.pages import render_main_page

def main():
    """Main application entry point."""
    # Configure Streamlit
    configure_streamlit()
    
    # Render the main page
    render_main_page()

if __name__ == "__main__":
    main()