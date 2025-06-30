"""Audio preprocessing functions for silence removal and compression."""

import tempfile
import os
import streamlit as st
from typing import Tuple, Optional
from ..utils.dependencies import safe_import_pydub, safe_import_ffmpeg
from .utils import create_temp_audio_file, load_audio_segment, get_audio_info, cleanup_temp_files, split_audio_by_size, split_audio_by_duration

def remove_silence(audio_segment, silence_thresh: int = -50, min_silence_len: int = 1000):
    """Remove silence from audio using pydub."""
    try:
        AudioSegment, split_on_silence, error = safe_import_pydub()
        if AudioSegment is None:
            raise ImportError(f"pydub not available: {error}")
        
        # Split audio on silence
        chunks = split_on_silence(
            audio_segment,
            min_silence_len=min_silence_len,  # Minimum length of silence to split on (ms)
            silence_thresh=silence_thresh,   # Silence threshold in dBFS
            keep_silence=200  # Keep 200ms of silence at the beginning and end of each chunk
        )
        
        if not chunks:
            return audio_segment
        
        # Combine all chunks
        combined = AudioSegment.empty()
        for chunk in chunks:
            combined += chunk
        
        return combined
    except Exception as e:
        st.warning(f"Silence removal failed: {str(e)}. Using original audio.")
        return audio_segment

def compress_audio_with_ffmpeg(input_path: str, output_path: str) -> bool:
    """Compress audio using ffmpeg with specified settings."""
    try:
        ffmpeg, error = safe_import_ffmpeg()
        if ffmpeg is None:
            raise ImportError(f"ffmpeg-python not available: {error}")
        
        # Use ffmpeg-python to apply the compression
        (
            ffmpeg
            .input(input_path)
            .output(
                output_path,
                vn=None,  # No video
                map_metadata=-1,  # Remove metadata
                ac=1,  # Mono audio
                acodec='libopus',  # Opus codec
                audio_bitrate='12k',  # 12kbps bitrate
                **{'application': 'voip'}  # VoIP application for speech - use dict unpacking for special params
            )
            .overwrite_output()
            .run(quiet=True, capture_stdout=True, capture_stderr=True)
        )
        return True
    except Exception as e:
        if hasattr(e, 'stderr') and e.stderr:
            stderr_output = e.stderr.decode('utf-8') if e.stderr else 'Unknown FFmpeg error'
            st.warning(f"Audio compression failed: {stderr_output}. Using original audio.")
        else:
            st.warning(f"Audio compression failed: {str(e)}. Using original audio.")
        return False

def preprocess_audio(uploaded_file, enable_silence_removal: bool = True, enable_compression: bool = True, enable_time_splitting: bool = True, progress_callback=None) -> Tuple[list, str]:
    """Intelligent audio preprocessing with size-based compression decisions.
    
    Flow:
    1. Load & Remove Silence - reduce duration first
    2. Split by Duration (25min) - absolute API limit  
    3. For each chunk: decide compression based on size
       - If chunk ≤ 25MB → keep as WAV (max quality)
       - If chunk > 25MB → compress to OGG (meet API limit)
    """
    temp_files = []  # Track all temp files for cleanup
    
    try:
        # Progress update helper
        def update_progress(step, message):
            if progress_callback:
                return progress_callback(step, message)
            return True
        
        # Validate input
        if not uploaded_file:
            raise ValueError("No audio file provided")
        
        if not update_progress(20, "📂 Creating temporary files..."):
            return [uploaded_file.read()], uploaded_file.name
        
        # Create temporary input file
        temp_input_path = create_temp_audio_file(uploaded_file)
        temp_files.append(temp_input_path)
        
        if not update_progress(25, "🎵 Loading audio file..."):
            return [uploaded_file.read()], uploaded_file.name
        
        # Load audio and get original stats
        audio_segment = load_audio_segment(temp_input_path)
        original_info = get_audio_info(audio_segment)
        original_size = os.path.getsize(temp_input_path)
        
        # Validate minimum duration
        if original_info['duration_seconds'] < 0.1:
            raise ValueError("Audio file is too short (minimum 0.1 seconds)")
        
        processed_audio = audio_segment
        if not update_progress(30, "✅ Audio file loaded and validated"):
            return [uploaded_file.read()], uploaded_file.name
        
        # Phase 1: Remove silence if enabled (reduces duration first)
        if enable_silence_removal:
            if not update_progress(35, "🔇 Analyzing and removing silence..."):
                return [uploaded_file.read()], uploaded_file.name
            try:
                processed_audio = remove_silence(audio_segment)
                processed_info = get_audio_info(processed_audio)
                
                # Calculate and show silence removal results
                time_saved = original_info['duration_seconds'] - processed_info['duration_seconds']
                if time_saved > 0.1:  # Only show if meaningful reduction
                    reduction_percent = (time_saved / original_info['duration_seconds']) * 100
                    st.success(f"✂️ Removed {time_saved:.1f}s of silence ({reduction_percent:.1f}% reduction)")
                    if not update_progress(45, f"✅ Removed {time_saved:.1f}s of silence"):
                        return [uploaded_file.read()], uploaded_file.name
                else:
                    st.info("No significant silence detected to remove")
                    if not update_progress(45, "✅ Silence analysis completed"):
                        return [uploaded_file.read()], uploaded_file.name
                
            except Exception as e:
                st.warning(f"Silence removal failed: {str(e)}. Using original audio.")
                processed_audio = audio_segment
                if not update_progress(45, "⚠️ Silence removal failed, using original"):
                    return [uploaded_file.read()], uploaded_file.name
        
        # Phase 2: Split by duration (25 minutes) - absolute limit
        max_duration_minutes = 25.0
        processed_duration = get_audio_info(processed_audio)['duration_seconds'] / 60
        
        if enable_time_splitting and processed_duration > max_duration_minutes:
            if not update_progress(50, f"✂️ Splitting by duration ({processed_duration:.1f}min > 25min)..."):
                return [uploaded_file.read()], uploaded_file.name
            
            duration_chunks = split_audio_by_duration(processed_audio, max_duration_minutes)
            st.success(f"✂️ Split audio into {len(duration_chunks)} duration-based chunks")
            
            if not update_progress(55, f"✅ Created {len(duration_chunks)} duration chunks"):
                return [uploaded_file.read()], uploaded_file.name
        else:
            # Single chunk under duration limit
            duration_chunks = [processed_audio]
            if not update_progress(55, "✅ Audio under 25-minute limit, no duration splitting needed"):
                return [uploaded_file.read()], uploaded_file.name
        
        # Phase 3: Intelligent compression decision per chunk
        max_size_bytes = 24900000  # 24.9MB in bytes
        final_chunk_data = []
        final_format = "audio.wav"  # Default format
        chunks_compressed = 0
        chunks_kept_wav = 0
        
        if not update_progress(60, f"🤔 Analyzing {len(duration_chunks)} chunks for compression needs..."):
            return [uploaded_file.read()], uploaded_file.name
        
        for i, chunk in enumerate(duration_chunks):
            chunk_duration = len(chunk) / 1000 / 60  # minutes
            
            # Export chunk to temporary WAV to check size
            temp_chunk_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_files.append(temp_chunk_wav.name)
            chunk.export(temp_chunk_wav.name, format="wav")
            temp_chunk_wav.close()
            
            chunk_size = os.path.getsize(temp_chunk_wav.name)
            chunk_size_mb = chunk_size / (1024 * 1024)
            
            st.info(f"📊 Chunk {i+1}: {chunk_duration:.1f}min, {chunk_size_mb:.1f}MB")
            
            # Decision: compress or keep WAV?
            if chunk_size <= max_size_bytes:
                # Chunk fits in API limit - keep as WAV for maximum quality
                st.success(f"✅ Chunk {i+1}: {chunk_size_mb:.1f}MB ≤ 25MB → Keeping as WAV (max quality)")
                
                with open(temp_chunk_wav.name, 'rb') as f:
                    final_chunk_data.append(f.read())
                chunks_kept_wav += 1
                
            elif enable_compression:
                # Chunk too big - compression required
                st.info(f"🗜️ Chunk {i+1}: {chunk_size_mb:.1f}MB > 25MB → Compressing to OGG")
                
                # Create compressed version
                temp_chunk_ogg = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
                temp_files.append(temp_chunk_ogg.name)
                temp_chunk_ogg.close()
                
                # Compress with FFmpeg
                compression_success = compress_audio_with_ffmpeg(temp_chunk_wav.name, temp_chunk_ogg.name)
                
                if compression_success and os.path.exists(temp_chunk_ogg.name):
                    compressed_size = os.path.getsize(temp_chunk_ogg.name)
                    compressed_size_mb = compressed_size / (1024 * 1024)
                    reduction = ((chunk_size - compressed_size) / chunk_size) * 100
                    
                    st.success(f"📉 Chunk {i+1}: {chunk_size_mb:.1f}MB → {compressed_size_mb:.1f}MB ({reduction:.1f}% reduction)")
                    
                    if compressed_size <= max_size_bytes:
                        # Compression successful - use OGG
                        with open(temp_chunk_ogg.name, 'rb') as f:
                            final_chunk_data.append(f.read())
                        chunks_compressed += 1
                        final_format = "audio.ogg"  # At least one chunk is OGG
                    else:
                        # Still too big after compression - need to split further
                        st.warning(f"⚠️ Chunk {i+1}: Still {compressed_size_mb:.1f}MB after compression > 25MB")
                        st.info(f"🔄 Further splitting chunk {i+1} by size...")
                        
                        # Split this chunk by size and compress each piece
                        sub_chunks = split_audio_by_size(chunk, max_size_bytes)
                        st.info(f"✂️ Split chunk {i+1} into {len(sub_chunks)} sub-chunks")
                        
                        for j, sub_chunk in enumerate(sub_chunks):
                            # Export and compress each sub-chunk
                            temp_sub_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                            temp_sub_ogg = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
                            temp_files.extend([temp_sub_wav.name, temp_sub_ogg.name])
                            
                            sub_chunk.export(temp_sub_wav.name, format="wav")
                            temp_sub_wav.close()
                            temp_sub_ogg.close()
                            
                            if compress_audio_with_ffmpeg(temp_sub_wav.name, temp_sub_ogg.name):
                                with open(temp_sub_ogg.name, 'rb') as f:
                                    final_chunk_data.append(f.read())
                                chunks_compressed += 1
                            else:
                                # Compression failed - use WAV
                                with open(temp_sub_wav.name, 'rb') as f:
                                    final_chunk_data.append(f.read())
                                chunks_kept_wav += 1
                        
                        final_format = "audio.ogg" if chunks_compressed > 0 else "audio.wav"
                else:
                    # Compression failed - use original WAV (might exceed limit)
                    st.warning(f"⚠️ Compression failed for chunk {i+1}, using WAV")
                    with open(temp_chunk_wav.name, 'rb') as f:
                        final_chunk_data.append(f.read())
                    chunks_kept_wav += 1
            else:
                # Compression disabled but chunk too big - split by size
                st.warning(f"⚠️ Chunk {i+1}: {chunk_size_mb:.1f}MB > 25MB but compression disabled")
                st.info(f"✂️ Splitting chunk {i+1} by size to fit API limit...")
                
                sub_chunks = split_audio_by_size(chunk, max_size_bytes)
                st.info(f"✂️ Split chunk {i+1} into {len(sub_chunks)} sub-chunks")
                
                for sub_chunk in sub_chunks:
                    temp_sub_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                    temp_files.append(temp_sub_wav.name)
                    
                    sub_chunk.export(temp_sub_wav.name, format="wav")
                    temp_sub_wav.close()
                    
                    with open(temp_sub_wav.name, 'rb') as f:
                        final_chunk_data.append(f.read())
                    chunks_kept_wav += 1
        
        # Show final summary
        total_chunks = len(final_chunk_data)
        if not update_progress(90, f"✅ Processed {total_chunks} final chunks"):
            return [uploaded_file.read()], uploaded_file.name
        
        if chunks_compressed > 0 and chunks_kept_wav > 0:
            st.info(f"📊 Final result: {chunks_kept_wav} WAV chunks (≤25MB) + {chunks_compressed} OGG chunks (compressed)")
            final_format = "mixed"  # Mixed formats
        elif chunks_compressed > 0:
            st.success(f"📊 Final result: {chunks_compressed} compressed OGG chunks sent to Whisper")
            final_format = "audio.ogg"
        else:
            st.success(f"📊 Final result: {chunks_kept_wav} WAV chunks sent to Whisper (no compression needed)")
            final_format = "audio.wav"
        
        if not update_progress(100, "🎉 Audio preprocessing completed!"):
            return [uploaded_file.read()], uploaded_file.name
        
        return final_chunk_data, final_format
        
    except Exception as e:
        st.error(f"Audio preprocessing failed: {str(e)}")
        # Return original file as fallback
        uploaded_file.seek(0)
        return [uploaded_file.read()], uploaded_file.name
        
    finally:
        # Clean up all temporary files
        cleanup_temp_files(temp_files)