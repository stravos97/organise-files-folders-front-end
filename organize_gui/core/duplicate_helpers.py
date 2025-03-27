import mutagen
import os
from pathlib import Path # Import Path

def score_metadata(file_path):
    """Calculates a score based on metadata completeness."""
    try:
        # Ensure file_path is a Path object or convert it
        file_path_obj = Path(file_path)
        if not file_path_obj.is_file():
             print(f"Warning: score_metadata - File not found or not a file: {file_path}")
             return 0
             
        audio = mutagen.File(file_path_obj)
        if audio is None:
            # print(f"Warning: score_metadata - Could not load audio metadata for: {file_path}")
            return 0 # Return 0 if mutagen can't read it

        score = 0
        # Check for common tag fields
        # ID3 (MP3)
        if hasattr(audio, 'tags') and audio.tags:
            # ID3 tags
            if 'TPE1' in audio: score += 1 # Artist
            if 'TIT2' in audio: score += 1 # Title
            if 'TALB' in audio: score += 1 # Album
            if 'TDRC' in audio or 'TYER' in audio: score += 1 # Year
            if 'TCON' in audio: score += 1 # Genre
            if 'APIC:' in audio or 'APIC' in audio: score += 0.5 # Cover art
        # FLAC/Vorbis comments
        elif hasattr(audio, 'get'): # Check if it behaves like a dictionary
            if audio.get('artist'): score += 1
            if audio.get('title'): score += 1
            if audio.get('album'): score += 1
            if audio.get('date'): score += 1
            if audio.get('genre'): score += 1
            if hasattr(audio, 'pictures') and audio.pictures: score += 0.5
        # MP4/AAC (uses keys like \xa9ART)
        elif hasattr(audio, 'items'): # Check if it has items like a dict
             # Use lowercase keys for comparison as mutagen might return them differently
            lower_keys = {k.lower() for k in audio.keys()}
            if '\xa9art' in lower_keys: score += 1 # Artist
            if '\xa9nam' in lower_keys: score += 1 # Title
            if '\xa9alb' in lower_keys: score += 1 # Album
            if '\xa9day' in lower_keys: score += 1 # Year
            if '\xa9gen' in lower_keys: score += 1 # Genre
            if 'covr' in lower_keys: score += 0.5 # Cover art

        # Add bonus for file size (proxy for quality)
        file_size = os.path.getsize(file_path_obj)
        # Adjust scaling factor if needed, e.g., 10MB = 1 point max
        size_score = min(file_size / 10000000, 1.0) 
        score += size_score

        # print(f"Score for {os.path.basename(file_path)}: {score}")
        return score
    except Exception as e:
        print(f"Error scoring metadata for {file_path}: {e}")
        return 0

def decide_music_duplicate(duplicate, path, **kwargs):
    """
    Decides which music file duplicate to keep based on metadata score.
    Returns True if the current file should be considered the duplicate,
    False if it should be considered the original (better metadata).
    'duplicate' and 'path' are provided by organize-tool.
    """
    try:
        original_path = duplicate["original"]
        current_path = str(path) # path is a Path object from organize-tool

        # Ensure paths exist before scoring
        if not os.path.exists(original_path):
             print(f"Warning: decide_music_duplicate - Original path does not exist: {original_path}")
             return True # Treat current as duplicate if original is missing
        if not os.path.exists(current_path):
             print(f"Warning: decide_music_duplicate - Current path does not exist: {current_path}")
             # This case shouldn't happen if organize-tool is processing it, but handle defensively
             return True 

        original_score = score_metadata(original_path)
        current_score = score_metadata(current_path)

        # print(f"Comparing: '{os.path.basename(current_path)}' (Score: {current_score}) vs Original: '{os.path.basename(original_path)}' (Score: {original_score})")

        # If current file has better metadata, return False (keep current as original)
        if current_score > original_score:
            # print(f"   -> Keeping current '{os.path.basename(current_path)}' as original.")
            return False

        # Otherwise, return True (keep original, mark current as duplicate)
        # print(f"   -> Marking '{os.path.basename(current_path)}' as duplicate.")
        return True
    except Exception as e:
        print(f"Error in decide_music_duplicate for {path}: {e}")
        # Fallback behavior: treat as duplicate if error occurs
        return True
