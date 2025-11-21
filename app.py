import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

# 1. CONFIGURATION & SETUP
st.set_page_config(page_title="PhysioGold AI", layout="wide")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- HELPER FUNCTIONS ---
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_active_model_name(api_key):
    """Finds the first available model that supports chat."""
    try:
        genai.configure(api_key=api_key)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: # Prefer faster models
                    return m.name
        # If no flash model, return the first valid one
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return m.name
    except:
        return "models/gemini-1.5-flash" # Fallback default

# 2. SIDEBAR - The "Control Panel"
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3774/3774299.png", width=50)
    st.title("PhysioGold Settings")
    
    # Security & Mode
    api_key = st.text_input("Enter Google API Key", type="password")
    mode = st.radio("Select User Mode:", ["Patient Intake", "Clinician Mentor"])
    
    st.divider()
    
    # KNOWLEDGE BASE UPLOADER
    st.subheader("📚 Knowledge Base")
    uploaded_files = st.file_uploader("Upload APTA/FSBPT PDFs", accept_multiple_files=True, type="pdf")
    
    # --- DEBUG INFO ---
    if api_key:
        active_model = get_active_model_name(api_key)
        st.caption(f"🟢 Connected to: {active_model}")

# 3. INITIALIZE AI
if api_key:
    genai.configure(api_key=api_key)
    
    # Auto-select the working model found above
    try:
        model = genai.GenerativeModel(active_model)
    except:
        st.error("Could not connect to Google AI. Check your API Key.")
    
    # Process Uploaded PDFs
    knowledge_base_text = ""
    if uploaded_files:
        with st.spinner("Reading Guidelines..."):
            knowledge_base_text = get_pdf_text(uploaded_files)
            st.success("Guidelines Loaded!")

    # Dynamic System Instructions
    base_instruction = ""
    if mode == "Patient Intake":
        base_instruction = """
        ROLE: You are an empathetic Intake Assistant. 
        GOAL: Collect Subjective History and 'Way of Life' data (Job, Hobbies).
        RULES: Use 6th-grade language. Do NOT diagnose. Ask 1 question at a time.
        """
    else: # Clinician Mode
        base_instruction = """
        ROLE: You are an expert Clinical Mentor.
        GOAL: Analyze data, challenge diagnosis, and check Red Flags.
        RULES: Use medical terminology. Cite specific evidence from the provided Reference Documents.
        """
    
    # INJECT THE KNOWLEDGE
    if knowledge_base_text:
        system_instruction = base_instruction + f"\n\nIMPORTANT REFERENCE DOCUMENTS (Adhere strictly to these):\n{knowledge_base_text}"
    else:
        system_instruction = base_instruction

else:
    system_instruction = "Please enter API Key."

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
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            full_prompt = system_instruction + "\n\nUser History:\n" 
            for m in st.session_state.messages:
                full_prompt += f"{m['role']}: {m['content']}\n"
            
            with st.chat_message("assistant"):
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Error: {e}")
