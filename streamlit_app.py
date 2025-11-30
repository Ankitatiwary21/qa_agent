"""
QA Agent - Streamlit Cloud Deployment Version
Combined backend and frontend for single-file deployment
"""

import streamlit as st
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="QA Agent - Test Case & Script Generator",
    page_icon="🧪",
    layout="wide"
)

# Import backend modules
import sys
sys.path.append(os.path.dirname(__file__))

from backend.vector_store import VectorStore
from backend.ingestion import DocumentIngestion
from backend.test_generator import TestCaseGenerator, TestCaseParser
from backend.script_generator import SeleniumScriptGenerator, ScriptParser

# Initialize components (cached)
@st.cache_resource
def init_components():
    vector_store = VectorStore(persist_directory="./chroma_db")
    ingestion = DocumentIngestion(vector_store)
    test_generator = TestCaseGenerator(vector_store)
    script_generator = SeleniumScriptGenerator(vector_store)
    return vector_store, ingestion, test_generator, script_generator

vector_store, ingestion, test_generator, script_generator = init_components()

# Store HTML content
if 'html_content' not in st.session_state:
    st.session_state.html_content = None
if 'test_cases' not in st.session_state:
    st.session_state.test_cases = None
if 'selected_test_case' not in st.session_state:
    st.session_state.selected_test_case = None
if 'generated_script' not in st.session_state:
    st.session_state.generated_script = None

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="main-header">🧪 QA Agent</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Autonomous Test Case & Selenium Script Generator</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📊 System Status")
    st.success("✅ System Ready")
    
    st.divider()
    
    st.header("📚 Knowledge Base")
    doc_count = vector_store.get_document_count()
    st.metric("Documents Indexed", doc_count)
    
    sources = vector_store.get_sources()
    if sources:
        st.write("**Sources:**")
        for source in sources:
            st.write(f"• {source}")
    
    if st.button("🗑️ Clear Knowledge Base"):
        vector_store.clear()
        st.session_state.html_content = None
        st.session_state.test_cases = None
        st.session_state.selected_test_case = None
        st.session_state.generated_script = None
        st.rerun()

# Main tabs
tab1, tab2, tab3 = st.tabs(["📁 Phase 1: Upload & Build", "📝 Phase 2: Test Cases", "🤖 Phase 3: Selenium Scripts"])

# Tab 1: Upload
with tab1:
    st.header("Phase 1: Knowledge Base Ingestion")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Support Documents")
        support_docs = st.file_uploader(
            "Upload documentation files",
            type=['md', 'txt', 'json', 'pdf', 'docx'],
            accept_multiple_files=True,
            key="support_docs"
        )
    
    with col2:
        st.subheader("🌐 HTML File")
        html_file = st.file_uploader(
            "Upload HTML file to test",
            type=['html'],
            key="html_file"
        )
    
    if st.button("🚀 Build Knowledge Base", type="primary", use_container_width=True):
        if not support_docs and not html_file:
            st.warning("Please upload at least one file.")
        else:
            with st.spinner("Building knowledge base..."):
                total_chunks = 0
                
                # Process support docs
                if support_docs:
                    for doc in support_docs:
                        content = doc.read()
                        chunks = ingestion.ingest_file(file_content=content, filename=doc.name)
                        total_chunks += chunks
                
                # Process HTML
                if html_file:
                    html_content = html_file.read()
                    st.session_state.html_content = html_content.decode('utf-8')
                    script_generator.set_html_content(st.session_state.html_content)
                    chunks = ingestion.ingest_html(html_content, html_file.name)
                    total_chunks += chunks
                
                st.success(f"✅ Knowledge base built! {total_chunks} chunks indexed.")
                st.rerun()

# Tab 2: Test Cases
with tab2:
    st.header("Phase 2: Test Case Generation")
    
    if vector_store.get_document_count() == 0:
        st.warning("⚠️ Please build the knowledge base first (Phase 1)")
    else:
        mode = st.radio("Choose mode:", ["Custom Query", "Generate All"], horizontal=True)
        
        if mode == "Custom Query":
            query = st.text_area("Enter your query:", placeholder="Generate test cases for the discount code feature")
            if st.button("🔄 Generate Test Cases", type="primary"):
                if query:
                    with st.spinner("Generating..."):
                        response = test_generator.generate_test_cases(query)
                        st.session_state.test_cases = TestCaseParser.parse_json_response(response)
                        st.success("✅ Test cases generated!")
        else:
            if st.button("🔄 Generate All Test Cases", type="primary"):
                with st.spinner("Generating comprehensive test cases..."):
                    response = test_generator.generate_all_test_cases()
                    st.session_state.test_cases = TestCaseParser.parse_json_response(response)
                    st.success("✅ Test cases generated!")
        
        # Display test cases
        if st.session_state.test_cases:
            st.divider()
            st.subheader("📋 Generated Test Cases")
            
            test_data = st.session_state.test_cases
            
            if isinstance(test_data, dict) and "test_cases" in test_data:
                test_list = test_data["test_cases"]
            elif isinstance(test_data, list):
                test_list = test_data
            else:
                st.code(json.dumps(test_data, indent=2), language="json")
                test_list = []
            
            for i, tc in enumerate(test_list):
                with st.expander(f"**{tc.get('test_id', f'TC-{i+1}')}**: {tc.get('feature', 'N/A')}"):
                    st.write(f"**Scenario:** {tc.get('test_scenario', 'N/A')}")
                    st.write(f"**Expected:** {tc.get('expected_result', 'N/A')}")
                    st.write(f"**Type:** {tc.get('test_type', 'N/A')}")
                    st.write(f"**Source:** {tc.get('grounded_in', 'N/A')}")
                    
                    if st.button(f"🎯 Select", key=f"sel_{i}"):
                        st.session_state.selected_test_case = tc
                        st.success(f"Selected {tc.get('test_id', 'N/A')}")

# Tab 3: Selenium Scripts
with tab3:
    st.header("Phase 3: Selenium Script Generation")
    
    if st.session_state.selected_test_case:
        tc = st.session_state.selected_test_case
        st.info(f"**Selected:** {tc.get('test_id')} - {tc.get('feature')}")
        
        if st.button("⚡ Generate Selenium Script", type="primary", use_container_width=True):
            if not st.session_state.html_content:
                st.error("Please upload HTML file first!")
            else:
                with st.spinner("Generating script..."):
                    script = script_generator.generate_script(tc)
                    clean_script = ScriptParser.extract_python_code(script)
                    st.session_state.generated_script = clean_script
                    st.success("✅ Script generated!")
        
        if st.session_state.generated_script:
            st.divider()
            st.subheader("🐍 Generated Script")
            st.code(st.session_state.generated_script, language="python")
            st.download_button(
                "📥 Download Script",
                st.session_state.generated_script,
                "selenium_test.py",
                "text/plain"
            )
    else:
        st.warning("⚠️ Please select a test case from Phase 2 first.")

# Footer
st.divider()
st.markdown("<center>QA Agent - Built with Streamlit + ChromaDB + Groq LLM</center>", unsafe_allow_html=True)