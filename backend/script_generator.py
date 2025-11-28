"""
Selenium Script Generator Module
Generates executable Python Selenium scripts from test cases
"""

import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SeleniumScriptGenerator:
    """Generates Selenium Python scripts from test cases"""
    
    def __init__(self, vector_store):
        """
        Initialize the script generator
        
        Args:
            vector_store: VectorStore instance for retrieving context
        """
        self.vector_store = vector_store
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        self.html_content = None
    
    def set_html_content(self, html_content):
        """
        Set the HTML content for script generation
        
        Args:
            html_content: The full HTML content of the page to test
        """
        self.html_content = html_content
    
    def generate_script(self, test_case):
        """
        Generate a Selenium script for a given test case
        
        Args:
            test_case: Dictionary containing test case details
            
        Returns:
            Generated Python Selenium script as string
        """
        # Get relevant documentation
        feature = test_case.get('feature', '')
        scenario = test_case.get('test_scenario', '')
        query = f"{feature} {scenario}"
        
        relevant_docs = self.vector_store.search(query, n_results=5)
        context = self._build_context(relevant_docs)
        
        # Create prompt
        prompt = self._create_script_prompt(test_case, context)
        
        # Generate script
        script = self._call_llm(prompt)
        
        return script
    
    def _build_context(self, documents):
        """Build context string from retrieved documents"""
        if not documents:
            return "No additional context available."
        
        context_parts = []
        for doc in documents:
            source = doc['metadata'].get('source', 'Unknown')
            content = doc['content']
            context_parts.append(f"[Source: {source}]\n{content}")
        
        return "\n\n".join(context_parts)
    
    def _create_script_prompt(self, test_case, context):
        """Create the prompt for Selenium script generation"""
        
        test_case_str = f"""
Test ID: {test_case.get('test_id', 'N/A')}
Feature: {test_case.get('feature', 'N/A')}
Test Scenario: {test_case.get('test_scenario', 'N/A')}
Preconditions: {test_case.get('preconditions', [])}
Test Steps: {test_case.get('test_steps', [])}
Test Data: {test_case.get('test_data', 'N/A')}
Expected Result: {test_case.get('expected_result', 'N/A')}
Test Type: {test_case.get('test_type', 'N/A')}
"""
        
        prompt = f"""You are an expert Selenium Python automation engineer. Generate a complete, runnable Selenium Python script for the following test case.

TEST CASE:
{test_case_str}

HTML STRUCTURE OF THE PAGE:
```html
{self.html_content if self.html_content else 'HTML not provided'}
```

ADDITIONAL CONTEXT FROM DOCUMENTATION:
{context}

REQUIREMENTS:
1. Use Python with Selenium WebDriver
2. Use appropriate selectors (prefer ID, then name, then CSS selector)
3. Include proper waits (WebDriverWait, expected_conditions)
4. Add assertions to verify expected results
5. Include setup and teardown
6. Add comments explaining each step
7. Handle potential exceptions
8. Make the script completely runnable

Generate a complete Python script following this structure:
```python
\"\"\"
Selenium Test Script
Test ID: [test_id]
Feature: [feature]
Scenario: [scenario]
\"\"\"

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

class Test[FeatureName]:
    def setup_method(self):
        # Setup code
        pass
    
    def teardown_method(self):
        # Teardown code
        pass
    
    def test_[test_name](self):
        # Test implementation
        pass

if __name__ == "__main__":
    # Run the test
    pass
```

Generate the complete, working script:"""

        return prompt
    
    def _call_llm(self, prompt):
        """Call the Groq LLM API"""
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Selenium automation engineer. Generate clean, working Python Selenium scripts. Only output the Python code without additional explanation."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.2,
                max_tokens=4000
            )
            
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            return f"# Error generating script: {str(e)}"
    
    def generate_script_from_text(self, test_description):
        """
        Generate a Selenium script from a text description
        
        Args:
            test_description: Plain text description of what to test
            
        Returns:
            Generated Python Selenium script
        """
        # Create a simple test case structure
        test_case = {
            'test_id': 'TC-CUSTOM',
            'feature': 'Custom Test',
            'test_scenario': test_description,
            'preconditions': ['Browser is open', 'Page is loaded'],
            'test_steps': [test_description],
            'test_data': 'As specified in description',
            'expected_result': 'As specified in description',
            'test_type': 'custom'
        }
        
        return self.generate_script(test_case)


class ScriptParser:
    """Utility class to parse and clean generated scripts"""
    
    @staticmethod
    def extract_python_code(response_text):
        """
        Extract Python code from LLM response
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Clean Python code
        """
        import re
        
        # Try to extract from markdown code blocks
        code_match = re.search(r'```python\s*([\s\S]*?)\s*```', response_text)
        if code_match:
            return code_match.group(1).strip()
        
        # Try generic code blocks
        code_match = re.search(r'```\s*([\s\S]*?)\s*```', response_text)
        if code_match:
            return code_match.group(1).strip()
        
        # If no code blocks, check if response starts with typical Python patterns
        if response_text.strip().startswith(('"""', 'from ', 'import ', '#', 'class ', 'def ')):
            return response_text.strip()
        
        # Return as-is if nothing else works
        return response_text
    
    @staticmethod
    def validate_script(script):
        """
        Basic validation of generated script
        
        Args:
            script: Python script string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            compile(script, '<string>', 'exec')
            return True, "Script syntax is valid"
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"
    
    @staticmethod
    def add_html_path(script, html_path):
        """
        Update script to use correct HTML file path
        
        Args:
            script: Python script string
            html_path: Path to the HTML file
            
        Returns:
            Updated script
        """
        import re
        
        # Replace common placeholder URLs
        placeholders = [
            r'file:///path/to/checkout\.html',
            r'http://localhost[:/\d]*/checkout\.html',
            r'YOUR_HTML_PATH_HERE',
            r'path/to/your/checkout\.html',
            r'file:///.*?checkout\.html'
        ]
        
        for placeholder in placeholders:
            script = re.sub(placeholder, f'file:///{html_path}', script, flags=re.IGNORECASE)
        
        return script