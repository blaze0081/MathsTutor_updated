import streamlit as st
from openai import OpenAI
import os
import re
import html
import requests
from stringsFormatter import should_skip_text, latex_to_symbols

api_key = st.secrets["openai"]["api_key"]
GOOGLE_API_KEY = st.secrets["google"]["credentials"]

def process_latex_content(answer):
    # Split the text by LaTeX blocks (both \[...\] and \boxed{...})
    parts = re.split(r'(\\\[.*?\\\]|\\\boxed\{.*?\})', answer, flags=re.DOTALL)
    
    for part in parts:
        if part.strip():
            if part.startswith('\\[') and part.endswith('\\]'):
                # Extract content between \[...\]
                math_content = part[2:-2].strip()
                st.latex(math_content)
            elif part.startswith('\\boxed{'):
                # Extract content between \boxed{...}
                math_content = part[7:-1].strip()
                st.latex(f"\\boxed{{{math_content}}}")
            else:
                # Split the text part into lines
                lines = part.split('\n')
                for line in lines:
                    # Only write lines that don't match math patterns
                    if line.strip() and not should_skip_text(line):
                        st.write(line)


def process_math_expressions(text):
    """
    Extracts math expressions from text and replaces them with placeholders
    Returns processed text and a dictionary of replacements
    """
    math_expressions = []
    placeholders = {}
    
    # Find all LaTeX expressions between \[ \] and \boxed{}
    latex_pattern = r'(\\\[.*?\\\]|\\\boxed\{.*?\})'
    
    def replacement(match):
        expr = match.group(1)
        placeholder = f"__MATH_{len(math_expressions)}__"
        math_expressions.append(expr)
        placeholders[placeholder] = expr
        return placeholder
    
    processed_text = re.sub(latex_pattern, replacement, text, flags=re.DOTALL)
    return processed_text, placeholders

def translate_text(text, target_language):
    try:
        if target_language.lower() == 'hindi':
            target_language = 'hi'
            
        url = 'https://translation.googleapis.com/language/translate/v2'
        params = {
            'q': text,
            'target': target_language,
            'key': GOOGLE_API_KEY
        }
        
        response = requests.post(url, params=params)
        
        if response.status_code == 200:
            result = response.json()
            translated_text = html.unescape(
                result['data']['translations'][0]['translatedText']
            )
            return translated_text
        else:
            st.error(f"Translation API error: {response.text}")
            return text
            
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return text

def solve():
    if not st.session_state.question_queue:
        return "No questions selected to solve. Please select questions from the main page."
    
    client = OpenAI(api_key=api_key)
    
    questions = list(st.session_state.question_queue)
    language = st.session_state.language
    prompt = "Please solve the following mathematics questions step by step:\n\n"
    for i, question in enumerate(questions, 1):
        prompt += f"Question {i}: {question}\n"

    system_message = "You are a math tutor."
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "system", "content": prompt}
        ] 
    )
        
    answer = response.choices[0].message.content

    # If translation is needed
    if language == "Hindi":
        # First extract and save all LaTeX expressions
        processed_text, math_placeholders = process_math_expressions(answer)
        
        # Convert remaining LaTeX commands to symbols in the text
        processed_text = latex_to_symbols(processed_text)
        
        # Translate the processed text
        translated_text = translate_text(processed_text, language)
        
        # Restore the original LaTeX expressions
        for placeholder, math_expr in math_placeholders.items():
            translated_text = translated_text.replace(placeholder, math_expr)
        
        answer = translated_text
    
    # Process and display the content
    process_latex_content(answer)
    
    st.session_state.question_queue.clear()
    st.session_state.checked_questions.clear()

