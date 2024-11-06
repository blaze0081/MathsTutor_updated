import streamlit as st
from openai import OpenAI
import os
import re
from markdown_pdf import MarkdownPdf, Section
import streamlit.components.v1 as components
from typing import List
from latexConvertor import convert_latex_document

# Get API key from Streamlit secrets
api_key = st.secrets["openai"]["api_key"]

from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

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
        "Same as Original": {
            "Hindi": "मूल प्रश्न के समान",
            "English": "Same as Original"
        },
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
            list(question_type_map.keys())
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
                "Hindi": f"""आप एक अनुभवी गणित शिक्षक हैं। दिए गए उदाहरणों की तरह प्रश्न बनाएं और इन नियमों का पालन करें:
                1.	गणितीय अभिव्यक्तियों को लिखने के लिए LaTeX फॉर्मेटिंग का उपयोग करें (इनलाइन गणित के लिए $ और बड़े गणित के लिए $$ का उपयोग करें)।
	            2.	कठिनाई स्तर ‘{selected_difficulty}’ पर सेट करें। अगर कठिनाई स्तर बदलना हो, तो संख्या या स्थिति को और जटिल बनाएं, लेकिन वही गणितीय अवधारणा बनाए रखें।
                3. प्रश्न का प्रारूप निम्नलिखित होना चाहिए:
                    यदि प्रारूप '{question_type_map[question_type]["Hindi"]}' है:
                        - यदि "मूल प्रश्न के समान" चुना गया है, तो मूल प्रश्न का प्रारूप बनाए रखें
                        - यदि "बहुविकल्पीय प्रश्न" चुना गया है, तो प्रत्येक प्रश्न में चार विकल्प दें (a, b, c, d)
                        - यदि "रिक्त स्थान भरें" चुना गया है, तो वाक्य में रिक्त स्थान (_____) छोड़ें
                        - यदि "लघु उत्तरीय प्रश्न" चुना गया है, तो प्रश्न को छोटे उत्तर वाले प्रश्न में बदलें
                        - यदि "सही/गलत" चुना गया है, तो कथन बनाएं जिनका उत्तर सही या गलत में दिया जा सके
                    प्रत्येक प्रारूप के लिए विशिष्ट निर्देश:
                    1. बहुविकल्पीय प्रश्न: 
                        - चारों विकल्प तार्किक और प्रासंगिक होने चाहिए
                        - एक स्पष्ट सही उत्तर होना चाहिए
                        - गलत विकल्प सामान्य गलतियों पर आधारित होने चाहिए
                    2. रिक्त स्थान:
                        - रिक्त स्थान महत्वपूर्ण गणितीय अवधारणा के लिए होना चाहिए
                        - एक से अधिक रिक्त स्थान हो सकते हैं
                        - स्पष्ट संदर्भ प्रदान करें
                    3. लघु उत्तरीय:
                        - प्रश्न विशिष्ट और संक्षिप्त होना चाहिए
                        - उत्तर 2-3 वाक्यों में दिया जा सकना चाहिए
                    4. सही/गलत:
                        - कथन स्पष्ट और असंदिग्ध होना चाहिए
                        - गणितीय अवधारणाओं पर आधारित होना चाहिए
	            4.	प्रश्न देने के बाद उसका चरण-दर-चरण समाधान भी लिखें।
	            5.	समाधान बनाते समय पूरा हल दिखाएं और अंतिम उत्तर को “अंतिम उत्तर: <उत्तर>” के रूप में लिखें।
	            6.	ध्यान रखें कि समाधान का आखिरी कदम उस मान को दिखाए जो अंतिम उत्तर है। अंतिम उत्तर में संख्या होनी चाहिए, किसी अनसुलझे समीकरण के रूप में न हो।
	            7.	समाधान में सबसे पहले उस अवधारणा को सरल शब्दों में समझाएं जो प्रश्न में पूछी जा रही है।
	            8.	किसी अवधारणा को समझाते समय, पहले एक उदाहरण दें और उसके बाद एक उल्टा उदाहरण भी दें। इससे बात और साफ हो जाती है।
	            9.	जब भी कोई समाधान लिखें, तो उसे आसान शब्दों में इस तरह समझाएं कि वह उन बच्चों को भी समझ में आ सके जिन्हें कठिन तकनीकी शब्दों में परेशानी होती है।
	            10.	समाधान को सरल बनाने के लिए स्थानीय आम बोलचाल के शब्दों का उपयोग करें और तकनीकी शब्दों से बचें। यदि तकनीकी शब्द आवश्यक हों, तो उन्हें भी आसान भाषा में समझाएं।
	            11.	किसी भी गलती के लिए समाधान की पुनः जांच करें।
	            12.	हर प्रश्न-समाधान जोड़ी को ‘प्रश्न N:’ से शुरू करें, जहाँ N प्रश्न की संख्या है। प्रश्न को मोटे अक्षरों में लिखें और फिर पूरा समाधान दें।
	            13.	सभी प्रश्न और उत्तर हिंदी में होने चाहिए।""",
                
                "English": f"""You are an experienced mathematics teacher. Generate questions similar to the given examples, following these guidelines:
                1. Use LaTeX formatting for mathematical expressions (use $ for inline math and $$ for display math)
                2. Set difficulty level to '{selected_difficulty}' - if changing from original, use more complex numbers or situations while maintaining the same mathematical concept
                3. The question format should be as follows:
                    If format is '{question_type_map[question_type]["English"]}':
                        - If "Same as Original" is selected, maintain the original question format
                        - If "Multiple Choice Questions" is selected, provide four options (a, b, c, d) for each question
                        - If "Fill in the Blanks" is selected, create sentences with blanks (_____)
                        - If "Short Answer Type" is selected, convert to questions requiring brief answers
                        - If "True/False" is selected, create statements that can be judged as true or false
                    Specific instructions for each format:
                    1. Multiple Choice Questions:
                        - All four options should be logical and relevant
                        - There should be one clear correct answer
                        - Wrong options should be based on common misconceptions
                    2. Fill in the Blanks:
                        - Blanks should test key mathematical concepts
                        - Can have multiple blanks
                        - Provide clear context
                    3. Short Answer:
                        - Questions should be specific and concise
                        - Answer should be possible in 2-3 sentences
                    4. True/False:
                        - Statements should be clear and unambiguous
                        - Should be based on mathematical concepts
                4. After providing the question, also generate its step-by-step solution 
                5. When generating solutions, show complete solution with final answers written as Final Answer: <answer>
                6. Ensure that the last step, with the final value of the variable, is displayed at the end of the solution. The value should be in numbers, do not write an unsolved equation as the final value
                7. Whenever showing the solution, first explain the concept that is being tested by the question in simple terms 
                8. While explaining a concept , besides giving an example, also give a counter-example at the beginning . That always makes things clear
                9. Any time you write a solution,  explain the solution in a way that is extremely easy to understand by children struggling with complex technical terms 
                10. Whenever trying to explain in simple terms : 1. use colloquial local language terms and try to avoid technical terms . When using technical terms , re explain those terms in local colloquial terms 
                11. Recheck the solution for any mistakes
                12. Start each question-solution pair with '**Question N:**' where N is the question number, and reproduce the question in bold letters before following it up with detailed solution
                13. All questions and answers should be in English"""
            }

            for i, (question, count) in enumerate(zip(questions, distribution)):
                try:
                    # Language-specific prompts
                    prompts = {
                        "Hindi": f"""इस उदाहरण प्रश्न के आधार पर:
उदाहरण: {question}: {count} नए {difficulty_map[selected_difficulty]["Hindi"]} स्तर के प्रश्नों को निर्दिष्ट प्रारूप '{question_type_map[question_type]["Hindi"]}' में बनाएं।
यदि मूल प्रश्न से कठिनाई स्तर बदल रहा है, तो समान गणितीय अवधारणा का उपयोग करते हुए अधिक जटिल संख्याएँ या परिस्थितियाँ प्रयोग करें।
उत्तर को इस प्रकार संरचित करें:
प्रश्न:
1. [पहला प्रश्न]
2. [दूसरा प्रश्न]
...
उत्तर:
1. [पहले प्रश्न के लिए आसान भाषा में हर कदम का विस्तार से हल, जिसमें अवधारणाओं को समझाने के लिए उदाहरण और उल्टा उदाहरण भी दिए गए हों।]
2. [दूसरे प्रश्न के लिए आसान भाषा में हर कदम का विस्तार से हल, जिसमें अवधारणाओं को समझाने के लिए उदाहरण और उल्टा उदाहरण भी दिए गए हों।]
...""",

                        "English": f"""Based on this example question:
Example: {question}:Generate {count} new {difficulty_map[selected_difficulty]["English"]} level variations.Create the questions in the specified format '{question_type_map[question_type]["English"]}.
If changing difficulty from original, use more complex numbers or situations while maintaining the same mathematical concept.
Structure the response as follows:
Questions:
1. [First question]
2. [Second question]
...
Answers:
1. [Step-by-step detailed solution in simplest possible language alongwith explanation of underlying concepts using both examples and counter-examples for first question]
2. [Step-by-step detailed solution in simplest possible language alongwith explanation of underlying concepts using both examples and counter-examples for second question]
..."""
                    }

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
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
            formatted_text = convert_latex_document(processed_content)
            try:
                pdf_filename = create_pdf(formatted_text, "questions_and_answers.pdf")
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
