import re

def normalize_text(text: str) -> str:
    """Sanitizes text for TTS speech synthesis.
    
    Removes null bytes, ASCII control characters, excessive whitespace, and
    strips non-printable characters.
    """
    if not text:
        return ""
    
    # Remove null bytes and ASCII control characters (0x00-0x1F, except \n and \t)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Remove zero-width spaces and non-breaking spaces
    text = text.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '').replace('\ufeff', '')
    
    # Normalize multiple blank spaces while keeping single spaces
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Strip spaces around newlines
    text = re.sub(r'[ \t]*\n[ \t]*', '\n', text)
    
    # Clean up blank lines (more than 2 consecutive newlines into 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()
