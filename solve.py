import streamlit as st
from openai import OpenAI
import os
import re
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

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
    prompt = f"Please solve the following mathematics questions in {language} step by step:\n\n "
    for i, question in enumerate(questions, 1):
        prompt += f"Question {i}: {question}\n"


    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    raw_answer = response.choices[0].message.content

    # if language == "Hindi":
    #     # Translate the processed text
    #     translated_text = translate_text(raw_answer) 

    #     raw_answer = translated_text
    
    # Process the content for better rendering
    processed_content = process_latex_content(raw_answer)
        
    
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