import streamlit as st
from pypdf import PdfReader
import google.generativeai as genai
import json

# --- 1. Настройки и Инициализация "Памяти" ---
st.set_page_config(page_title="Exam Killer", page_icon="🎓")

# Если в памяти еще нет вопросов, создаем пустое место для них
if 'quiz_data' not in st.session_state:
    st.session_state['quiz_data'] = None

# --- 2. Сайдбар ---
with st.sidebar:
    st.header("🔑 Settings")
    api_key = st.text_input("API Key", type="password")
    
    # Выбор модели
    selected_model = "models/gemini-1.5-flash"
    if api_key:
        try:
            genai.configure(api_key=api_key)
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            if models:
                selected_model = st.selectbox("Model:", models, index=0)
        except:
            pass

# --- 3. Загрузка и Генерация ---
st.title("🎓 Exam Killer")

uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file is not None:
    # Кнопка генерации
    if st.button("🚀 Generate new test"):
        if not api_key:
            st.error("Insert API Key!")
        else:
            with st.spinner("Reading PDF and generating test..."):
                try:
                    # Читаем PDF
                    reader = PdfReader(uploaded_file)
                    text = ""
                    for page in reader.pages[:10]:
                        text += page.extract_text() + "\n"

                    # Запрос к Gemini
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(selected_model)
                    
                    prompt = f"""
                    Make a quiz of 5 questions based on this text.
                    Output MUST be a valid JSON list of dictionaries.
                    Format: [{{"question": "...", "options": ["a", "b", "c", "d"], "answer": "exact_option_text"}}]
                    Text: {text[:5000]}
                    """
                    
                    response = model.generate_content(prompt)
                    clean_json = response.text.replace("```json", "").replace("```", "").strip()
                    
                    # СОХРАНЯЕМ В ПАМЯТЬ (Session State)
                    st.session_state['quiz_data'] = json.loads(clean_json)
                    st.rerun() # Перезагружаем страницу, чтобы отобразить тест

                except Exception as e:
                    st.error(f"Error: {e}")

# --- 4. Отображение Теста (Берем из памяти) ---
if st.session_state['quiz_data']:
    st.write("---")
    st.header("📝 Check Your Answers")
    
    # Форма
    with st.form("quiz_form"):
        user_answers = {}
        score = 0
        
        # Рисуем вопросы
        for i, q in enumerate(st.session_state['quiz_data']):
            st.subheader(f"{i+1}. {q['question']}")
            # Сохраняем выбор пользователя
            user_answers[i] = st.radio("Answer options:", q['options'], key=f"q_{i}")
        
        # Кнопка проверки
        submitted = st.form_submit_button("Check Your Answers")
        
        if submitted:
            for i, q in enumerate(st.session_state['quiz_data']):
                user_choice = user_answers[i]
                correct_answer = q['answer']
                
                if user_choice == correct_answer:
                    score += 1
                    st.success(f"Question {i+1}: Correct! ({user_choice})")
                else:
                    st.error(f"Question {i+1}: Wrong. Your answer: '{user_choice}', correct answer: '{correct_answer}'")
            
            # Итог
            st.write("---")
            if score == 5:
                st.balloons()
                st.markdown(f"### 🏆 Perfect! {score}/5")
            elif score >= 3:
                st.markdown(f"### 😐 Not bad. {score}/5")
            else:
                st.markdown(f"### 💀 Bad. {score}/5")
