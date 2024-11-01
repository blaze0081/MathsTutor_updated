import streamlit as st
import json
import os
from collections import deque
from solve import solve
from generate import generate


# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'main'
if 'question_queue' not in st.session_state:
    st.session_state.question_queue = deque()
if 'checked_questions' not in st.session_state:
    st.session_state.checked_questions = set()
if 'language' not in st.session_state:
    st.session_state.language = "Hindi"  # Changed default to Hindi
if 'data' not in st.session_state:
    st.session_state.data = None

# Function to handle checkbox changes
def update_question(question, is_checked):
    if is_checked:
        if question not in st.session_state.question_queue:
            st.session_state.question_queue.append(question)
        st.session_state.checked_questions.add(question)
    else:
        if question in st.session_state.question_queue:
            st.session_state.question_queue.remove(question)
        st.session_state.checked_questions.discard(question)

# Main page
def main_page():

    main_body_logo = "logo.jpeg"
    sidebar_logo = "horizontal.png"

    st.logo(sidebar_logo, icon_image=main_body_logo)
    st.image("logo.jpeg", caption="Padha with AI")

    st.title("Exercise Questions Viewer")
    st.markdown("Select Language and Chapter from sidebar and click Submit")

    # Sidebar for Chapter and Exercise selection
    st.sidebar.title("Select Options")
    
    # Language selection in sidebar
    st.sidebar.header("Select Language")
    language_selection = st.sidebar.radio("", 
        ["***Hindi***", "***English***"], 
        index=0  # Set index to 0 for Hindi as default
    )
    
    # Update session state language (strip asterisks)
    st.session_state.language = language_selection.replace("*", "")

    # Chapter selection in sidebar
    st.sidebar.header("Select Chapter")
    chapter = st.sidebar.selectbox("Chapter Number", list(range(1, 15)))
    
    # Submit button in sidebar
    submit_button = st.sidebar.button("Submit")

    if submit_button:
        if st.session_state.language == "English":
            json_path = f"Class10English/engChapter{chapter}.json"
        else:
            json_path = f"Class10Hindi/hindichapter{chapter}.json"
        
        if os.path.exists(json_path):
            with open(json_path, 'r') as file:
                st.session_state.data = json.load(file)
        else:
            st.error(f"No data found for Chapter {chapter} in {st.session_state.language} language.")
            st.session_state.data = None
    
    if st.session_state.data:
        # List of exercises in the selected chapter
        exercises = [exercise["exercise"] for exercise in st.session_state.data["exercises"]]
        exercise_selected = st.sidebar.selectbox("Select an exercise", exercises)

        # Find the corresponding exercise questions
        for exercise in st.session_state.data["exercises"]:
            if exercise["exercise"] == exercise_selected:
                questions = exercise["questions"]
                break

        # Display the questions interactively with checkboxes
        st.header(f"Exercise {exercise_selected} Questions")
        for i, question in enumerate(questions):
            question_text = f"Question {i + 1}: {question['question']}"
            if "sub_questions" in question:
                for sub_i, sub_question in enumerate(question["sub_questions"]):
                    full_question_text = f"{question_text} {i + 1}.{sub_i + 1} {sub_question}"
                    is_checked = st.checkbox(
                        full_question_text,
                        value=full_question_text in st.session_state.checked_questions,
                        key=f"checkbox_{i}_{sub_i}"
                    )
                    update_question(full_question_text, is_checked)
            if "image"in question:
                 # give logic
                 print("hi")
            else:
                is_checked = st.checkbox(
                    question_text,
                    value=question_text in st.session_state.checked_questions,
                    key=f"checkbox_{i}"
                )
                update_question(question_text, is_checked)

        # Display the selected questions queue
        st.sidebar.subheader("Selected Questions Queue")
        if st.session_state.question_queue:
            for q in st.session_state.question_queue:
                st.sidebar.write(q)
        else:
            st.sidebar.write("No questions selected.")

        # Add "Solve" and "Generate More" buttons
        if st.sidebar.button("Solve", key="solve_button"):
            st.session_state.page = 'solve'
            st.rerun()
        if st.sidebar.button("Generate More", key="generate_button"):
            st.session_state.page = 'generate'
            st.rerun()

# Solve page
def solve_page():
    st.title("Solve")
    solve()
    if st.button("Back", key="back_solve"):
        st.session_state.page = 'main'
        st.rerun()

# Generate More page
def generate_page():
    st.title("Generate More Questions")
    generate()
    if st.button("Back", key="back_generate"):
        st.session_state.page = 'main'
        st.rerun()

# Main app logic
if st.session_state.page == 'main':
    main_page()
elif st.session_state.page == 'solve':
    solve_page()
elif st.session_state.page == 'generate':
    generate_page()