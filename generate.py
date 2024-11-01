import streamlit as st
from openai import OpenAI
import os
import re
from markdown_pdf import MarkdownPdf, Section
import streamlit.components.v1 as components

api_key = st.secrets["openai"]["api_key"]



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

def create_pdf(text, filename):
    """
    Creates a PDF from markdown text and returns the filename
    
    Args:
        text (str): Markdown text to convert
        filename (str): Output filename
        
    Returns:
        str: The filename of the created PDF
    """
    pdf = MarkdownPdf(toc_level=2)
    pdf.add_section(Section(text))
    pdf.save(filename)
    return filename  # Return the filename instead of the PDF object

def generate():
    client = OpenAI(api_key=api_key)

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
        
        number = st.number_input("Number of questions to generate", 1, 10, 5)

    # with col2:
    #     question_type = st.selectbox(
    #         "Question Type",
    #         ("Multiple Choice Questions", "Fill in the Blanks", "Short Answer Type", "True/False")
    #     )
    #     if language == "Hindi":
    #         preset_index = 1
    #     else:
    #         preset_index = 0
        
    #     language = st.selectbox(
    #         "Language",
    #         ("English", "Hindi"),
    #         index=preset_index
    #     )

    if st.button("Generate Questions"):
        with st.spinner("Generating questions... this may take some time"):
            system_message = """You are an experienced mathematics teacher. Generate questions similar to the given examples, following these guidelines:
            1. Use LaTeX formatting for mathematical expressions (use $ for inline math and $$ for display math)
            """

            questions = list(st.session_state.question_queue)
            prompt = f"""Based on these example questions:

{chr(10).join(f'Example {i+1}: {q}' for i, q in enumerate(questions))}

Generate {number} new {toughness.lower()} difficulty questions with the following structure:

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
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                
                raw_answer = response.choices[0].message.content
                
                # if language == "Hindi":
                # # Translate the processed text
                #     translated_text = translate_text(raw_answer, language) 

                #     raw_answer = translated_text

                processed_content = process_latex_content(raw_answer)
                
                # Display content
                st.write("### Generated Questions and Solutions")
                sections = processed_content.split('\n\n')
                for section in sections:
                    if section.strip():
                        st.markdown(section, unsafe_allow_html=True)
                        st.markdown("&nbsp;")
                 
                
                # PDF generation and download
                try:
                    pdf_filename = create_pdf(processed_content, "questions_and_answers.pdf")
                    with open(pdf_filename, "rb") as pdf_file:
                        pdf_data = pdf_file.read()
                        st.download_button(
                            label="Download PDF",
                            data=pdf_data,
                            file_name="questions_and_answers.pdf",
                            mime="application/pdf"
                        )
                    os.remove(pdf_filename)  # Clean up
                except Exception as pdf_error:
                    st.error(f"Error generating PDF: {str(pdf_error)}")
                
            except Exception as e:
                st.error(f"An error occurred while generating questions: {str(e)}")