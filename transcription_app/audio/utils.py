"""Audio utility functions and helpers."""

import tempfile
import os
from typing import Tuple, Optional
from ..utils.dependencies import safe_import_pydub, safe_import_ffmpeg
from ..utils.file_utils import sanitize_filename

def create_temp_audio_file(uploaded_file, prefix: str = "whisper_") -> str:
    """Create a temporary file from uploaded audio data."""
    safe_filename = sanitize_filename(uploaded_file.name)
    
    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=f"_input_{safe_filename}",
        prefix=prefix
    )
    
    uploaded_file.seek(0)
    temp_file.write(uploaded_file.read())
    temp_file.close()
    
    return temp_file.name

def load_audio_segment(file_path: str):
    """Load audio file using pydub with error handling."""
    AudioSegment, split_on_silence, error = safe_import_pydub()
    if AudioSegment is None:
        raise ImportError(f"pydub not available: {error}")
    
    try:
        audio_segment = AudioSegment.from_file(file_path)
        return audio_segment
    except Exception as e:
        raise ValueError(f"Invalid audio file or unsupported format: {str(e)}")

def get_audio_info(audio_segment) -> dict:
    """Get information about audio segment."""
    return {
        'duration_ms': len(audio_segment),
        'duration_seconds': len(audio_segment) / 1000,
        'channels': audio_segment.channels,
        'frame_rate': audio_segment.frame_rate,
        'sample_width': audio_segment.sample_width
    }

def validate_audio_duration(audio_segment, min_duration: float = 0.1) -> Tuple[bool, Optional[str]]:
    """Validate audio duration meets minimum requirements."""
    duration_seconds = len(audio_segment) / 1000
    if duration_seconds < min_duration:
        return False, f"Audio file is too short (minimum {min_duration} seconds)"
    return True, None

def cleanup_temp_files(file_paths: list):
    """Clean up temporary files safely."""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            pass  # Ignore cleanup errors

def split_audio_by_duration(audio_segment, max_duration_minutes: float = 25.0) -> list:
    """Split audio into chunks that don't exceed the duration limit."""
    AudioSegment, split_on_silence, error = safe_import_pydub()
    if AudioSegment is None:
        raise ImportError(f"pydub not available: {error}")
    
    duration_ms = len(audio_segment)
    max_duration_ms = max_duration_minutes * 60 * 1000  # Convert minutes to milliseconds
    
    # If audio is shorter than limit, return as single chunk
    if duration_ms <= max_duration_ms:
        return [audio_segment]
    
    # Split audio into time-based chunks
    chunks = []
    start = 0
    
    while start < duration_ms:
        end = min(start + max_duration_ms, duration_ms)
        chunk = audio_segment[start:end]
        chunks.append(chunk)
        start = end
    
    return chunks

def split_audio_by_size(audio_segment, max_size_bytes: int = 24900000) -> list:
    """Split audio into chunks that don't exceed the size limit."""
    AudioSegment, split_on_silence, error = safe_import_pydub()
    if AudioSegment is None:
        raise ImportError(f"pydub not available: {error}")
    
    # First, try to export the full audio to check size
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_file.close()
    
    try:
        audio_segment.export(temp_file.name, format="wav")
        file_size = os.path.getsize(temp_file.name)
        
        # If file is already small enough, return as single chunk
        if file_size <= max_size_bytes:
            return [audio_segment]
        
        # Calculate number of chunks needed based on file size
        num_chunks_needed = max(2, (file_size + max_size_bytes - 1) // max_size_bytes)
        chunk_duration_ms = len(audio_segment) // num_chunks_needed
        
        # Ensure minimum chunk duration (at least 30 seconds)
        min_chunk_duration_ms = 30 * 1000
        if chunk_duration_ms < min_chunk_duration_ms:
            chunk_duration_ms = min_chunk_duration_ms
        
        # Split audio into time-based chunks
        chunks = []
        start = 0
        
        while start < len(audio_segment):
            end = min(start + chunk_duration_ms, len(audio_segment))
            chunk = audio_segment[start:end]
            
            # Verify chunk size - only adjust if significantly over limit
            temp_chunk = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_chunk.close()
            
            try:
                chunk.export(temp_chunk.name, format="wav")
                chunk_size = os.path.getsize(temp_chunk.name)
                
                # Only split further if chunk is significantly over the limit (> 110% of limit)
                if chunk_size > max_size_bytes * 1.1:
                    # Reduce chunk size more conservatively 
                    reduction_factor = max_size_bytes / chunk_size * 0.9  # 90% of target
                    smaller_duration = int(chunk_duration_ms * reduction_factor)
                    chunk = audio_segment[start:start + smaller_duration]
                    end = start + smaller_duration
                
                chunks.append(chunk)
                start = end
                
            finally:
                os.unlink(temp_chunk.name)
        
        return chunks
        
    finally:
        os.unlink(temp_file.name)

def export_audio_chunk_to_bytes(audio_chunk, format: str = "wav") -> bytes:
    """Export audio chunk to bytes."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}")
    temp_file.close()
    
    try:
        audio_chunk.export(temp_file.name, format=format)
        with open(temp_file.name, 'rb') as f:
            return f.read()
    finally:
        os.unlink(temp_file.name)

def split_audio_combined(audio_segment, max_size_bytes: int = 24900000, max_duration_minutes: float = 25.0) -> list:
    """Split audio by both size and duration limits, whichever is more restrictive."""
    AudioSegment, split_on_silence, error = safe_import_pydub()
    if AudioSegment is None:
        raise ImportError(f"pydub not available: {error}")
    
    # First check duration
    duration_chunks = split_audio_by_duration(audio_segment, max_duration_minutes)
    
    # Then check each duration chunk for size limits
    final_chunks = []
    for chunk in duration_chunks:
        size_chunks = split_audio_by_size(chunk, max_size_bytes)
        final_chunks.extend(size_chunks)
    
    return final_chunks