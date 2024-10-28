import streamlit as st
from openai import OpenAI
import os
import re
import html
import requests
import streamlit.components.v1 as components

api_key = st.secrets["openai"]["api_key"]
GOOGLE_API_KEY = st.secrets["google"]["credentials"]

# Add MathJax initialization to your Streamlit app
def init_mathjax():
    components.html(
        """
        <script>
            window.MathJax = {
                tex: {
                    inlineMath: [['$', '$'], ['\\(', '\\)']],
                    displayMath: [['$$', '$$'], ['\\[', '\\]']]
                },
                svg: {
                    fontCache: 'global'
                }
            };
        </script>
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        """,
        height=0,
    )

def process_latex_content(content):
    # Function to process and clean LaTeX content
    processed_content = content
    
    # Replace common LaTeX patterns for better rendering
    replacements = {
        r'\(': '$',
        r'\)': '$',
        r'\[': '$$',
        r'\]': '$$',
    }
    
    for old, new in replacements.items():
        processed_content = processed_content.replace(old, new)
    
    # Split content into questions and answers sections
    sections = re.split(r'(Questions:|Answers:)', processed_content)
    formatted_content = []
    
    for section in sections:
        if section.strip() in ['Questions:', 'Answers:']:
            formatted_content.append(f"### {section.strip()}\n")
        else:
            # Process numbered items
            section = re.sub(r'(\d+\.) ', r'\n\1 ', section)
            formatted_content.append(section)
    
    return '\n'.join(formatted_content)

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
    # Initialize MathJax
    init_mathjax()
    

    
    client = OpenAI(api_key=api_key)
    
    system_message = """You are an experienced mathematics teacher. Solve the questions given, following these guidelines:
    1. Include step-by-step solutions where appropriate
    2. Use LaTeX formatting for mathematical expressions (use $ for inline math and $$ for display math)
    3. Number each question clearly
    4. Separate questions and answers clearly"""
    questions = list(st.session_state.question_queue)
    language = st.session_state.language
    prompt = "Please solve the following mathematics questions step by step:\n\n"
    for i, question in enumerate(questions, 1):
        prompt += f"Question {i}: {question}\n"


    response = client.chat.completions.create(
        model="gpt-4-0613",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    raw_answer = response.choices[0].message.content
    
    # Process the content for better rendering
    processed_content = process_latex_content(raw_answer)
    
    # Handle translation if Hindi is selected
    if language == "Hindi":
        # Extract and preserve LaTeX expressions
        latex_expressions = re.findall(r'\$[^$]+\$|\$\$[^$]+\$\$', processed_content)
        # Replace LaTeX with placeholders
        for i, expr in enumerate(latex_expressions):
            processed_content = processed_content.replace(expr, f'LATEX_{i}_')
        
        # Translate the text
        translated_text = translate_text(processed_content, "hi")
        
        # Restore LaTeX expressions
        for i, expr in enumerate(latex_expressions):
            translated_text = translated_text.replace(f'LATEX_{i}_', expr)
        
        processed_content = translated_text
    
    # Display the content using Streamlit's markdown
    st.write("### Generated Questions and Solutions")
    for line in processed_content.split('\n'):
        if line.strip():
            st.markdown(line, unsafe_allow_html=True)

    if st.button("Clear Selected Questions"):
        st.session_state.question_queue.clear()
        st.session_state.checked_questions.clear()
        st.success("Selected questions cleared!")
        st.rerun()

