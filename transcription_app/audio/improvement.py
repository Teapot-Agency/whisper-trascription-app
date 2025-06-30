"""Transcript improvement using GPT-4o-mini."""

import openai
import streamlit as st
from typing import Optional

# Focused prompt for transcript improvement
IMPROVEMENT_PROMPT = """You are a transcript correction assistant. Your task is to improve the quality of audio transcriptions by:


GOAL → Deliver a corrected version that is fluent and properly punctuated, while preserving 100 % of the original meaning and sentence count.

STRICT RULES
1. Do NOT add or remove sentences, phrases, or information.
2. Correct spelling, diacritics, homophones, and obvious mis-hearings.
3. Fix grammar and word order only as needed for natural flow.
4. Insert appropriate punctuation and capitalisation.
5. Keep all jargon, proper names, numbers, and measurement units unchanged.
6. Do NOT translate; retain every language exactly as it appears.
7. Preserve existing speaker labels or timestamps if present.
8. Return **only** the improved transcript — no commentary, no Markdown, no code fences.
9. Fix all obvious spelling mistakes (e.g. doviditeľnosť → viditeľnosť).

Input transcript:
{transcript}

Improved transcript:"""

# Second pass prompt for punctuation refinement
PUNCTUATION_PROMPT = """You are a punctuation specialist. Review the following text and make ONLY punctuation and capitalization adjustments.

STRICT RULES:
1. Do NOT change, add, or remove any words whatsoever.
2. ONLY insert, remove, or adjust punctuation marks (. , ; : ! ? " ' - etc.)
3. ONLY adjust capitalization where grammatically required.
4. Ensure proper sentence boundaries and flow.
5. Use appropriate punctuation for lists, quotes, and pauses.
6. Preserve all proper names, numbers, and technical terms exactly as written.
7. Return **only** the punctuation-corrected text — no commentary, no explanations.

Input text:
{transcript}

Punctuation-corrected text:"""

def improve_transcript(transcript: str, api_key: str, cancellation_check=None, progress_callback=None) -> Optional[str]:
    """Improve transcript quality using GPT-4o-mini."""
    try:
        if not transcript or not transcript.strip():
            return None
            
        # Progress update helper
        def update_progress(step, message):
            if progress_callback:
                return progress_callback(step, message)
            return True
        
        # Check for cancellation
        if cancellation_check and cancellation_check():
            return None
            
        if not update_progress(80, "🧠 Preparing to improve transcript..."):
            return None
            
        client = openai.OpenAI(api_key=api_key)
        
        # Split long transcripts into chunks if needed (GPT-4o-mini has token limits)
        max_chunk_length = 8000  # Conservative limit for GPT-4o-mini
        
        if len(transcript) <= max_chunk_length:
            # Single chunk processing with two-pass improvement
            if not update_progress(85, "🔧 Pass 1: Improving content and grammar..."):
                return None
                
            # Pass 1: Content and grammar improvement
            improved = _improve_single_chunk(client, transcript, cancellation_check, IMPROVEMENT_PROMPT)
            
            if improved and not (cancellation_check and cancellation_check()):
                if not update_progress(90, "🔧 Pass 2: Refining punctuation..."):
                    return None
                
                # Pass 2: Punctuation refinement
                final_improved = _improve_single_chunk(client, improved, cancellation_check, PUNCTUATION_PROMPT)
                
                if final_improved and not (cancellation_check and cancellation_check()):
                    if not update_progress(95, "✅ Two-pass improvement completed"):
                        return None
                    st.success("🎉 Transcript improved with two-pass refinement!")
                    return final_improved
                else:
                    # Fallback to first pass if second fails
                    if not update_progress(95, "✅ First-pass improvement completed"):
                        return None
                    st.success("🎉 Transcript improved (first pass only)!")
                    return improved
            
        else:
            # Multi-chunk processing for very long transcripts
            if not update_progress(82, "📄 Processing long transcript in chunks..."):
                return None
                
            improved_chunks = []
            sentences = transcript.split('. ')
            current_chunk = ""
            
            for i, sentence in enumerate(sentences):
                # Check for cancellation
                if cancellation_check and cancellation_check():
                    return None
                    
                if len(current_chunk + sentence) < max_chunk_length:
                    current_chunk += sentence + ". "
                else:
                    # Process current chunk
                    if current_chunk.strip():
                        chunk_progress = 85 + (i / len(sentences)) * 8
                        if not update_progress(int(chunk_progress), f"🔧 Improving chunk {len(improved_chunks)+1}..."):
                            return None
                            
                        improved_chunk = _improve_single_chunk(client, current_chunk.strip(), cancellation_check, IMPROVEMENT_PROMPT)
                        if improved_chunk:
                            improved_chunks.append(improved_chunk)
                        else:
                            improved_chunks.append(current_chunk.strip())
                    
                    current_chunk = sentence + ". "
            
            # Process final chunk
            if current_chunk.strip():
                if not update_progress(93, "🔧 Improving final chunk..."):
                    return None
                    
                improved_chunk = _improve_single_chunk(client, current_chunk.strip(), cancellation_check, IMPROVEMENT_PROMPT)
                if improved_chunk:
                    improved_chunks.append(improved_chunk)
                else:
                    improved_chunks.append(current_chunk.strip())
            
            # Combine improved chunks and apply second pass
            if improved_chunks and not (cancellation_check and cancellation_check()):
                combined_improved = " ".join(improved_chunks)
                
                # Pass 2: Punctuation refinement on combined text
                if not update_progress(94, "🔧 Pass 2: Refining punctuation on combined text..."):
                    return None
                
                # Apply punctuation refinement to the full combined text if not too long
                if len(combined_improved) <= max_chunk_length:
                    final_improved = _improve_single_chunk(client, combined_improved, cancellation_check, PUNCTUATION_PROMPT)
                    if final_improved and not (cancellation_check and cancellation_check()):
                        if not update_progress(95, "✅ Two-pass improvement completed"):
                            return None
                        st.success(f"🎉 Improved transcript with {len(improved_chunks)} chunks and punctuation refinement!")
                        return final_improved
                
                # Fallback if combined text too long for second pass
                if not update_progress(95, "✅ First-pass improvement completed"):
                    return None
                st.success(f"🎉 Improved transcript with {len(improved_chunks)} chunks!")
                return combined_improved
        
        return None
        
    except Exception as e:
        st.error(f"Error improving transcript: {str(e)}")
        return None

def _improve_single_chunk(client, chunk: str, cancellation_check=None, prompt_template=None) -> Optional[str]:
    """Improve a single chunk of transcript using specified prompt."""
    try:
        # Check for cancellation before API call
        if cancellation_check and cancellation_check():
            return None
        
        # Use default prompt if none specified
        if prompt_template is None:
            prompt_template = IMPROVEMENT_PROMPT
            
        # Use stricter parameters for punctuation refinement
        is_punctuation_pass = prompt_template == PUNCTUATION_PROMPT
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user", 
                    "content": prompt_template.format(transcript=chunk)
                }
            ],
            max_tokens = int(len(chunk.split()) * 2.5) + 50,  # Allow roughly 2x original length
            temperature=0.0,  # Low temperature for consistency, minimal creativity
            top_p=1.0 if not is_punctuation_pass else 1.0  # Both use top_p=1 for deterministic results
        )
        
        # Check for cancellation after API call
        if cancellation_check and cancellation_check():
            return None
            
        improved_text = response.choices[0].message.content.strip()
        
        # Basic validation - ensure we got reasonable output
        if improved_text and len(improved_text) > 10:
            return improved_text
        else:
            st.warning("⚠️ AI improvement produced unexpected output, using original")
            return chunk
            
    except Exception as e:
        st.warning(f"⚠️ Chunk improvement failed: {str(e)}, using original")
        return chunk

def estimate_improvement_cost(transcript_length: int) -> dict:
    """Estimate cost for transcript improvement based on length."""
    # GPT-4o-mini pricing (approximate as of 2024)
    input_cost_per_token = 0.000150 / 1000  # $0.00015 per 1K tokens
    output_cost_per_token = 0.000600 / 1000  # $0.0006 per 1K tokens
    
    # Rough estimate: 1 word ≈ 1.3 tokens
    estimated_input_tokens = int(transcript_length * 0.25 * 1.3)  # characters to words to tokens
    estimated_output_tokens = estimated_input_tokens  # Assume similar length output
    
    input_cost = estimated_input_tokens * input_cost_per_token
    output_cost = estimated_output_tokens * output_cost_per_token
    total_cost = input_cost + output_cost
    
    return {
        'estimated_input_tokens': estimated_input_tokens,
        'estimated_output_tokens': estimated_output_tokens,
        'estimated_cost': round(total_cost, 4),
        'input_cost': round(input_cost, 4),
        'output_cost': round(output_cost, 4)
    }