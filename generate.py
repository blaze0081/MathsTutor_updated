import streamlit as st
from openai import OpenAI
import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.pagesizes import letter
from io import BytesIO
import streamlit.components.v1 as components
from dotenv import load_dotenv

api_key = st.secrets["openai"]["api_key"]
# Initialize OpenAI client at the module level
client = OpenAI(api_key=api_key)

def format_math_content(content):
    """
    Formats mathematical content consistently for both display and download
    """
    # Split into questions and answers sections
    sections = content.split('\n\n')
    formatted_sections = []
    
    current_section = None
    current_items = []
    
    for section in sections:
        if section.strip().startswith('Questions:'):
            if current_section and current_items:
                formatted_sections.append(f"{current_section}\n" + "\n\n".join(current_items))
            current_section = "Questions:"
            current_items = []
        elif section.strip().startswith('Answers:'):
            if current_section and current_items:
                formatted_sections.append(f"{current_section}\n" + "\n\n".join(current_items))
            current_section = "Answers:"
            current_items = []
        else:
            # Process individual questions/answers
            lines = section.strip().split('\n')
            formatted_item = []
            
            for line in lines:
                # Handle question numbers and options
                if re.match(r'^\d+\.', line):
                    if formatted_item:
                        current_items.append('\n'.join(formatted_item))
                        formatted_item = []
                    formatted_item.append(line)
                elif re.match(r'^[a-d]\)', line):
                    formatted_item.append(line)
                elif line.strip().startswith('Steps:'):
                    formatted_item.append('\n' + line)
                else:
                    formatted_item.append(line)
            
            if formatted_item:
                current_items.append('\n'.join(formatted_item))
    
    # Add the last section
    if current_section and current_items:
        formatted_sections.append(f"{current_section}\n" + "\n\n".join(current_items))
    
    return '\n\n'.join(formatted_sections)

def create_pdf(text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom style for mathematical content
    math_style = ParagraphStyle(
        'MathStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=16,
        spaceAfter=12  # Add space after paragraphs
    )
    
    # Create header style
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading1'],
        fontSize=14,
        leading=18,
        spaceAfter=12
    )
    
    story = []
    sections = text.split('\n\n')
    
    for section in sections:
        if section.strip():
            if section.strip().startswith(('Questions:', 'Answers:')):
                # Handle section headers
                story.append(Paragraph(section.split('\n')[0], header_style))
                remaining_content = '\n'.join(section.split('\n')[1:])
                if remaining_content.strip():
                    story.append(Paragraph(remaining_content, math_style))
            else:
                # Handle questions and answers
                story.append(Paragraph(section, math_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

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

def generate():
    # Initialize MathJax
    init_mathjax()
    language = st.session_state.language

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
        if language == "Hindi":
            preset_index = 1
        else:
            preset_index = 0
        
        language = st.selectbox(
            "Language",
            ("English", "Hindi"),
            index=preset_index
        )

    if st.button("Generate Questions"):
        with st.spinner("Generating questions..."):
            system_message = """You are an experienced mathematics teacher. Generate questions similar to the given examples, following these guidelines:
            1. Maintain consistent difficulty level
            2. Include step-by-step solutions where appropriate
            3. For MCQs, include 4 options with one correct answer
            4. Use LaTeX formatting for mathematical expressions (use $ for inline math and $$ for display math)
            5. Number each question clearly
            6. Separate questions and answers clearly"""

            questions = list(st.session_state.question_queue)
            prompt = f"""Based on these example questions:

{chr(10).join(f'Example {i+1}: {q}' for i, q in enumerate(questions))}

Generate {number} new {toughness.lower()} difficulty {question_type} in {language} with the following structure:

Questions:
1. [First question]
2. [Second question]
...

Answers:
1. [Answer to first question with steps]
2. [Answer to second question with steps]
..."""

            try:
                response = client.chat.completions.create(
                    model="gpt-4",  # Fixed the model name from "gpt-4o" to "gpt-4"
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                
                raw_answer = response.choices[0].message.content
                
                # Process the content for better rendering
                processed_content = format_math_content(raw_answer)
                
                # Display the content using Streamlit's markdown
                st.write("### Generated Questions and Solutions")
                # Split content into sections and display with proper spacing
                sections = processed_content.split('\n\n')
                for section in sections:
                    if section.strip():
                        st.markdown(section, unsafe_allow_html=True)
                        st.markdown("&nbsp;")  # Add extra space between sections
                
                # Create download buttons with properly formatted content
                st.download_button(
                    label="Download Questions and Solutions",
                    data=processed_content,
                    file_name="math_questions.txt",
                    mime="text/plain"
                )
                
                # Create and offer PDF download
                pdf = create_pdf(processed_content)
                st.download_button(
                    label="Download PDF",
                    data=pdf,
                    file_name="questions_and_answers.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"An error occurred while generating questions: {str(e)}")
