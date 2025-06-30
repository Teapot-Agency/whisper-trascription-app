"""Configuration and environment settings for the Transcription App."""

import os
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

class AppConfig:
    """Application configuration settings."""
    
    # API Settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    # Supabase Settings
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')
    
    # App Settings
    PAGE_TITLE = "Whisper Transcription App"
    PAGE_ICON = "🎙️"
    LAYOUT = "wide"
    
    # Audio Settings
    SUPPORTED_FORMATS = ['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm']
    SUPPORTED_LANGUAGES = ["Auto-detect", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "sk", "cs"]
    
    # Audio Preprocessing
    DEFAULT_SILENCE_THRESH = -50
    DEFAULT_MIN_SILENCE_LEN = 1000
    DEFAULT_KEEP_SILENCE = 200
    MIN_AUDIO_DURATION = 0.1  # seconds

def configure_streamlit():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title=AppConfig.PAGE_TITLE,
        page_icon=AppConfig.PAGE_ICON,
        layout=AppConfig.LAYOUT
    )

def get_api_key():
    """Get OpenAI API key from environment or user input."""
    return AppConfig.OPENAI_API_KEY