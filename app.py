import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

# 1. CONFIGURATION & SETUP
st.set_page_config(page_title="PhysioGold AI", layout="wide")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Function to extract text from PDF
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

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
    
    # --- DEBUGGING TOOL ---
    if api_key:
        with st.expander("🛠️ Troubleshooting"):
            if st.button("Check Available Models"):
                try:
                    genai.configure(api_key=api_key)
                    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    st.write("Available Models:", models)
                except Exception as e:
                    st.error(f"Error: {e}")

# 3. INITIALIZE AI
if api_key:
    genai.configure(api_key=api_key)
    
    # --- TRYING THE NEWEST MODEL ---
    # If 2.5 fails, use the Troubleshooting tool to find the valid name
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest') 
    except:
        model = genai.GenerativeModel('gemini-pro') # Fallback to standard
    
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
