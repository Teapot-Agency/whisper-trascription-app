"""Reusable UI components for the Transcription App."""

import streamlit as st
import json
from datetime import datetime
from typing import List, Dict, Optional
from ..config.settings import AppConfig
from ..config.styles import display_message, display_section_title

def render_file_uploader():
    """Render the audio file uploader component."""
    return st.file_uploader(
        "Choose an audio file",
        type=AppConfig.SUPPORTED_FORMATS,
        help=f"Supported formats: {', '.join(AppConfig.SUPPORTED_FORMATS)}"
    )

def render_transcription_options():
    """Render transcription configuration options."""
    col1, col2 = st.columns([2, 2])
    
    with col1:
        custom_name = st.text_input(
            "Custom name (optional)",
            placeholder="e.g., Meeting notes, Interview with John",
            help="Give your transcription a memorable name"
        )
    
    with col2:
        language = st.selectbox(
            "Language (optional)",
            AppConfig.SUPPORTED_LANGUAGES,
            help="Select the audio language or leave as auto-detect"
        )
    
    return custom_name, language

def render_preprocessing_options(preprocessing_available: bool):
    """Render audio preprocessing options."""
    display_section_title("⚙️ Audio Preprocessing Options")
    
    if not preprocessing_available:
        display_message("warning", "⚠️ Audio preprocessing disabled due to missing dependencies")
    
    col1, col2 = st.columns([2, 2])
    
    with col1:
        enable_silence_removal = st.checkbox(
            "🔇 Remove silence",
            value=True if preprocessing_available else False,
            disabled=not preprocessing_available,
            help="Automatically detect and remove silent parts to reduce file size and improve transcription speed" if preprocessing_available else "Requires pydub to be installed"
        )
        
        enable_compression = st.checkbox(
            "🗜️ Compress audio",
            value=True if preprocessing_available else False,
            disabled=not preprocessing_available,
            help="Compress audio using Opus codec at 12kbps for faster upload and processing" if preprocessing_available else "Requires FFmpeg and ffmpeg-python to be installed"
        )
    
    with col2:
        enable_time_splitting = st.checkbox(
            "⏱️ Split long files (25+ min)",
            value=True if preprocessing_available else False,
            disabled=not preprocessing_available,
            help="Automatically split audio files longer than 25 minutes for better processing" if preprocessing_available else "Requires audio preprocessing to be enabled"
        )
        
        enable_transcript_improvement = st.checkbox(
            "🧠 Improve transcript with AI",
            value=True,
            help="Use GPT-4o-mini to fix transcription errors and improve readability while preserving original meaning"
        )
        
        # Output format selection
        st.markdown("**Output Format:**")
        output_format = st.radio(
            "Choose transcription format",
            options=["text", "srt"],
            format_func=lambda x: {
                "text": "📄 Text (plain transcript)",
                "srt": "🎬 SRT (subtitles with timestamps)"
            }[x],
            help="Text format provides plain transcription. SRT format includes precise timestamps for video subtitles.",
            horizontal=True
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        transcribe_button = st.button("🎯 Transcribe", use_container_width=True)
    
    return enable_silence_removal, enable_compression, enable_time_splitting, enable_transcript_improvement, output_format, transcribe_button

def render_api_key_section(api_key: str):
    """Render API key configuration section."""
    if not api_key:
        display_section_title("🔑 API Configuration")
        display_message("error", "⚠️ OpenAI API key not found. Please add OPENAI_API_KEY to your environment.")
        
        # Fallback: Allow manual input if env var not set
        api_key = st.text_input(
            "OpenAI API Key (temporary)",
            type="password",
            placeholder="sk-...",
            help="For production, add OPENAI_API_KEY to your environment"
        )
        return api_key
    else:
        # API key is working - don't show anything (clean UI)
        return api_key

def render_transcription_result(transcription_text: str, filename: str, improved_text: str = None):
    """Render transcription results with download option."""
    display_section_title("📝 Transcription Result")
    
    if improved_text:
        # Show improved version by default with tabs to switch
        tab1, tab2 = st.tabs(["🧠 Improved Version", "📝 Original Version"])
        
        with tab1:
            st.markdown(f'<div class="transcription-card">{improved_text}</div>', unsafe_allow_html=True)
            # Download improved version
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Download Improved",
                    data=improved_text,
                    file_name=f"{filename}_improved_transcription.txt",
                    mime="text/plain",
                    key="download_improved"
                )
            with col2:
                st.download_button(
                    label="📊 Download Both Versions",
                    data=f"=== IMPROVED VERSION ===\n\n{improved_text}\n\n=== ORIGINAL VERSION ===\n\n{transcription_text}",
                    file_name=f"{filename}_both_transcriptions.txt",
                    mime="text/plain",
                    key="download_both"
                )
        
        with tab2:
            st.markdown(f'<div class="transcription-card">{transcription_text}</div>', unsafe_allow_html=True)
            # Download original version
            st.download_button(
                label="📥 Download Original",
                data=transcription_text,
                file_name=f"{filename}_original_transcription.txt",
                mime="text/plain",
                key="download_original"
            )
    else:
        # Show single version (original only)
        st.markdown(f'<div class="transcription-card">{transcription_text}</div>', unsafe_allow_html=True)
        
        # Download button
        st.download_button(
            label="📥 Download Transcription",
            data=transcription_text,
            file_name=f"{filename}_transcription.txt",
            mime="text/plain"
        )

def render_supabase_setup_instructions():
    """Render Supabase setup instructions."""
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
            improved_text TEXT,
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

def render_transcription_history_item(item: Dict, item_id: str):
    """Render a single transcription history item."""
    # Check if we have an improved version
    has_improved = item.get('improved_text') and item['improved_text'].strip()
    title_icon = "🧠" if has_improved else "🎵"
    
    with st.expander(f"{title_icon} {item['name']} - {item['date']}", expanded=False):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**Original filename:** {item['filename']}")
            st.markdown(f"**Language:** {item['language']}")
            st.markdown(f"**Date:** {item['date']}")
            if has_improved:
                st.markdown("**Status:** ✨ AI-improved version available")

            # Show transcription(s)
            if has_improved:
                # Show tabs for both versions
                tab1, tab2 = st.tabs(["🧠 Improved", "📝 Original"])
                
                with tab1:
                    st.text_area(
                        "Improved transcription",
                        item['improved_text'],
                        height=200,
                        key=f"improved_{item_id}",
                        disabled=True
                    )
                
                with tab2:
                    st.text_area(
                        "Original transcription", 
                        item['text'],
                        height=200,
                        key=f"original_{item_id}",
                        disabled=True
                    )
            else:
                # Show single version
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

            # Determine file extension and MIME type based on output format
            output_format = item.get('output_format', 'text')
            if output_format == 'srt':
                file_ext = 'srt'
                mime_type = 'application/x-subrip'
            else:
                file_ext = 'txt'
                mime_type = 'text/plain'

            if has_improved:
                # Download options for improved version (only for text format)
                if output_format == 'text':
                    st.download_button(
                        label="📥 Improved",
                        data=item['improved_text'],
                        file_name=f"{item['name']}_improved.{file_ext}",
                        mime=mime_type,
                        key=f"download_improved_{item_id}"
                    )
                
                st.download_button(
                    label="📝 Original",
                    data=item['text'],
                    file_name=f"{item['name']}_original.{file_ext}",
                    mime=mime_type,
                    key=f"download_original_{item_id}"
                )
                
                # Download both versions (only for text format)
                if output_format == 'text':
                    both_versions = f"=== IMPROVED VERSION ===\n\n{item['improved_text']}\n\n=== ORIGINAL VERSION ===\n\n{item['text']}"
                    st.download_button(
                        label="📊 Both",
                        data=both_versions,
                        file_name=f"{item['name']}_both.txt",
                        mime="text/plain",
                        key=f"download_both_{item_id}"
                    )
            else:
                # Download button for single version
                download_label = "🎬 Download SRT" if output_format == 'srt' else "📥 Download"
                st.download_button(
                    label=download_label,
                    data=item['text'],
                    file_name=f"{item['name']}_transcription.{file_ext}",
                    mime=mime_type,
                    key=f"download_{item_id}"
                )

            # Delete button
            if st.button("🗑️ Delete", key=f"delete_{item_id}"):
                return True  # Signal to delete this item
    
    return False

def render_export_options(filtered_history: List[Dict]):
    """Render export options for transcription history."""
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
            # Export as text (improved versions when available)
            text_export_parts = []
            for item in filtered_history:
                has_improved = item.get('improved_text') and item['improved_text'].strip()
                if has_improved:
                    text_export_parts.append(
                        f"Name: {item['name']}\nDate: {item['date']}\nLanguage: {item['language']}\nStatus: AI-Improved\n\nImproved Transcription:\n{item['improved_text']}\n\nOriginal Transcription:\n{item['text']}\n\n{'=' * 50}"
                    )
                else:
                    text_export_parts.append(
                        f"Name: {item['name']}\nDate: {item['date']}\nLanguage: {item['language']}\n\nTranscription:\n{item['text']}\n\n{'=' * 50}"
                    )
            
            text_export = "\n\n".join(text_export_parts)
            st.download_button(
                label="📄 Export All History (TXT)",
                data=text_export,
                file_name=f"transcription_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

def render_footer(use_supabase: bool):
    """Render application footer."""
    st.markdown("---")
    st.markdown(
        f"""
        <div style="text-align: center; color: #6B7280; padding: 1rem;">
            <p>Built with Streamlit and OpenAI Whisper v3 | 
            <a href="https://platform.openai.com/docs/guides/speech-to-text" target="_blank" style="color: #3B82F6;">API Documentation</a></p>
            <p style="font-size: 0.875rem; margin-top: 0.5rem;">
            {'📊 Database: Supabase (Cloud)' if use_supabase else '💾 Storage: Session State (Temporary)'}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )