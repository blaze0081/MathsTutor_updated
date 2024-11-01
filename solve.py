import streamlit as st
from openai import OpenAI
import os
import streamlit.components.v1 as components
from dotenv import load_dotenv

api_key = st.secrets["openai"]["api_key"]

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

def solve():
    # Initialize MathJax first
    init_mathjax()
    
    client = OpenAI(api_key=api_key)
    
    if not st.session_state.question_queue:
        st.error("No questions selected to solve. Please select questions from the main page.")
        return

    # Display selected questions first
    st.write("### Selected Questions")
    for i, question in enumerate(st.session_state.question_queue, 1):
        st.markdown(f"**Question {i}:** {question}")

    st.write("### Solutions")
    
    system_message = """You are an experienced mathematics teacher. Solve the questions given, following these guidelines:
    1. Include step-by-step solutions
    2. Use LaTeX formatting for mathematical expressions (use $ for inline math and $$ for display math)
    3. Show complete solution with final answers written as Final Answer: <answer>
    4. Ensure that the last step, with the final value of the variable, is displayed at the end of the solution. The value should be in numbers, do not write an unsolved equation as the final value
    5. If the question is a word problem, explain the solution in a way that is easy to understand
    6. Recheck the solution for any mistakes
    7. Start each question with '**Question N:**' where N is the question number, and reproduce the question in bold letters"""
    
    prompt = f"Please solve the following mathematics questions in {st.session_state.language} step by step:\n\n"
    for i, question in enumerate(st.session_state.question_queue, 1):
        prompt += f"Question {i}: {question}\n"

    
    with st.spinner("Generating solutions... Please wait"):
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        raw_answer = response.choices[0].message.content
        
        # Display content using Streamlit's markdown
        st.markdown(raw_answer, unsafe_allow_html=True)
            

   
    if st.button("Clear Selected Questions"):
        st.session_state.question_queue.clear()
        st.session_state.checked_questions.clear()
        st.success("Selected questions cleared!")
        st.rerun()





