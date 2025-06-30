"""Main page rendering logic for the Transcription App."""

import streamlit as st
import uuid
from datetime import datetime
from typing import Optional

from ..config.settings import AppConfig, get_api_key
from ..config.styles import apply_custom_styles, display_header, display_section_title, display_message
from ..database.models import get_db
from ..database.connection import display_database_status, get_database_status
from ..utils.dependencies import display_dependency_status, get_dependency_status
from ..audio.preprocessing import preprocess_audio
from ..audio.transcription import transcribe_audio_chunks, validate_api_key
from ..audio.improvement import improve_transcript
from .components import (
    render_file_uploader, render_transcription_options, render_preprocessing_options,
    render_api_key_section, render_transcription_result, render_supabase_setup_instructions,
    render_transcription_history_item, render_export_options, render_footer
)

def check_system_status(db, api_key):
    """Check overall system status and return issues to display."""
    issues = []
    show_refresh = False
    
    # Check dependencies
    dep_status = get_dependency_status()
    if dep_status['status'] == 'error':
        issues.append({
            'type': 'error',
            'title': 'Dependency Issues Detected',
            'messages': dep_status['issues'],
            'instructions': dep_status['fix_instructions']
        })
    
    # Check database status (only show warning if using session state)
    db_status = get_database_status(db.use_supabase)
    if db_status['status'] == 'warning':
        issues.append({
            'type': 'warning', 
            'title': 'Database Status',
            'messages': [db_status['message']],
            'instructions': ['Configure Supabase for permanent storage (see setup instructions below)']
        })
        show_refresh = True
    
    # Check API key
    if not validate_api_key(api_key):
        issues.append({
            'type': 'error',
            'title': 'API Key Required',
            'messages': ['OpenAI API key is not configured'],
            'instructions': ['Enter your OpenAI API key in the sidebar to use transcription features']
        })
    
    return issues, show_refresh

def display_system_issues(issues, show_refresh=False):
    """Display system issues in a unified error box."""
    if not issues:
        return
    
    # Create unified error container
    st.markdown('<div class="error-container">', unsafe_allow_html=True)
    
    for issue in issues:
        # Determine styling based on issue type
        if issue['type'] == 'error':
            header_class = 'error-box'
            icon = '❌'
        else:
            header_class = 'warning-box'
            icon = '⚠️'
        
        # Display issue header
        st.markdown(f'<div class="{header_class}">{icon} <strong>{issue["title"]}:</strong></div>', unsafe_allow_html=True)
        
        # Display issue messages
        for message in issue['messages']:
            st.markdown(f'<div class="error-detail">• {message}</div>', unsafe_allow_html=True)
        
        # Display fix instructions
        if issue['instructions']:
            st.markdown('<div class="info-box"><strong>How to fix:</strong></div>', unsafe_allow_html=True)
            for instruction in issue['instructions']:
                st.markdown(f'<div class="info-detail">• {instruction}</div>', unsafe_allow_html=True)
        
        st.markdown('<br>', unsafe_allow_html=True)
    
    # Show refresh button if needed
    if show_refresh:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔄 Refresh Status", use_container_width=True):
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_main_page():
    """Render the main transcription page."""
    # Apply custom styles
    apply_custom_styles()
    
    # Display header
    display_header()
    
    # Get database instance and API key
    db = get_db()
    api_key = get_api_key()
    api_key = render_api_key_section(api_key)
    
    # Check system status and only show issues if there are any
    system_issues, show_refresh = check_system_status(db, api_key)
    if system_issues:
        display_system_issues(system_issues, show_refresh)
        
        # Show Supabase setup instructions if database is the issue and not using Supabase
        if not db.use_supabase and any(issue['title'] == 'Database Status' for issue in system_issues):
            render_supabase_setup_instructions()
    
    # Get preprocessing availability (don't display status, just get the boolean)
    dep_status = get_dependency_status()
    preprocessing_available = dep_status['available']
    
    # Main transcription section
    display_section_title("📤 Upload Audio File")
    
    # File uploader
    uploaded_file = render_file_uploader()
    
    # Transcription options
    custom_name, language = render_transcription_options()
    
    # Audio preprocessing options
    enable_silence_removal, enable_compression, enable_time_splitting, enable_transcript_improvement, output_format, transcribe_button = render_preprocessing_options(preprocessing_available)
    
    # Handle transcription
    if transcribe_button and uploaded_file and validate_api_key(api_key):
        handle_transcription(
            uploaded_file, custom_name, language, api_key,
            enable_silence_removal, enable_compression, enable_time_splitting, enable_transcript_improvement, output_format, db
        )
    elif transcribe_button and not validate_api_key(api_key):
        display_message("error", "⚠️ Please configure your OpenAI API key")
    elif transcribe_button and not uploaded_file:
        display_message("error", "⚠️ Please upload an audio file first")
    
    # Render transcription history
    render_history_section(db)

def handle_transcription(uploaded_file, custom_name: str, language: str, api_key: str,
                        enable_silence_removal: bool, enable_compression: bool, enable_time_splitting: bool, enable_transcript_improvement: bool, output_format: str, db):
    """Handle the transcription process with progress bars and cancel option."""
    # Initialize cancellation state
    if 'cancel_transcription' not in st.session_state:
        st.session_state.cancel_transcription = False
    
    # Create progress bar container
    progress_container = st.container()
    
    with progress_container:
        # Main progress bar
        main_progress = st.progress(0)
        progress_text = st.empty()
        
        # Cancel button container
        cancel_container = st.container()
        with cancel_container:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("❌ Cancel Processing", key="cancel_btn", use_container_width=True):
                    st.session_state.cancel_transcription = True
                    st.warning("🛑 Processing cancelled by user")
                    return
        
        # Check for cancellation before each step
        def check_cancellation():
            if st.session_state.cancel_transcription:
                st.session_state.cancel_transcription = False  # Reset for next time
                st.warning("🛑 Processing was cancelled")
                return True
            return False
        
        # Step 1: Initialize
        if check_cancellation():
            return
        main_progress.progress(0.10)
        progress_text.text("🔄 Initializing audio processing...")
        
        # Preprocess audio if any option is enabled
        if enable_silence_removal or enable_compression:
            if check_cancellation():
                return
            main_progress.progress(0.20)
            progress_text.text("🔧 Starting audio preprocessing...")
            
            # Define progress callback for preprocessing
            def preprocessing_progress(step, message):
                if check_cancellation():
                    return False  # Signal to stop processing
                main_progress.progress(step / 100.0)
                progress_text.text(message)
                return True
            
            processed_audio_data_list, processed_filename = preprocess_audio(
                uploaded_file, 
                enable_silence_removal=enable_silence_removal,
                enable_compression=enable_compression,
                enable_time_splitting=enable_time_splitting,
                progress_callback=preprocessing_progress
            )
            
            if check_cancellation():
                return
            main_progress.progress(0.70)
            progress_text.text("✅ Audio preprocessing completed")
        else:
            # Use original audio
            if check_cancellation():
                return
            main_progress.progress(0.30)
            progress_text.text("📂 Loading original audio file...")
            
            uploaded_file.seek(0)
            processed_audio_data_list = [uploaded_file.read()]
            processed_filename = uploaded_file.name
            
            if check_cancellation():
                return
            main_progress.progress(0.50)
            progress_text.text("✅ Audio file loaded")

        # Step 2: Transcription
        if check_cancellation():
            return
        main_progress.progress(0.75)
        progress_text.text("🎤 Preparing for transcription...")
        
        transcription_text = transcribe_audio_chunks(
            processed_audio_data_list,
            processed_filename,
            api_key,
            language,
            response_format=output_format,
            cancellation_check=lambda: st.session_state.cancel_transcription
        )
        
        if check_cancellation():
            return
        main_progress.progress(0.80)
        progress_text.text("✅ Transcription completed successfully!")
        
        # Step 3: Improve transcript if enabled (only for text format)
        improved_text = None
        if transcription_text and enable_transcript_improvement and output_format == "text":
            if check_cancellation():
                return
            main_progress.progress(0.85)
            progress_text.text("🧠 Improving transcript with AI...")
            
            # Define progress callback for improvement (85-95%)
            def improvement_progress(step, message):
                if check_cancellation():
                    return False
                # Convert percentage to 0.0-1.0 range for st.progress()
                # Map improvement progress to 85-95% range
                adjusted_step = 85 + (step - 85) * 0.5 if step > 85 else step
                progress_value = min(95, adjusted_step) / 100.0  # Convert to 0.0-1.0 range
                main_progress.progress(progress_value)
                progress_text.text(message)
                return True
            
            improved_text = improve_transcript(
                transcription_text,
                api_key,
                cancellation_check=lambda: st.session_state.cancel_transcription,
                progress_callback=improvement_progress
            )
        elif transcription_text and enable_transcript_improvement and output_format == "srt":
            # Skip improvement for SRT format and inform user
            main_progress.progress(0.85)
            progress_text.text("ℹ️ SRT format - skipping AI improvement (timestamps preserved)")
            st.info("💡 AI improvement is not applied to SRT format to preserve precise timestamps")
            
            if check_cancellation():
                return
            main_progress.progress(0.95)
            progress_text.text("✅ Transcript improvement completed!")

        if transcription_text:
            # Step 4: Save to database (96-99%)
            if check_cancellation():
                return
            main_progress.progress(0.96)
            progress_text.text("💾 Saving transcription...")
            
            # Create transcription record
            transcription_record = {
                "id": str(uuid.uuid4()),
                "name": custom_name or uploaded_file.name,
                "filename": uploaded_file.name,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "text": transcription_text,
                "improved_text": improved_text,
                "language": language,
                "output_format": output_format
            }

            # Save to database
            if db.add_transcription(transcription_record):
                if check_cancellation():
                    return
                main_progress.progress(0.99)
                progress_text.text("✅ Transcription saved successfully!")
                
                # Final completion - reach 100%
                main_progress.progress(1.0)
                if improved_text:
                    progress_text.text("🎉 Transcription completed, improved, and saved!")
                    display_message("success", "✅ Transcription completed, improved, and saved!")
                else:
                    progress_text.text("🎉 Transcription completed and saved!")
                    display_message("success", "✅ Transcription completed and saved!")
            else:
                # Database save failed, but transcription was successful
                main_progress.progress(1.0)
                if improved_text:
                    progress_text.text("🎉 Transcription completed and improved!")
                    display_message("warning", "⚠️ Transcription completed but save failed. Check database connection.")
                else:
                    progress_text.text("🎉 Transcription completed!")
                    display_message("warning", "⚠️ Transcription completed but save failed. Check database connection.")
            
            # Hide cancel button after ALL processing is complete (regardless of save status)
            cancel_container.empty()

            # Display transcription result
            render_transcription_result(
                transcription_text, 
                custom_name or uploaded_file.name,
                improved_text
            )

def render_history_section(db):
    """Render the transcription history section with pagination."""
    transcription_history = db.get_all_transcriptions()

    if transcription_history:
        display_section_title("📚 Transcription History")
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

        # Get filtered results
        filtered_history = db.search_transcriptions(search_query)
        
        # Pagination settings
        items_per_page = 5
        total_items = len(filtered_history)
        total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
        
        # Initialize page state
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1
        
        # Reset to page 1 if search query changes
        if 'last_search_query' not in st.session_state:
            st.session_state.last_search_query = ""
        
        if search_query != st.session_state.last_search_query:
            st.session_state.current_page = 1
            st.session_state.last_search_query = search_query
        
        # Ensure current page is within bounds
        st.session_state.current_page = max(1, min(st.session_state.current_page, total_pages))
        
        if total_items > 0:
            # Pagination controls
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if st.button("⬅️ Previous", disabled=st.session_state.current_page <= 1):
                    st.session_state.current_page = max(1, st.session_state.current_page - 1)
                    st.rerun()
            
            with col2:
                st.markdown(f'<p style="text-align: center; color: #6B7280; margin: 0.5rem 0;">Page {st.session_state.current_page} of {total_pages}</p>', 
                           unsafe_allow_html=True)
            
            with col3:
                if st.button("➡️ Next", disabled=st.session_state.current_page >= total_pages):
                    st.session_state.current_page = min(total_pages, st.session_state.current_page + 1)
                    st.rerun()
            
            # Calculate items for current page
            start_idx = (st.session_state.current_page - 1) * items_per_page
            end_idx = min(start_idx + items_per_page, total_items)
            current_page_items = filtered_history[start_idx:end_idx]
            
            # Display current page items
            for idx, item in enumerate(current_page_items):
                item_id = item.get('id', str(start_idx + idx))
                should_delete = render_transcription_history_item(item, item_id)
                
                if should_delete:
                    db.delete_transcription(item_id)
                    # Adjust current page if we deleted the last item on the page
                    if len(current_page_items) == 1 and st.session_state.current_page > 1:
                        st.session_state.current_page -= 1
                    st.rerun()
            
            # Export options for current filtered results (not just current page)
            render_export_options(filtered_history)
        else:
            st.markdown('<p style="color: #6B7280; text-align: center; margin: 2rem 0;">No transcriptions match your search.</p>', 
                       unsafe_allow_html=True)

    else:
        display_message("info", "📭 No transcriptions yet. Upload an audio file to get started!")

    # Render footer
    render_footer(db.use_supabase)