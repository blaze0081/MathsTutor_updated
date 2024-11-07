from pylatexenc.latex2text import LatexNodes2Text
import re

def convert_superscript(text):
    """
    Convert caret notation to Unicode superscript characters.
    
    Args:
        text (str): Text containing caret notation numbers
    Returns:
        str: Text with Unicode superscript numbers
    """
    # Mapping of regular numbers to superscript numbers
    superscript_map = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
    }
    
    def replace_superscript(match):
        number = match.group(1)
        return ''.join(superscript_map.get(digit, digit) for digit in number)
    
    # Replace numbers after ^ with superscript versions
    return re.sub(r'\^(\d+)', replace_superscript, text)

def convert_latex_document(content):
    """
    Convert LaTeX content to plain text using pylatexenc with enhanced superscript handling
    
    Args:
        content (str): Input text containing LaTeX expressions
    Returns:
        str: Converted text with mathematical symbols and proper superscripts
    """
    # Create converter instance
    converter = LatexNodes2Text()
    
    # Function to handle math mode conversions
    def replace_math(match):
        latex_expr = match.group(1) or match.group(2)
        if not latex_expr:
            return match.group(0)
        try:
            # Convert the LaTeX expression to text
            converted = converter.latex_to_text(latex_expr)
            # Handle superscripts in the converted text
            converted = convert_superscript(converted)
            return converted
        except Exception as e:
            print(f"Warning: Could not convert expression '{latex_expr}': {str(e)}")
            return match.group(0)

    # Replace both display math ($$..$$) and inline math ($...$)
    processed_text = re.sub(r'\$\$(.*?)\$\$|\$(.*?)\$', 
                          replace_math, 
                          content, 
                          flags=re.DOTALL)
    
    # Handle any remaining superscripts outside of math mode
    processed_text = convert_superscript(processed_text)
    
    return processed_text

def process_latex_content(content: str) -> str:
    """
    Process and clean LaTeX content for better rendering.
    
    Args:
        content: Raw content containing LaTeX expressions
        
    Returns:
        Processed content with proper LaTeX formatting
    """
    # Replace common LaTeX patterns
    replacements = {
        r'\(': '$',
        r'\)': '$',
        r'\[': '$$',
        r'\]': '$$',
    }
    
    processed_content = content
    for old, new in replacements.items():
        processed_content = processed_content.replace(old, new)
    
    # Split content into sections
    sections = re.split(r'(Questions:|Answers:|प्रश्न:|उत्तर:)', processed_content)
    formatted_content = []
    
    for section in sections:
        if section.strip() in ['Questions:', 'Answers:', 'प्रश्न:', 'उत्तर:']:
            formatted_content.append(f"### {section.strip()}\n")
        else:
            # Process numbered items
            section = re.sub(r'(\d+\.) ', r'\n\1 ', section)
            formatted_content.append(section)
    
    return '\n'.join(formatted_content)
