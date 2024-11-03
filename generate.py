import streamlit as st
from openai import OpenAI
import os
import re
from markdown_pdf import MarkdownPdf, Section
import streamlit.components.v1 as components
from dotenv import load_dotenv
from typing import List

# Get API key from Streamlit secrets
api_key = st.secrets["openai"]["api_key"]

def format_math_content(content: str) -> str:
    """
    Formats mathematical content consistently for both display and download.
    
    Args:
        content: Raw content string containing questions and answers
        
    Returns:
        Formatted content string with consistent structure
    """
    # Split into questions and answers sections
    sections = content.split('\n\n')
    formatted_sections = []
    
    current_section = None
    current_items = []
    
    for section in sections:
        if section.strip().startswith('Questions:') or section.strip().startswith('प्रश्न:'):
            if current_section and current_items:
                formatted_sections.append(f"{current_section}\n" + "\n\n".join(current_items))
            current_section = "Questions:" if "Questions:" in section else "प्रश्न:"
            current_items = []
        elif section.strip().startswith('Answers:') or section.strip().startswith('उत्तर:'):
            if current_section and current_items:
                formatted_sections.append(f"{current_section}\n" + "\n\n".join(current_items))
            current_section = "Answers:" if "Answers:" in section else "उत्तर:"
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
                elif line.strip().startswith('Steps:') or line.strip().startswith('चरण:'):
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
    """Initialize MathJax for rendering LaTeX equations"""
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
        <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.0/es5/tex-mml-chtml.js" async></script>
        """,
        height=0
    )

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

def create_pdf(text: str, filename: str) -> str:
    """
    Creates a PDF from markdown text and returns the filename.
    
    Args:
        text: Markdown text to convert
        filename: Output filename
        
    Returns:
        str: The filename of the created PDF
    """
    try:
        pdf = MarkdownPdf(toc_level=2)
        pdf.add_section(Section(text))
        pdf.save(filename)
        return filename
    except Exception as e:
        raise Exception(f"Error creating PDF: {str(e)}")

def calculate_question_distribution(total_questions: int, num_selected: int) -> List[int]:
    """
    Calculates how many variations to generate for each selected question.
    
    Args:
        total_questions: Total number of questions requested by user
        num_selected: Number of questions selected by user
    
    Returns:
        List of integers representing how many variations to generate for each question
    """
    base_count = total_questions // num_selected
    remainder = total_questions % num_selected
    
    distribution = [base_count] * num_selected
    
    # Distribute remaining questions evenly
    for i in range(remainder):
        distribution[i] += 1
        
    return distribution

def generate():
    """Main function to handle question generation workflow"""
    client = OpenAI(api_key=api_key)

    # Initialize MathJax
    init_mathjax()
    language = st.session_state.language

    if not st.session_state.question_queue:
        error_msg = "कोई प्रश्न नहीं चुना गया है। कृपया मुख्य पृष्ठ से प्रश्न चुनें।" if language == "Hindi" else "No questions selected to generate from. Please select questions from the main page."
        st.error(error_msg)
        return

    title = "समान प्रश्न उत्पन्न करें" if language == "Hindi" else "Generate Similar Questions"
    st.write(f"### {title}")
    
    # Create language-specific difficulty options
    difficulty_options = {
        "English": {
            "labels": ["Same Level", "Harder", "Most Hard"],
            "descriptions": ["Similar to original", "More challenging", "Much more challenging"]
        },
        "Hindi": {
            "labels": ["समान स्तर", "कठिन", "सबसे कठिन"],
            "descriptions": ["मूल प्रश्न के समान", "अधिक चुनौतीपूर्ण", "बहुत अधिक चुनौतीपूर्ण"]
        }
    }

    # Question type mappings
    question_type_map = {
        "Multiple Choice Questions": {
            "Hindi": "बहुविकल्पीय प्रश्न",
            "English": "Multiple Choice Questions"
        },
        "Fill in the Blanks": {
            "Hindi": "रिक्त स्थान भरें",
            "English": "Fill in the Blanks"
        },
        "Short Answer Type": {
            "Hindi": "लघु उत्तरीय प्रश्न",
            "English": "Short Answer Type"
        },
        "True/False": {
            "Hindi": "सही/गलत",
            "English": "True/False"
        }
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Create difficulty selection with descriptions
        difficulty_format = lambda label, desc: f"{label} ({desc})"
        
        current_lang = language
        difficulty_choices = [
            difficulty_format(label, desc) 
            for label, desc in zip(
                difficulty_options[current_lang]["labels"],
                difficulty_options[current_lang]["descriptions"]
            )
        ]
        
        difficulty_label = "कठिनाई स्तर" if language == "Hindi" else "Difficulty Level"
        toughness = st.selectbox(
            difficulty_label,
            difficulty_choices
        )
        # Extract just the label part for use in prompts
        selected_difficulty = toughness.split(" (")[0]
        
        num_label = "उत्पन्न करने के लिए प्रश्नों की संख्या" if language == "Hindi" else "Number of questions to generate"
        num_questions = st.number_input(num_label, 1, 50, 5)

    with col2:
        type_label = "प्रश्न का प्रकार" if language == "Hindi" else "Question Type"
        question_type = st.selectbox(
            type_label,
            ["Multiple Choice Questions", "Fill in the Blanks", "Short Answer Type", "True/False"]
        )
        
        # Set language selection default based on current session state
        preset_index = 1 if language == "Hindi" else 0
        lang_label = "भाषा" if language == "Hindi" else "Language"
        language_selection = st.selectbox(
            lang_label,
            ("English", "Hindi"),
            index=preset_index
        )

    # Create difficulty mapping for prompt generation
    difficulty_map = {
        "Same Level": {"Hindi": "समान स्तर", "English": "Same Level"},
        "Harder": {"Hindi": "कठिन", "English": "Harder"},
        "Most Hard": {"Hindi": "सबसे कठिन", "English": "Most Hard"},
        "समान स्तर": {"Hindi": "समान स्तर", "English": "Same Level"},
        "कठिन": {"Hindi": "कठिन", "English": "Harder"},
        "सबसे कठिन": {"Hindi": "सबसे कठिन", "English": "Most Hard"}
    }

    button_label = "प्रश्न उत्पन्न करें" if language == "Hindi" else "Generate Questions"
    if st.button(button_label):
        spinner_text = "प्रश्न उत्पन्न किए जा रहे हैं... कृपया प्रतीक्षा करें" if language == "Hindi" else "Generating questions... this may take some time"
        with st.spinner(spinner_text):
            questions = list(st.session_state.question_queue)
            distribution = calculate_question_distribution(num_questions, len(questions))
            
            progress_message = "कुल {} प्रश्न {} चयनित प्रश्नों के आधार पर उत्पन्न किए जा रहे हैं" if language == "Hindi" else "Generating {} questions based on {} selected questions"
            st.info(progress_message.format(num_questions, len(questions)))
            progress_bar = st.progress(0)
            
            all_generated_questions = []
            
            # Language-specific system messages
            system_messages = {
                "Hindi": f"""आप एक अनुभवी गणित शिक्षक हैं। दिए गए उदाहरण प्रश्न के समान प्रश्न तैयार करें, निम्नलिखित दिशानिर्देशों का पालन करते हुए:
                1. गणितीय अभिव्यक्तियों के लिए LaTeX का उपयोग करें (इनलाइन गणित के लिए $ और डिस्प्ले गणित के लिए $$ का उपयोग करें)
                2. कठिनाई स्तर '{selected_difficulty}' के अनुसार रखें - यदि मूल प्रश्न का स्तर बदलना है तो उसी विषय पर अधिक जटिल संख्याएँ या परिस्थितियाँ प्रयोग करें
                3. विस्तृत चरण-दर-चरण हल प्रदान करें
                4. प्रत्येक प्रश्न का स्पष्ट अंतिम उत्तर शामिल करें
                5. सभी प्रश्न और उत्तर हिंदी में होने चाहिए""",
                
                "English": f"""You are an experienced mathematics teacher. Generate questions similar to the given examples, following these guidelines:
                1. Use LaTeX formatting for mathematical expressions (use $ for inline math and $$ for display math)
                2. Set difficulty level to '{selected_difficulty}' - if changing from original, use more complex numbers or situations while maintaining the same mathematical concept
                3. Provide detailed step-by-step solutions
                4. Include a clear final answer for each question
                5. All questions and answers should be in English"""
            }

            for i, (question, count) in enumerate(zip(questions, distribution)):
                try:
                    # Language-specific prompts
                    prompts = {
                        "Hindi": f"""इस उदाहरण प्रश्न के आधार पर:

उदाहरण: {question}

{count} नए {difficulty_map[selected_difficulty]["Hindi"]} स्तर के {question_type_map[question_type]["Hindi"]} तैयार करें।
यदि मूल प्रश्न से कठिनाई स्तर बदल रहा है, तो समान गणितीय अवधारणा का उपयोग करते हुए अधिक जटिल संख्याएँ या परिस्थितियाँ प्रयोग करें।
उत्तर को इस प्रकार संरचित करें:

प्रश्न:
1. [पहला प्रश्न]
2. [दूसरा प्रश्न]
...

उत्तर:
1. [पहले प्रश्न का चरण-दर-चरण हल]
2. [दूसरे प्रश्न का चरण-दर-चरण हल]
...""",

                        "English": f"""Based on this example question:

Example: {question}

Generate {count} new {difficulty_map[selected_difficulty]["English"]} level variations.
If changing difficulty from original, use more complex numbers or situations while maintaining the same mathematical concept.
Structure the response as follows:

Questions:
1. [First question]
2. [Second question]
...

Answers:
1. [Step-by-step solution for first question]
2. [Step-by-step solution for second question]
..."""
                    }

                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": system_messages[language_selection]},
                            {"role": "user", "content": prompts[language_selection]}
                        ],
                        temperature=0.7
                    )
                    
                    raw_answer = response.choices[0].message.content
                    all_generated_questions.append(raw_answer)
                    
                    # Update progress
                    progress = (i + 1) / len(questions)
                    progress_bar.progress(progress)
                    
                except Exception as e:
                    error_msg = f"प्रश्न {i+1} के लिए विविधताएँ उत्पन्न करने में त्रुटि:" if language == "Hindi" else f"Error generating variations for question {i+1}:"
                    st.error(f"{error_msg} {str(e)}")
                    continue
            
            # Combine and format all generated questions
            combined_content = "\n\n".join(all_generated_questions)
            processed_content = process_latex_content(combined_content)
            
            # Display content
            header = "उत्पन्न प्रश्न और समाधान" if language == "Hindi" else "Generated Questions and Solutions"
            st.write(f"### {header}")
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
                    download_label = "डाउनलोड PDF" if language_selection == "Hindi" else "Download PDF"
                    st.download_button(
                        label=download_label,
                        data=pdf_data,
                        file_name="questions_and_answers.pdf",
                        mime="application/pdf"
                    )
                os.remove(pdf_filename)  # Clean up
            except Exception as pdf_error:
                error_msg = "PDF बनाने में त्रुटि:" if language == "Hindi" else "Error generating PDF:"
                st.error(f"{error_msg} {str(pdf_error)}")
            
            # Clear progress bar after completion
            progress_bar.empty()
