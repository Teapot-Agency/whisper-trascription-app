import streamlit as st
import openai
from datetime import datetime
import os
from typing import Optional
import json
from dotenv import load_dotenv
import uuid

# Try to import Supabase
try:
    from supabase import create_client, Client

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

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
    .warning-box {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)


# Database setup
class TranscriptionDB:
    def __init__(self):
        # Check if Supabase credentials are available
        self.supabase_url = os.getenv('SUPABASE_URL', '')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY', '')
        self.use_supabase = bool(self.supabase_url and self.supabase_key and SUPABASE_AVAILABLE)

        if self.use_supabase:
            try:
                self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
                # Create table if it doesn't exist (do this in Supabase dashboard)
                # Table schema:
                # CREATE TABLE transcriptions (
                #     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                #     name TEXT NOT NULL,
                #     filename TEXT NOT NULL,
                #     date TEXT NOT NULL,
                #     text TEXT NOT NULL,
                #     language TEXT,
                #     created_at TIMESTAMP DEFAULT NOW()
                # );
            except Exception as e:
                st.error(f"Failed to connect to Supabase: {str(e)}")
                self.use_supabase = False

        # Fallback to session state if Supabase not available
        if not self.use_supabase:
            if 'transcription_history' not in st.session_state:
                st.session_state.transcription_history = []

    def add_transcription(self, transcription):
        """Add a new transcription"""
        if self.use_supabase:
            try:
                data = self.supabase.table('transcriptions').insert({
                    'name': transcription['name'],
                    'filename': transcription['filename'],
                    'date': transcription['date'],
                    'text': transcription['text'],
                    'language': transcription['language']
                }).execute()
                return True
            except Exception as e:
                st.error(f"Error saving to Supabase: {str(e)}")
                return False
        else:
            st.session_state.transcription_history.insert(0, transcription)
            return True

    def get_all_transcriptions(self):
        """Get all transcriptions"""
        if self.use_supabase:
            try:
                response = self.supabase.table('transcriptions').select("*").order('created_at', desc=True).execute()
                return response.data
            except Exception as e:
                st.error(f"Error fetching from Supabase: {str(e)}")
                return []
        else:
            return st.session_state.transcription_history

    def delete_transcription(self, transcription_id):
        """Delete a transcription"""
        if self.use_supabase:
            try:
                self.supabase.table('transcriptions').delete().eq('id', transcription_id).execute()
                return True
            except Exception as e:
                st.error(f"Error deleting from Supabase: {str(e)}")
                return False
        else:
            st.session_state.transcription_history = [
                t for t in st.session_state.transcription_history
                if t.get('id') != transcription_id
            ]
            return True

    def clear_all_transcriptions(self):
        """Clear all transcriptions"""
        if self.use_supabase:
            try:
                # Delete all records - be careful with this!
                self.supabase.table('transcriptions').delete().neq('id',
                                                                   '00000000-0000-0000-0000-000000000000').execute()
                return True
            except Exception as e:
                st.error(f"Error clearing Supabase: {str(e)}")
                return False
        else:
            st.session_state.transcription_history = []
            return True


# Initialize database
@st.cache_resource
def get_db():
    return TranscriptionDB()


db = get_db()

# Get API key from environment
api_key = os.getenv('OPENAI_API_KEY', '')

# Header
st.markdown('<h1 class="header-title">🎙️ Whisper Transcription App</h1>', unsafe_allow_html=True)
st.markdown(
    '<p style="color: #6B7280; font-size: 1.125rem;">Upload audio files and get accurate transcriptions using OpenAI Whisper v3</p>',
    unsafe_allow_html=True)

# Database status indicator
col1, col2 = st.columns([3, 1])
with col1:
    if db.use_supabase:
        st.markdown(
            '<p style="color: #10B981; font-size: 0.875rem;">✅ Connected to Supabase - Transcriptions saved permanently</p>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            '<p style="color: #F59E0B; font-size: 0.875rem;">⚠️ Using temporary storage - Transcriptions will be lost on refresh</p>',
            unsafe_allow_html=True)
with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

# API Key Section - Only show if not set in environment
if not api_key:
    with st.container():
        st.markdown('<div class="section-title">🔑 API Configuration</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="error-box">⚠️ OpenAI API key not found. Please add OPENAI_API_KEY to your environment.</div>',
            unsafe_allow_html=True)

        # Fallback: Allow manual input if env var not set
        api_key = st.text_input(
            "OpenAI API Key (temporary)",
            type="password",
            placeholder="sk-...",
            help="For production, add OPENAI_API_KEY to your environment"
        )
else:
    st.markdown('<div class="success-box">✅ API key loaded from environment</div>', unsafe_allow_html=True)

# Show Supabase setup instructions if not configured
if not db.use_supabase and not SUPABASE_AVAILABLE:
    with st.expander("💡 Enable Permanent Storage (Optional)"):
        st.markdown("""
        To save transcriptions permanently, set up Supabase (free):

        1. **Create account at [supabase.com](https://supabase.com)**
        2. **Create a new project**
        3. **Run this SQL in SQL Editor:**
        ```sql
        CREATE TABLE transcriptions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name TEXT NOT NULL,
            filename TEXT NOT NULL,
            date TEXT NOT NULL,
            text TEXT NOT NULL,
            language TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        ```
        4. **Add to your .env or Streamlit secrets:**
        ```
        SUPABASE_URL=your-project-url
        SUPABASE_ANON_KEY=your-anon-key
        ```
        5. **Install supabase:** `pip install supabase`
        """)

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
                "id": str(uuid.uuid4()),
                "name": custom_name or uploaded_file.name,
                "filename": uploaded_file.name,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "text": transcription_text,
                "language": language
            }

            # Save to database
            if db.add_transcription(transcription_record):
                st.markdown('<div class="success-box">✅ Transcription completed and saved!</div>',
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
transcription_history = db.get_all_transcriptions()

if transcription_history:
    st.markdown('<div class="section-title">📚 Transcription History</div>', unsafe_allow_html=True)
    st.markdown(f'<p style="color: #6B7280;">Found {len(transcription_history)} saved transcriptions</p>',
                unsafe_allow_html=True)

    # Search and filter
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            "🔍 Search transcriptions",
            placeholder="Search by name or content..."
        )
    with col2:
        if st.button("Clear All History", use_container_width=True):
            if st.checkbox("Confirm deletion"):
                db.clear_all_transcriptions()
                st.rerun()

    # Display history
    filtered_history = transcription_history
    if search_query:
        filtered_history = [
            t for t in transcription_history
            if search_query.lower() in t.get('name', '').lower() or
               search_query.lower() in t.get('text', '').lower()
        ]

    for idx, item in enumerate(filtered_history):
        item_id = item.get('id', str(idx))
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
                    key=f"text_{item_id}",
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
                    key=f"download_{item_id}"
                )

                # Delete button
                if st.button("🗑️ Delete", key=f"delete_{item_id}"):
                    db.delete_transcription(item_id)
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
    f"""
    <div style="text-align: center; color: #6B7280; padding: 1rem;">
        <p>Built with Streamlit and OpenAI Whisper v3 | 
        <a href="https://platform.openai.com/docs/guides/speech-to-text" target="_blank" style="color: #3B82F6;">API Documentation</a></p>
        <p style="font-size: 0.875rem; margin-top: 0.5rem;">
        {'📊 Database: Supabase (Cloud)' if db.use_supabase else '💾 Storage: Session State (Temporary)'}
        </p>
    </div>
    """,
    unsafe_allow_html=True
)