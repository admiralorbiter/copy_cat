import re

EMOJI_PATTERN = re.compile(
    r"[\U0001F600-\U0001F64F"
    r"\U0001F300-\U0001F5FF"
    r"\U0001F680-\U0001F6FF"
    r"\U0001F700-\U0001F77F"
    r"\U0001F780-\U0001F7FF"
    r"\U0001F800-\U0001F8FF"
    r"\U0001F900-\U0001F9FF"
    r"\U0001FA00-\U0001FA6F"
    r"\U0001FA70-\U0001FAFF"
    r"\U00002600-\U000026FF"
    r"\U00002700-\U000027BF]"
    , re.UNICODE
)

def normalize_text(text: str) -> str:
    """Sanitizes text for natural TTS speech synthesis.
    
    Strips emojis, ASCII control characters, broken UI link linebreaks, table pipe syntax,
    horizontal rule lines, and normalizes tabs into natural speech spaces.
    """
    if not text or not text.strip():
        return ""
    
    # 1. Remove ASCII control characters (except \n and \t)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # 2. Remove zero-width spaces and non-breaking spaces
    text = text.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '').replace('\ufeff', '')
    
    # 3. Strip emojis and decorative symbols
    text = EMOJI_PATTERN.sub('', text)

    # 4. Remove horizontal rules (---, ***, ===)
    text = re.sub(r'^[ \t]*[-*=_]{3,}[ \t]*$', '', text, flags=re.MULTILINE)

    # 5. Fix multi-line UI link artifacts: "Parser (\nparser.py\n)" -> "Parser (parser.py)"
    text = re.sub(r'\([ \t]*\n[ \t]*([^\n]+?)[ \t]*\n[ \t]*\)', r'(\1)', text)

    # 6. Clean standalone isolated parentheses/brackets on lines
    text = re.sub(r'^[ \t]*[\(\)\[\]\{\}][ \t]*$', '', text, flags=re.MULTILINE)

    # 7. Convert Markdown table pipes into comma pauses and tabs into spaces
    text = re.sub(r'[ \t]*\|[ \t]*', ', ', text)
    text = text.replace('\t', ' ')

    # 8. Normalize multiple spaces
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'[ \t]*\n[ \t]*', '\n', text)
    
    # 9. Clean double commas resulting from table formatting ", ," -> ","
    text = re.sub(r'(,\s*)+,', ',', text)

    # 10. Clean up blank lines (more than 2 consecutive newlines into 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()
