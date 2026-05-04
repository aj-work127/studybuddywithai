import streamlit as st
import database
import rag_engine 
from streamlit_mic_recorder import speech_to_text
from gtts import gTTS
import io
import time
import sqlite3
import pandas as pd
from datetime import datetime
from streamlit_option_menu import option_menu

# 1. Page Configuration
# 1. Page Configuration
st.set_page_config(
    page_title="AI Study Buddy", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded" # 🟢 THIS FORCES THE MENU TO STAY OPEN
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Hide the default Streamlit main menu and footer for a cleaner app look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* 🟢 We removed the 'header hidden' line so you can still use the sidebar toggle if needed */
    
    /* Round the corners of the text inputs and buttons */
    .stTextInput input {
        border-radius: 10px;
    }
    .stButton>button {
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 10px rgba(138, 43, 226, 0.3);
    }
    
    /* Make the chat messages look more like bubbles */
    .stChatMessage {
        border-radius: 15px;
        padding: 10px 15px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)



# 2. Initialize Database
database.init_db()

# 3. Session State Management
if "current_user_id" not in st.session_state:
    st.session_state.current_user_id = 1 
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_quiz" not in st.session_state:
    st.session_state.current_quiz = None
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

# 4. Modern Sidebar Navigation
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135692.png", width=50)
    st.title("Study Buddy AI")
    st.markdown("---")
    
    # Modern Option Menu
    page = option_menu(
        menu_title=None, 
        options=["Smart Chat", "Flashcards", "Quizzes"],
        icons=["chat-left-text-fill", "collection-fill", "list-check"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#8A2BE2", "font-size": "18px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#2C303A"},
            "nav-link-selected": {"background-color": "#2C303A"},
        }
    )
    
    st.markdown("---")
    api_key = st.text_input("Enter Gemini API Key", type="password", help="Get your free key from Google AI Studio")
    if not api_key:
        st.warning("⚠️ API Key required for AI features.")

# ==========================================
# PAGE ROUTING
# ==========================================

if page == "Smart Chat":
    st.title("💬 Smart Document Chat")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.write("### 📚 Study Material")
        uploaded_file = st.file_uploader("Upload a PDF to study", type=["pdf"])
        
        if uploaded_file and api_key:
            if st.button("Process Document", use_container_width=True):
                with st.status("🧠 Processing your study materials...", expanded=True) as status:
                    st.write("Extracting text from PDF...")
                    time.sleep(1) # Slight UI delay 
                    st.write("Chunking concepts...")
                    
                    success, message = rag_engine.process_and_store_document(uploaded_file, api_key)
                    
                    if success:
                        status.update(label="Document fully processed!", state="complete", expanded=False)
                        st.session_state.chat_history = [] 
                        st.toast("Document is ready for chat!", icon="✅") 
                    else:
                        status.update(label="Processing failed.", state="error")
                        st.error(message)
                        
        elif uploaded_file and not api_key:
            st.error("Please enter your API Key in the sidebar.")
            
    with col2:
        st.write("### 🤖 Study Buddy Chat")
        
        # Display the chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
        # Voice and Text Input Logic
        st.write("🎙️ **Click to speak:**")
        voice_input = speech_to_text(language='en', use_container_width=True, just_once=True, key='STT')
        text_input = st.chat_input("...or type your question here")
        
        user_question = voice_input or text_input
        
        if user_question:
            if not api_key:
                st.error("Please enter your API Key in the sidebar to chat.")
            else:
                with st.chat_message("user"):
                    st.markdown(user_question)
                st.session_state.chat_history.append({"role": "user", "content": user_question})
                
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        answer = rag_engine.ask_document(user_question, api_key)
                        st.markdown(answer)
                        
                        # Text to Speech Output
                        try:
                            tts = gTTS(text=answer, lang='en')
                            audio_bytes = io.BytesIO()
                            tts.write_to_fp(audio_bytes)
                            st.audio(audio_bytes, format='audio/mp3', autoplay=True)
                        except Exception as e:
                            st.error(f"Audio generation failed: {e}")
                            
                st.session_state.chat_history.append({"role": "assistant", "content": answer})

elif page == "Flashcards":
    st.title("🃏 Spaced Repetition Flashcards")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.write("### ⚙️ Auto-Generate")
        st.write("Let the AI extract key concepts from your uploaded document.")
        
        if st.button("Generate 5 New Flashcards", use_container_width=True):
            if not api_key:
                st.error("Please enter your API Key in the sidebar.")
            else:
                with st.spinner("Scanning document and generating cards..."):
                    success, result = rag_engine.generate_flashcards(api_key, num_cards=5)
                    
                    if success:
                        conn = sqlite3.connect("data/study_buddy.db")
                        cursor = conn.cursor()
                        today = datetime.now().strftime("%Y-%m-%d")
                        
                        for card in result:
                            cursor.execute('''
                                INSERT INTO Flashcards (topic, front_text, back_text, next_review_date) 
                                VALUES (?, ?, ?, ?)
                            ''', ("Auto-Generated", card['front'], card['back'], today))
                        
                        conn.commit()
                        conn.close()
                        st.success("✅ Flashcards generated and saved!")
                    else:
                        st.error(result)
                        
    with col2:
        st.write("### 🧠 Your Deck")
        
        conn = sqlite3.connect("data/study_buddy.db")
        df = pd.read_sql_query("SELECT card_id, topic, front_text, back_text FROM Flashcards ORDER BY card_id DESC", conn)
        conn.close()
        
        if df.empty:
            st.info("Your deck is empty. Generate some cards to start studying!")
        else:
            for index, row in df.iterrows():
                with st.container(border=True): 
                    st.subheader(f"Q: {row['front_text']}")
                    if st.button("Show Answer", key=f"btn_{row['card_id']}"):
                        st.success(f"**A:** {row['back_text']}")
                    st.caption(f"Topic: {row['topic']}")

elif page == "Quizzes":
    st.title("📝 AI Quiz Generator")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.write("### ⚙️ Quiz Setup")
        st.write("Test your knowledge on the uploaded document.")
        
        if st.button("Generate 5-Question Quiz", use_container_width=True):
            if not api_key:
                st.error("Please enter your API Key in the sidebar.")
            else:
                with st.spinner("Analyzing document and writing questions..."):
                    success, result = rag_engine.generate_quiz(api_key, num_questions=5)
                    if success:
                        st.session_state.current_quiz = result
                        st.session_state.quiz_submitted = False
                        st.success("✅ Quiz ready!")
                    else:
                        st.error(result)
                        
        st.markdown("---")
        st.write("### 📊 Your Past Scores")
        conn = sqlite3.connect("data/study_buddy.db")
        scores_df = pd.read_sql_query("SELECT topic, score, total_questions, date_taken FROM QuizScores ORDER BY score_id DESC", conn)
        conn.close()
        st.dataframe(scores_df, use_container_width=True, hide_index=True)
                        
    with col2:
        st.write("### 🧠 The Quiz")
        
        if st.session_state.current_quiz:
            with st.form("quiz_form"):
                user_answers = {}
                
                for i, q in enumerate(st.session_state.current_quiz):
                    st.write(f"**Question {i+1}:** {q['question']}")
                    user_answers[i] = st.radio(
                        "Select an answer:", 
                        q['options'], 
                        key=f"q_{i}", 
                        index=None 
                    )
                    st.markdown("---")
                
                submitted = st.form_submit_button("Submit Answers")
                
                if submitted:
                    st.session_state.quiz_submitted = True
                    score = 0
                    
                    st.write("### 🎯 Results")
                    for i, q in enumerate(st.session_state.current_quiz):
                        st.write(f"**Q{i+1}: {q['question']}**")
                        
                        user_ans = user_answers[i]
                        correct_ans = q['answer']
                        
                        if user_ans == correct_ans:
                            st.success(f"✅ Your answer: {user_ans}")
                            score += 1
                        else:
                            st.error(f"❌ Your answer: {user_ans}")
                            st.info(f"**Correct answer:** {correct_ans}")
                            
                        st.caption(f"*Explanation: {q['explanation']}*")
                        st.write("")
                    
                    st.metric(label="Final Score", value=f"{score} / {len(st.session_state.current_quiz)}")
                    
                    conn = sqlite3.connect("data/study_buddy.db")
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO QuizScores (user_id, topic, score, total_questions) 
                        VALUES (?, ?, ?, ?)
                    ''', (st.session_state.current_user_id, "Auto-Generated Quiz", score, len(st.session_state.current_quiz)))
                    conn.commit()
                    conn.close()
        else:
            st.info("👈 Click the button on the left to generate a quiz!")