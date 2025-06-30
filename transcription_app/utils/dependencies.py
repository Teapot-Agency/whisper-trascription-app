"""Dependency checking and validation utilities."""

import subprocess
import streamlit as st

def safe_import_pydub():
    """Safely import pydub modules with error handling."""
    try:
        from pydub import AudioSegment
        from pydub.silence import split_on_silence
        return AudioSegment, split_on_silence, None
    except Exception as e:
        return None, None, str(e)

def safe_import_ffmpeg():
    """Safely import ffmpeg with error handling."""
    try:
        import ffmpeg
        return ffmpeg, None
    except Exception as e:
        return None, str(e)

def check_dependencies():
    """Check if required dependencies are available."""
    issues = []
    
    # Check pydub
    AudioSegment, split_on_silence, pydub_error = safe_import_pydub()
    if AudioSegment is None:
        if 'audioop' in str(pydub_error) or 'pyaudioop' in str(pydub_error):
            issues.append("pydub requires audioop module (Python 3.13 compatibility issue). Consider using Python 3.11 or 3.12")
        else:
            issues.append(f"pydub not available: {pydub_error}")
    else:
        try:
            # Test basic functionality
            AudioSegment.empty()
        except Exception as e:
            issues.append(f"pydub test failed: {str(e)}")
    
    # Check ffmpeg-python
    ffmpeg, ffmpeg_error = safe_import_ffmpeg()
    if ffmpeg is None:
        issues.append(f"ffmpeg-python not available: {ffmpeg_error}")
    else:
        try:
            # Test basic functionality
            ffmpeg.input('test')
        except Exception as e:
            issues.append(f"ffmpeg-python test failed: {str(e)}")
    
    # Check system ffmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, text=True)
        if 'libopus' not in result.stdout:
            issues.append("FFmpeg installed but libopus codec not available. Please install FFmpeg with opus support.")
    except FileNotFoundError:
        issues.append("FFmpeg not installed on system. Please install FFmpeg.")
    except subprocess.CalledProcessError:
        issues.append("FFmpeg found but not working properly.")
    
    return issues

def get_dependency_status():
    """Get dependency status without displaying UI."""
    dependency_issues = check_dependencies()
    
    if dependency_issues:
        return {
            'status': 'error',
            'available': False,
            'issues': dependency_issues,
            'message': 'Audio preprocessing dependencies missing',
            'fix_instructions': [
                'Install missing packages: pip install -r requirements.txt',
                'Install FFmpeg on your system (see CLAUDE.md for instructions)',
                'Audio preprocessing features will be disabled until dependencies are resolved'
            ]
        }
    else:
        return {
            'status': 'success',
            'available': True,
            'issues': [],
            'message': 'All audio preprocessing dependencies are available'
        }

def display_dependency_status():
    """Display dependency status in the UI (legacy function)."""
    status = get_dependency_status()
    
    if status['status'] == 'error':
        st.markdown('<div class="warning-box">⚠️ <strong>Dependency Issues Detected:</strong></div>', unsafe_allow_html=True)
        for issue in status['issues']:
            st.markdown(f'<div class="error-box">❌ {issue}</div>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="info-box">
        <strong>To fix these issues:</strong><br>
        {'<br>'.join(['• ' + instruction for instruction in status['fix_instructions']])}
        </div>
        """, unsafe_allow_html=True)
        return False
    else:
        st.markdown(f'<div class="success-box">✅ {status["message"]}</div>', unsafe_allow_html=True)
        return True