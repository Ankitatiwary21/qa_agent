"""
Streamlit Frontend for QA Agent
User interface for document upload, test case generation, and script generation
"""

import streamlit as st
import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="QA Agent - Test Case & Script Generator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #28a745;
        border-radius: 5px;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #dc3545;
        border-radius: 5px;
        color: #721c24;
    }
    .info-box {
        padding: 1rem;
        background-color: #cce5ff;
        border: 1px solid #007bff;
        border-radius: 5px;
        color: #004085;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def check_api_status():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_knowledge_base_status():
    """Get knowledge base status from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/status", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


def upload_files(files):
    """Upload multiple files to build knowledge base"""
    try:
        files_data = []
        for file in files:
            files_data.append(("files", (file.name, file.getvalue(), "application/octet-stream")))
        
        response = requests.post(
            f"{API_BASE_URL}/api/build-knowledge-base",
            files=files_data,
            timeout=60
        )
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def generate_test_cases(query):
    """Generate test cases from API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/generate-test-cases",
            json={"query": query, "num_results": 10},
            timeout=120
        )
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def generate_all_test_cases():
    """Generate all test cases"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/generate-all-test-cases",
            timeout=120
        )
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def generate_selenium_script(test_case):
    """Generate Selenium script for a test case"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/generate-selenium-script",
            json={"test_case": test_case},
            timeout=120
        )
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def clear_knowledge_base():
    """Clear the knowledge base"""
    try:
        response = requests.delete(
            f"{API_BASE_URL}/api/clear-knowledge-base",
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Initialize session state
if 'test_cases' not in st.session_state:
    st.session_state.test_cases = None
if 'selected_test_case' not in st.session_state:
    st.session_state.selected_test_case = None
if 'generated_script' not in st.session_state:
    st.session_state.generated_script = None
if 'kb_built' not in st.session_state:
    st.session_state.kb_built = False


# Main UI
st.markdown('<p class="main-header">🧪 QA Agent</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Autonomous Test Case & Selenium Script Generator</p>', unsafe_allow_html=True)

# Sidebar - Status and Controls
with st.sidebar:
    st.header("📊 System Status")
    
    # API Status
    api_status = check_api_status()
    if api_status:
        st.success("✅ API is running")
    else:
        st.error("❌ API is not running")
        st.warning("Start the API with:\n```\nuvicorn backend.main:app --reload\n```")
    
    st.divider()
    
    # Knowledge Base Status
    st.header("📚 Knowledge Base")
    if api_status:
        kb_status = get_knowledge_base_status()
        if kb_status:
            st.metric("Documents Indexed", kb_status.get("document_count", 0))
            sources = kb_status.get("sources", [])
            if sources:
                st.write("**Sources:**")
                for source in sources:
                    st.write(f"  • {source}")
        
        if st.button("🗑️ Clear Knowledge Base", type="secondary"):
            with st.spinner("Clearing..."):
                result = clear_knowledge_base()
                if result.get("status") == "success":
                    st.success("Knowledge base cleared!")
                    st.session_state.kb_built = False
                    st.session_state.test_cases = None
                    st.session_state.selected_test_case = None
                    st.session_state.generated_script = None
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Error: {result.get('message')}")
    
    st.divider()
    
    # Instructions
    st.header("📖 How to Use")
    st.markdown("""
    1. **Upload Documents** - Upload your support docs and HTML file
    2. **Build Knowledge Base** - Click to process documents
    3. **Generate Test Cases** - Enter a query or generate all
    4. **Select Test Case** - Choose one to create script
    5. **Generate Script** - Get executable Selenium code
    """)


# Main content area with tabs
tab1, tab2, tab3 = st.tabs(["📁 Phase 1: Upload & Build", "📝 Phase 2: Test Cases", "🤖 Phase 3: Selenium Scripts"])

# Tab 1: Document Upload
with tab1:
    st.header("Phase 1: Knowledge Base Ingestion")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Support Documents")
        st.write("Upload your documentation files (MD, TXT, JSON, PDF, DOCX)")
        support_docs = st.file_uploader(
            "Choose support documents",
            type=['md', 'txt', 'json', 'pdf', 'docx'],
            accept_multiple_files=True,
            key="support_docs"
        )
        if support_docs:
            st.write(f"**{len(support_docs)} file(s) selected:**")
            for doc in support_docs:
                st.write(f"  • {doc.name}")
    
    with col2:
        st.subheader("🌐 HTML File")
        st.write("Upload the HTML file you want to test")
        html_file = st.file_uploader(
            "Choose HTML file",
            type=['html'],
            accept_multiple_files=False,
            key="html_file"
        )
        if html_file:
            st.write(f"**Selected:** {html_file.name}")
            with st.expander("Preview HTML"):
                st.code(html_file.getvalue().decode('utf-8')[:2000] + "...", language="html")
    
    st.divider()
    
    # Build Knowledge Base Button
    if support_docs or html_file:
        all_files = []
        if support_docs:
            all_files.extend(support_docs)
        if html_file:
            all_files.append(html_file)
        
        if st.button("🚀 Build Knowledge Base", type="primary", use_container_width=True):
            if not api_status:
                st.error("API is not running. Please start the API first.")
            else:
                with st.spinner("Building knowledge base... This may take a moment."):
                    result = upload_files(all_files)
                    
                    if result.get("status") == "success":
                        st.session_state.kb_built = True
                        st.success(f"""
                        ✅ **Knowledge Base Built Successfully!**
                        - Total chunks indexed: {result.get('total_chunks', 0)}
                        - Files ingested: {', '.join(result.get('files_ingested', []))}
                        """)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Error: {result.get('message', 'Unknown error')}")
    else:
        st.info("👆 Please upload at least one document to build the knowledge base.")


# Tab 2: Test Case Generation
with tab2:
    st.header("Phase 2: Test Case Generation")
    
    if not st.session_state.kb_built:
        kb_status = get_knowledge_base_status()
        if kb_status and kb_status.get("document_count", 0) > 0:
            st.session_state.kb_built = True
        else:
            st.warning("⚠️ Please build the knowledge base first (Phase 1)")
    
    if st.session_state.kb_built or (get_knowledge_base_status() or {}).get("document_count", 0) > 0:
        st.subheader("🔍 Generate Test Cases")
        
        generation_mode = st.radio(
            "Choose generation mode:",
            ["Custom Query", "Generate All Test Cases"],
            horizontal=True
        )
        
        if generation_mode == "Custom Query":
            query = st.text_area(
                "Enter your test case query:",
                placeholder="Example: Generate all positive and negative test cases for the discount code feature.",
                height=100
            )
            
            if st.button("🔄 Generate Test Cases", type="primary"):
                if not query:
                    st.warning("Please enter a query.")
                else:
                    with st.spinner("Generating test cases... This may take a minute."):
                        result = generate_test_cases(query)
                        
                        if result.get("status") == "success":
                            st.session_state.test_cases = result
                            st.success("✅ Test cases generated successfully!")
                        else:
                            st.error(f"Error: {result.get('message', 'Unknown error')}")
        
        else:  # Generate All
            if st.button("🔄 Generate All Test Cases", type="primary"):
                with st.spinner("Generating comprehensive test cases... This may take a few minutes."):
                    result = generate_all_test_cases()
                    
                    if result.get("status") == "success":
                        st.session_state.test_cases = result
                        st.success("✅ Test cases generated successfully!")
                    else:
                        st.error(f"Error: {result.get('message', 'Unknown error')}")
        
        # Display Test Cases
        if st.session_state.test_cases:
            st.divider()
            st.subheader("📋 Generated Test Cases")
            
            test_data = st.session_state.test_cases.get("test_cases", {})
            
            # Handle different response formats
            if isinstance(test_data, dict) and "test_cases" in test_data:
                test_cases_list = test_data["test_cases"]
            elif isinstance(test_data, dict) and "raw_response" in test_data:
                st.code(test_data["raw_response"], language="json")
                test_cases_list = []
            elif isinstance(test_data, list):
                test_cases_list = test_data
            else:
                # Show raw response
                raw = st.session_state.test_cases.get("raw_response", "")
                st.code(raw, language="json")
                test_cases_list = []
            
            # Display as cards
            if test_cases_list:
                for i, tc in enumerate(test_cases_list):
                    with st.expander(f"**{tc.get('test_id', f'TC-{i+1}')}**: {tc.get('feature', 'N/A')} - {tc.get('test_scenario', 'N/A')[:50]}..."):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Test ID:** {tc.get('test_id', 'N/A')}")
                            st.write(f"**Feature:** {tc.get('feature', 'N/A')}")
                            st.write(f"**Type:** {tc.get('test_type', 'N/A')}")
                            st.write(f"**Grounded In:** {tc.get('grounded_in', 'N/A')}")
                        
                        with col2:
                            st.write(f"**Scenario:** {tc.get('test_scenario', 'N/A')}")
                            st.write(f"**Expected Result:** {tc.get('expected_result', 'N/A')}")
                        
                        if tc.get('test_steps'):
                            st.write("**Test Steps:**")
                            for step in tc.get('test_steps', []):
                                st.write(f"  • {step}")
                        
                        if st.button(f"🎯 Select for Script Generation", key=f"select_{i}"):
                            st.session_state.selected_test_case = tc
                            st.success(f"Selected: {tc.get('test_id', 'N/A')}")


# Tab 3: Selenium Script Generation
with tab3:
    st.header("Phase 3: Selenium Script Generation")
    
    if st.session_state.selected_test_case:
        st.subheader("📌 Selected Test Case")
        tc = st.session_state.selected_test_case
        
        st.info(f"""
        **Test ID:** {tc.get('test_id', 'N/A')}  
        **Feature:** {tc.get('feature', 'N/A')}  
        **Scenario:** {tc.get('test_scenario', 'N/A')}  
        **Expected Result:** {tc.get('expected_result', 'N/A')}
        """)
        
        if st.button("⚡ Generate Selenium Script", type="primary", use_container_width=True):
            with st.spinner("Generating Selenium script... This may take a minute."):
                result = generate_selenium_script(tc)
                
                if result.get("status") == "success":
                    st.session_state.generated_script = result
                    st.success("✅ Script generated successfully!")
                else:
                    st.error(f"Error: {result.get('message', 'Unknown error')}")
    else:
        st.warning("⚠️ Please select a test case from Phase 2 first.")
        st.info("Go to the 'Test Cases' tab, generate test cases, and click 'Select for Script Generation' on one of them.")
    
    # Display Generated Script
    if st.session_state.generated_script:
        st.divider()
        st.subheader("🐍 Generated Selenium Script")
        
        script_data = st.session_state.generated_script
        script = script_data.get("script", "")
        is_valid = script_data.get("is_valid", False)
        validation_msg = script_data.get("validation_message", "")
        
        # Validation status
        if is_valid:
            st.success(f"✅ {validation_msg}")
        else:
            st.warning(f"⚠️ {validation_msg}")
        
        # Display script
        st.code(script, language="python")
        
        # Download button
        st.download_button(
            label="📥 Download Script",
            data=script,
            file_name="selenium_test_script.py",
            mime="text/plain"
        )
        
        # Copy instructions
        with st.expander("📖 How to Run This Script"):
            st.markdown("""
            1. **Save the script** to a `.py` file
            2. **Install dependencies:**
```bash
               pip install selenium webdriver-manager
```
            3. **Update the HTML path** in the script to point to your actual file
            4. **Run the script:**
```bash
               python selenium_test_script.py
```
            """)


# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>QA Agent - Autonomous Test Case & Selenium Script Generator</p>
    <p>Built with FastAPI + Streamlit + ChromaDB + Groq LLM</p>
</div>
""", unsafe_allow_html=True)