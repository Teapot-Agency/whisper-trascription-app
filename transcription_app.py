import streamlit as st
import openai
from datetime import datetime
import io
import os
from typing import Dict, List, Optional
import json
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Whisper Transcription App",
    page_icon="🎙️",
    layout="wide"
)

# Custom CSS for Tailwind-like styling
st.markdown("""
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'transcription_history' not in st.session_state:
    st.session_state.transcription_history = []

# Get API key from environment or session state
api_key = os.getenv('OPENAI_API_KEY', '')

# Header
st.markdown('<h1 class="header-title">🎙️ Whisper Transcription App</h1>', unsafe_allow_html=True)
st.markdown(
    '<p style="color: #6B7280; font-size: 1.125rem;">Upload audio files and get accurate transcriptions using OpenAI Whisper v3</p>',
    unsafe_allow_html=True)

# API Key Section - Only show if not set in environment
if not api_key:
    with st.container():
        st.markdown('<div class="section-title">🔑 API Configuration</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="error-box">⚠️ OpenAI API key not found in environment variables. Please add OPENAI_API_KEY to your .env file or secrets.</div>',
            unsafe_allow_html=True)

        # Fallback: Allow manual input if env var not set
        api_key = st.text_input(
            "OpenAI API Key (temporary)",
            type="password",
            placeholder="sk-...",
            help="For production, add OPENAI_API_KEY to your .env file"
        )
else:
    st.markdown('<div class="success-box">✅ API key loaded from environment</div>', unsafe_allow_html=True)

# Main transcription section
st.markdown('<div class="section-title">📤 Upload Audio File</div>', unsafe_allow_html=True)

# File uploader
uploaded_file = st.file_uploader(
    "Choose an audio file",
    type=['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm'],
    help="Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, webm"
)

# Transcription options
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    custom_name = st.text_input(
        "Custom name (optional)",
        placeholder="e.g., Meeting notes, Interview with John",
        help="Give your transcription a memorable name"
    )
with col2:
    language = st.selectbox(
        "Language (optional)",
        ["Auto-detect", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
        help="Select the audio language or leave as auto-detect"
    )
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    transcribe_button = st.button("🎯 Transcribe", use_container_width=True)


# Transcription function
def transcribe_audio(file, api_key: str, language: str = None) -> Optional[str]:
    """Transcribe audio using OpenAI Whisper API"""
    try:
        client = openai.OpenAI(api_key=api_key)

        # Prepare language parameter
        lang_param = None if language == "Auto-detect" else language

        # Transcribe
        transcript = client.audio.transcriptions.create(
            model="whisper-1",  # This uses Whisper v3
            file=file,
            language=lang_param
        )

        return transcript.text
    except Exception as e:
        st.error(f"Error during transcription: {str(e)}")
        return None


# Handle transcription
if transcribe_button and uploaded_file and api_key:
    with st.spinner("🔄 Transcribing audio... This may take a moment."):
        # Reset file pointer
        uploaded_file.seek(0)

        # Transcribe
        transcription_text = transcribe_audio(
            uploaded_file,
            api_key,
            language
        )

        if transcription_text:
            # Create transcription record
            transcription_record = {
                "id": datetime.now().timestamp(),
                "name": custom_name or uploaded_file.name,
                "filename": uploaded_file.name,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "text": transcription_text,
                "language": language
            }

            # Add to history
            st.session_state.transcription_history.insert(0, transcription_record)

            # Show success message
            st.markdown('<div class="success-box">✅ Transcription completed successfully!</div>',
                        unsafe_allow_html=True)

            # Display transcription
            st.markdown('<div class="section-title">📝 Transcription Result</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="transcription-card">{transcription_text}</div>', unsafe_allow_html=True)

            # Download button
            st.download_button(
                label="📥 Download Transcription",
                data=transcription_text,
                file_name=f"{custom_name or uploaded_file.name}_transcription.txt",
                mime="text/plain"
            )

elif transcribe_button and not api_key:
    st.markdown('<div class="error-box">⚠️ Please configure your OpenAI API key</div>', unsafe_allow_html=True)
elif transcribe_button and not uploaded_file:
    st.markdown('<div class="error-box">⚠️ Please upload an audio file first</div>', unsafe_allow_html=True)

# History section
if st.session_state.transcription_history:
    st.markdown('<div class="section-title">📚 Transcription History</div>', unsafe_allow_html=True)

    # Search and filter
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            "🔍 Search transcriptions",
            placeholder="Search by name or content..."
        )
    with col2:
        if st.button("Clear History", use_container_width=True):
            st.session_state.transcription_history = []
            st.rerun()

    # Display history
    filtered_history = st.session_state.transcription_history
    if search_query:
        filtered_history = [
            t for t in filtered_history
            if search_query.lower() in t['name'].lower() or
               search_query.lower() in t['text'].lower()
        ]

    for idx, item in enumerate(filtered_history):
        with st.expander(f"🎵 {item['name']} - {item['date']}", expanded=False):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**Original filename:** {item['filename']}")
                st.markdown(f"**Language:** {item['language']}")
                st.markdown(f"**Date:** {item['date']}")

                # Show transcription
                st.markdown("**Transcription:**")
                st.text_area(
                    "Transcription text",
                    item['text'],
                    height=200,
                    key=f"text_{idx}",
                    disabled=True
                )

            with col2:
                st.markdown("<br>", unsafe_allow_html=True)

                # Download button for individual transcription
                st.download_button(
                    label="📥 Download",
                    data=item['text'],
                    file_name=f"{item['name']}_transcription.txt",
                    mime="text/plain",
                    key=f"download_{idx}"
                )

                # Delete button
                if st.button("🗑️ Delete", key=f"delete_{idx}"):
                    st.session_state.transcription_history.pop(idx)
                    st.rerun()

    # Export all history
    if len(filtered_history) > 0:
        st.markdown("---")

        # Prepare JSON export
        export_data = json.dumps(filtered_history, indent=2)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📑 Export All History (JSON)",
                data=export_data,
                file_name=f"transcription_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

        with col2:
            # Export as text
            text_export = "\n\n".join([
                f"Name: {item['name']}\nDate: {item['date']}\nLanguage: {item['language']}\n\nTranscription:\n{item['text']}\n\n{'=' * 50}"
                for item in filtered_history
            ])
            st.download_button(
                label="📄 Export All History (TXT)",
                data=text_export,
                file_name=f"transcription_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

else:
    st.markdown('<div class="info-box">📭 No transcriptions yet. Upload an audio file to get started!</div>',
                unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #6B7280; padding: 1rem;">
        <p>Built with Streamlit and OpenAI Whisper v3 | 
        <a href="https://platform.openai.com/docs/guides/speech-to-text" target="_blank" style="color: #3B82F6;">API Documentation</a></p>
    </div>
    """,
    unsafe_allow_html=True
)