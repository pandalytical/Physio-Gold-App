import streamlit as st
import google.generativeai as genai

# 1. CONFIGURATION & SETUP
st.set_page_config(page_title="PhysioGold AI", layout="wide")

# --- THE FIX: Initialize Chat History IMMEDIATELY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# 2. SIDEBAR - The "Control Panel"
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3774/3774299.png", width=50)
    st.title("PhysioGold Settings")
    
    # The API Key Input (Secure)
    api_key = st.text_input("Enter Google API Key", type="password")
    
    # The Magic Toggle
    mode = st.radio("Select User Mode:", ["Patient Intake", "Clinician Mentor"])
    
    st.info("⚠️ PROTOTYPE MODE: Do not enter real PII (Names/DOB).")

# 3. INITIALIZE AI (The Brain)
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # System Instructions based on Toggle
    if mode == "Patient Intake":
        system_instruction = """
        ROLE: You are an empathetic Intake Assistant for Physical Therapy. 
        GOAL: Collect Subjective History and 'Way of Life' data (Job, Hobbies, Goals).
        RULES: Use 6th-grade language. Do NOT diagnose. Ask 1 question at a time.
        """
    else: # Clinician Mode
        system_instruction = """
        ROLE: You are an expert Clinical Mentor (PT Specialist).
        GOAL: Analyze data, challenge diagnosis (Socratic method), and check Red Flags.
        RULES: Use medical terminology. Cite JOSPT guidelines. Suggest specific Special Tests with Likelihood Ratios.
        """
else:
    # If no key is provided yet, set a placeholder instruction
    system_instruction = "Please enter an API Key."

# 4. THE MAIN INTERFACE
st.title(f"PhysioGold: {mode} Mode")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Type here..."):
    if not api_key:
        st.error("Please enter an API Key in the sidebar to start.")
    else:
        # User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI Response Logic
        try:
            # Combine system instruction with chat history for context
            full_prompt = system_instruction + "\n\nUser History:\n" 
            for m in st.session_state.messages:
                full_prompt += f"{m['role']}: {m['content']}\n"
            
            with st.chat_message("assistant"):
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                
            # Save AI response
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Error: {e}")
