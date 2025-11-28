"""
Test Case Generator Module
Uses RAG + LLM to generate test cases from knowledge base
"""

import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TestCaseGenerator:
    """Generates test cases using RAG pipeline and LLM"""
    
    def __init__(self, vector_store):
        """
        Initialize the test case generator
        
        Args:
            vector_store: VectorStore instance for retrieving context
        """
        self.vector_store = vector_store
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
    
    def generate_test_cases(self, user_query, num_results=10):
        """
        Generate test cases based on user query
        
        Args:
            user_query: User's request for test cases
            num_results: Number of context chunks to retrieve
            
        Returns:
            Generated test cases as structured text
        """
        # Step 1: Retrieve relevant context from vector store
        relevant_docs = self.vector_store.search(user_query, n_results=num_results)
        
        # Step 2: Build context string
        context = self._build_context(relevant_docs)
        
        # Step 3: Create prompt
        prompt = self._create_test_case_prompt(user_query, context)
        
        # Step 4: Call LLM
        response = self._call_llm(prompt)
        
        return response
    
    def _build_context(self, documents):
        """Build context string from retrieved documents"""
        if not documents:
            return "No relevant documentation found."
        
        context_parts = []
        for i, doc in enumerate(documents):
            source = doc['metadata'].get('source', 'Unknown')
            content = doc['content']
            context_parts.append(f"[Source: {source}]\n{content}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def _create_test_case_prompt(self, user_query, context):
        """Create the prompt for test case generation"""
        prompt = f"""You are a QA Test Engineer expert. Your task is to generate comprehensive test cases based STRICTLY on the provided documentation.

IMPORTANT RULES:
1. ONLY generate test cases for features mentioned in the documentation
2. DO NOT invent or assume features not documented
3. Each test case must reference which source document it's based on
4. Include both positive and negative test cases
5. Be specific about expected results

DOCUMENTATION CONTEXT:
{context}

USER REQUEST:
{user_query}

Generate test cases in the following JSON format:
{{
    "test_cases": [
        {{
            "test_id": "TC-001",
            "feature": "Feature name",
            "test_scenario": "Description of what is being tested",
            "preconditions": ["List of preconditions"],
            "test_steps": ["Step 1", "Step 2", "..."],
            "test_data": "Specific test data to use",
            "expected_result": "What should happen",
            "test_type": "positive/negative",
            "grounded_in": "source_document.ext"
        }}
    ]
}}

Generate comprehensive test cases based on the user's request. Make sure every test case is grounded in the provided documentation."""

        return prompt
    
    def _call_llm(self, prompt):
        """Call the Groq LLM API"""
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional QA engineer who creates detailed, accurate test cases. Always respond with valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=4000
            )
            
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            return f"Error generating test cases: {str(e)}"
    
    def generate_all_test_cases(self):
        """
        Generate comprehensive test cases for all features in the knowledge base
        
        Returns:
            Generated test cases covering all documented features
        """
        query = """Generate comprehensive test cases covering ALL features documented in the knowledge base, including:
        1. Product/Cart functionality
        2. Discount code system
        3. Form validation (all fields)
        4. Shipping options
        5. Payment methods
        6. Order submission
        7. UI/UX requirements
        8. Error handling
        
        Include both positive and negative test cases for each feature."""
        
        return self.generate_test_cases(query, num_results=15)
    
    def generate_feature_test_cases(self, feature_name):
        """
        Generate test cases for a specific feature
        
        Args:
            feature_name: Name of the feature to test
            
        Returns:
            Generated test cases for the feature
        """
        query = f"""Generate all positive and negative test cases for the {feature_name} feature. 
        Include edge cases and boundary conditions.
        Cover all scenarios mentioned in the documentation."""
        
        return self.generate_test_cases(query, num_results=10)


class TestCaseParser:
    """Utility class to parse generated test cases"""
    
    @staticmethod
    def parse_json_response(response_text):
        """
        Parse JSON response from LLM
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Parsed test cases as dictionary
        """
        import json
        
        # Try to find JSON in the response
        try:
            # First, try direct parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code blocks
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object in text
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Return as plain text if parsing fails
        return {"raw_response": response_text}
    
    @staticmethod
    def format_test_cases_markdown(test_cases_dict):
        """
        Format test cases as markdown table
        
        Args:
            test_cases_dict: Dictionary containing test cases
            
        Returns:
            Markdown formatted string
        """
        if "raw_response" in test_cases_dict:
            return test_cases_dict["raw_response"]
        
        if "test_cases" not in test_cases_dict:
            return str(test_cases_dict)
        
        lines = ["# Generated Test Cases\n"]
        lines.append("| Test ID | Feature | Scenario | Expected Result | Type | Source |")
        lines.append("|---------|---------|----------|-----------------|------|--------|")
        
        for tc in test_cases_dict["test_cases"]:
            test_id = tc.get("test_id", "N/A")
            feature = tc.get("feature", "N/A")
            scenario = tc.get("test_scenario", "N/A")[:50] + "..."
            expected = tc.get("expected_result", "N/A")[:30] + "..."
            test_type = tc.get("test_type", "N/A")
            source = tc.get("grounded_in", "N/A")
            
            lines.append(f"| {test_id} | {feature} | {scenario} | {expected} | {test_type} | {source} |")
        
        return "\n".join(lines)