"""Whisper API integration for audio transcription."""

import openai
import streamlit as st
from typing import Optional
from io import BytesIO
import re

def transcribe_audio_chunks(file_data_list: list, filename: str, api_key: str, language: str = None, response_format: str = "text", cancellation_check=None) -> Optional[str]:
    """Transcribe multiple audio chunks using OpenAI Whisper API and concatenate results."""
    try:
        client = openai.OpenAI(api_key=api_key)

        # Prepare language parameter
        lang_param = None if language == "Auto-detect" else language

        transcriptions = []
        total_chunks = len(file_data_list)
        
        if total_chunks > 1:
            st.info(f"🎤 Processing {total_chunks} audio chunks...")
        
        for i, file_data in enumerate(file_data_list):
            # Check for cancellation before each chunk
            if cancellation_check and cancellation_check():
                st.warning("🛑 Transcription cancelled by user")
                return None
                
            if total_chunks > 1:
                st.info(f"📝 Transcribing chunk {i+1}/{total_chunks}...")
            
            # Create a file-like object from the chunk data
            audio_file = BytesIO(file_data)
            audio_file.name = f"{filename}_chunk_{i+1}" if total_chunks > 1 else filename

            # Transcribe chunk with specified format
            transcript = client.audio.transcriptions.create(
                model="whisper-1",  # This uses Whisper v3
                file=audio_file,
                language=lang_param,
                response_format=response_format
            )

            # Normalize API quirks: always end up with plain text
            if isinstance(transcript, str):
                # SRT/VTT already arrive as strings
                transcriptions.append(transcript)
            else:
                # OpenAI sometimes returns custom objects for other formats.
                # Fall back gracefully if the attribute is ever renamed/missing.
                transcriptions.append(getattr(transcript, "text", str(transcript)))
            
            if total_chunks > 1:
                st.success(f"✅ Chunk {i+1}/{total_chunks} completed")
                
            # Check for cancellation after each chunk
            if cancellation_check and cancellation_check():
                st.warning("🛑 Transcription cancelled by user")
                return None

        # Concatenate all transcriptions
        if total_chunks > 1:
            st.info("🔗 Combining transcriptions from all chunks...")
            
            if response_format == "srt":
                # Combine SRT files with adjusted numbering and timing
                combined_transcript = _combine_srt_transcriptions(transcriptions)
            else:
                # Simple text concatenation for other formats
                combined_transcript = " ".join(transcriptions)
            
            st.success(f"✅ Successfully combined {total_chunks} transcriptions")
            return combined_transcript
        else:
            return transcriptions[0]
            
    except Exception as e:
        st.error(f"Error during transcription: {str(e)}")
        return None

def _combine_srt_transcriptions(srt_chunks: list) -> str:
    """Combine multiple SRT transcription chunks with proper numbering and timing adjustment."""
    combined_entries = []
    entry_counter = 1
    time_offset = 0.0  # Track cumulative time offset
    
    for chunk_idx, srt_content in enumerate(srt_chunks):
        if not srt_content or not srt_content.strip():
            continue
            
        # Parse SRT entries from this chunk
        entries = _parse_srt_entries(srt_content)
        
        for entry in entries:
            # Adjust timing by adding offset from previous chunks
            adjusted_start = entry['start_time'] + time_offset
            adjusted_end = entry['end_time'] + time_offset
            
            # Format the adjusted SRT entry
            combined_entries.append(
                f"{entry_counter}\n"
                f"{_format_srt_time(adjusted_start)} --> {_format_srt_time(adjusted_end)}\n"
                f"{entry['text']}\n"
            )
            entry_counter += 1
        
        # Update time offset for next chunk (estimate based on last entry)
        if entries:
            time_offset = entries[-1]['end_time'] + time_offset
    
    return "\n".join(combined_entries)

def _parse_srt_entries(srt_content: str) -> list:
    """Parse SRT content into structured entries."""
    entries = []
    
    # Split by double newlines to separate entries
    srt_blocks = re.split(r'\n\s*\n', srt_content.strip())
    
    for block in srt_blocks:
        if not block.strip():
            continue
            
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            # Parse timing line (format: 00:00:00,000 --> 00:00:00,000)
            timing_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
            if timing_match:
                start_time = _parse_srt_time(timing_match.group(1))
                end_time = _parse_srt_time(timing_match.group(2))
                text = '\n'.join(lines[2:])  # Join remaining lines as text
                
                entries.append({
                    'start_time': start_time,
                    'end_time': end_time,
                    'text': text
                })
    
    return entries

def _parse_srt_time(time_str: str) -> float:
    """Parse SRT time format (HH:MM:SS,mmm) to seconds."""
    time_parts = time_str.replace(',', '.').split(':')
    hours = float(time_parts[0])
    minutes = float(time_parts[1])
    seconds = float(time_parts[2])
    return hours * 3600 + minutes * 60 + seconds

def _format_srt_time(seconds: float) -> str:
    """Format seconds to SRT time format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')

def validate_api_key(api_key: str) -> bool:
    """Validate if API key is provided."""
    return bool(api_key and api_key.strip())