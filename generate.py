import streamlit as st
from openai import OpenAI
import os
import re
import html
import requests
from stringsFormatter import should_skip_text, latex_to_symbols

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API")

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

def generate():
    if not st.session_state.question_queue:
        st.error("No questions selected to solve. Please select questions from the main page.")
        return

    st.write("### Generate Similar Questions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        toughness = st.selectbox(
            "Difficulty Level",
            ("Easy", "Medium", "Hard")
        )
        
        number = st.number_input("Number of questions to generate", 1, 50, 5)

    with col2:
        question_type = st.selectbox(
            "Question Type",
            ("Multiple Choice Questions", "Fill in the Blanks", "Short Answer Type", "True/False")
        )
        
        language = st.selectbox(
            "Language",
            ("English", "Hindi")
        )

    if st.button("Generate Questions"):
        with st.spinner("Generating questions..."):
            client = OpenAI(api_key=api_key)
            
            # Create a clear system message for context
            system_message = """You are an experienced mathematics teacher. Generate questions similar to the given examples, following these guidelines:
            1. Maintain consistent difficulty level
            2. Include step-by-step solutions where appropriate
            3. For MCQs, include 4 options with one correct answer
            4. Use LaTeX formatting for mathematical expressions
            5. Number each question clearly
            6. Separate questions and answers clearly"""

            # Create a structured prompt with the selected questions
            questions = list(st.session_state.question_queue)
            prompt = f"""Based on these example questions:

{chr(10).join(f'Example {i+1}: {q}' for i, q in enumerate(questions))}

Generate {number} new {toughness.lower()} difficulty {question_type} with the following structure:

Questions:
1. [First question]
2. [Second question]
...

Answers:
1. [Answer to first question with steps]
2. [Answer to second question with steps]
..."""

            try:
                # Make the API call
                response = client.chat.completions.create(
                    model="gpt-4o-mini",  # Make sure to use an appropriate model
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                
                answer = response.choices[0].message.content

                # Handle translation if Hindi is selected
                if language == "Hindi":
                    # First extract and save all LaTeX expressions
                    processed_text, math_placeholders = process_math_expressions(answer)
                    
                    # Convert remaining LaTeX commands to symbols in the text
                    processed_text = latex_to_symbols(processed_text)
                    
                    # Translate the processed text
                    translated_text = translate_text(processed_text, "hi")
                    
                    # Restore the original LaTeX expressions
                    for placeholder, math_expr in math_placeholders.items():
                        translated_text = translated_text.replace(placeholder, math_expr)
                    
                    answer = translated_text

                st.write("### Generated Questions and Solutions")
                process_latex_content(answer)
                
                # Add download button for the generated content
                st.download_button(
                    label="Download Questions and Solutions",
                    data=answer,
                    file_name="math_questions.txt",
                    mime="text/plain"
                )

            except Exception as e:
                st.error(f"An error occurred while generating questions: {str(e)}")

    # Clear the question queue if requested
    if st.button("Clear Selected Questions"):
        st.session_state.question_queue.clear()
        st.session_state.checked_questions.clear()
        st.success("Selected questions cleared!")
        st.rerun()