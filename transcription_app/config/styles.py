"""CSS styles and UI theming for the Transcription App."""

import streamlit as st

CUSTOM_CSS = """
<style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        background-color: #3B82F6;
        color: white;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: 500;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #2563EB;
        transform: translateY(-1px);
    }
    .transcription-card {
        background-color: #F3F4F6;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .history-item {
        background-color: white;
        border: 1px solid #E5E7EB;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s;
    }
    .history-item:hover {
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .header-title {
        color: #1F2937;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .section-title {
        color: #374151;
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        margin-top: 2rem;
    }
    .info-box {
        background-color: #EBF8FF;
        border-left: 4px solid #3B82F6;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.25rem;
    }
    .error-box {
        background-color: #FEE2E2;
        border-left: 4px solid #EF4444;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.25rem;
    }
    .success-box {
        background-color: #D1FAE5;
        border-left: 4px solid #10B981;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.25rem;
    }
    .warning-box {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.25rem;
    }
    .error-container {
        background-color: #FAFAFA;
        border: 1px solid #E5E7EB;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .error-detail {
        color: #6B7280;
        margin: 0.25rem 0;
        margin-left: 1rem;
        font-size: 0.875rem;
    }
    .info-detail {
        color: #374151;
        margin: 0.25rem 0;
        margin-left: 1rem;
        font-size: 0.875rem;
    }
</style>
"""

def apply_custom_styles():
    """Apply custom CSS styles to the Streamlit app."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def display_message(message_type: str, message: str):
    """Display a styled message box."""
    st.markdown(f'<div class="{message_type}-box">{message}</div>', unsafe_allow_html=True)

def display_section_title(title: str):
    """Display a styled section title."""
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

def display_header():
    """Display the main application header."""
    st.markdown('<h1 class="header-title">🎙️ Whisper Transcription App</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color: #6B7280; font-size: 1.125rem;">Upload audio files and get accurate transcriptions using OpenAI Whisper v3</p>',
        unsafe_allow_html=True
    )