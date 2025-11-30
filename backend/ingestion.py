"""
Document Ingestion Module
Handles parsing and chunking of various document types
"""

import os
import json
from bs4 import BeautifulSoup
from pypdf import PdfReader
from docx import Document


class DocumentParser:
    """Parses different document types and extracts text"""
    
    @staticmethod
    def parse_file(file_path=None, file_content=None, filename=None):
        """
        Parse a file and extract text content
        
        Args:
            file_path: Path to the file (for local files)
            file_content: File content bytes (for uploaded files)
            filename: Name of the file (required if using file_content)
            
        Returns:
            Extracted text content
        """
        if file_path:
            filename = os.path.basename(file_path)
            with open(file_path, 'rb') as f:
                file_content = f.read()
        
        if not filename:
            raise ValueError("Filename is required")
        
        extension = filename.lower().split('.')[-1]
        
        if extension == 'txt':
            return DocumentParser._parse_text(file_content)
        elif extension == 'md':
            return DocumentParser._parse_markdown(file_content)
        elif extension == 'json':
            return DocumentParser._parse_json(file_content)
        elif extension == 'html':
            return DocumentParser._parse_html(file_content)
        elif extension == 'pdf':
            return DocumentParser._parse_pdf(file_content)
        elif extension == 'docx':
            return DocumentParser._parse_docx(file_content)
        else:
            # Try to read as text
            try:
                return file_content.decode('utf-8')
            except:
                raise ValueError(f"Unsupported file type: {extension}")
    
    @staticmethod
    def _parse_text(content):
        """Parse plain text file"""
        if isinstance(content, bytes):
            return content.decode('utf-8')
        return content
    
    @staticmethod
    def _parse_markdown(content):
        """Parse markdown file (treat as plain text)"""
        if isinstance(content, bytes):
            return content.decode('utf-8')
        return content
    
    @staticmethod
    def _parse_json(content):
        """Parse JSON file and convert to readable text"""
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        
        data = json.loads(content)
        return DocumentParser._json_to_text(data)
    
    @staticmethod
    def _json_to_text(data, indent=0):
        """Convert JSON data to readable text format"""
        lines = []
        prefix = "  " * indent
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    lines.append(DocumentParser._json_to_text(value, indent + 1))
                else:
                    lines.append(f"{prefix}{key}: {value}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}Item {i + 1}:")
                    lines.append(DocumentParser._json_to_text(item, indent + 1))
                else:
                    lines.append(f"{prefix}- {item}")
        else:
            lines.append(f"{prefix}{data}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _parse_html(content):
        """Parse HTML file and extract text + structure info"""
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style']):
            element.decompose()
        
        # Extract text
        text = soup.get_text(separator='\n', strip=True)
        
        # Also extract important HTML structure information
        structure_info = DocumentParser._extract_html_structure(soup)
        
        return f"HTML Content:\n{text}\n\nHTML Structure:\n{structure_info}"
    
    @staticmethod
    def _extract_html_structure(soup):
        """Extract important HTML element information for Selenium"""
        structure_lines = []
        
        # Find forms
        forms = soup.find_all('form')
        for form in forms:
            form_id = form.get('id', 'no-id')
            structure_lines.append(f"Form: id='{form_id}'")
        
        # Find input fields
        inputs = soup.find_all('input')
        for inp in inputs:
            inp_type = inp.get('type', 'text')
            inp_id = inp.get('id', '')
            inp_name = inp.get('name', '')
            inp_placeholder = inp.get('placeholder', '')
            structure_lines.append(f"Input: type='{inp_type}', id='{inp_id}', name='{inp_name}', placeholder='{inp_placeholder}'")
        
        # Find textareas
        textareas = soup.find_all('textarea')
        for ta in textareas:
            ta_id = ta.get('id', '')
            ta_name = ta.get('name', '')
            structure_lines.append(f"Textarea: id='{ta_id}', name='{ta_name}'")
        
        # Find buttons
        buttons = soup.find_all('button')
        for btn in buttons:
            btn_id = btn.get('id', '')
            btn_class = btn.get('class', [])
            btn_text = btn.get_text(strip=True)
            structure_lines.append(f"Button: id='{btn_id}', class='{' '.join(btn_class) if btn_class else ''}', text='{btn_text}'")
        
        # Find select elements
        selects = soup.find_all('select')
        for sel in selects:
            sel_id = sel.get('id', '')
            sel_name = sel.get('name', '')
            structure_lines.append(f"Select: id='{sel_id}', name='{sel_name}'")
        
        # Find elements with specific classes that might be important
        error_elements = soup.find_all(class_=lambda x: x and 'error' in x.lower() if x else False)
        for elem in error_elements:
            elem_id = elem.get('id', '')
            elem_class = elem.get('class', [])
            structure_lines.append(f"Error Element: id='{elem_id}', class='{' '.join(elem_class) if elem_class else ''}'")
        
        return "\n".join(structure_lines)
    
    @staticmethod
    def _parse_pdf(content):
        """Parse PDF file"""
        import io
        pdf_file = io.BytesIO(content)
        reader = PdfReader(pdf_file)
        
        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text())
        
        return "\n\n".join(text_parts)
    
    @staticmethod
    def _parse_docx(content):
        """Parse DOCX file"""
        import io
        docx_file = io.BytesIO(content)
        doc = Document(docx_file)
        
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)


class TextChunker:
    """Splits text into chunks for embedding"""
    
    @staticmethod
    def chunk_text(text, chunk_size=500, overlap=50):
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            chunk_size: Maximum size of each chunk (in characters)
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # Find the end of this chunk
            end = start + chunk_size
            
            if end < text_length:
                # Try to break at a sentence or paragraph
                break_point = TextChunker._find_break_point(text, start, end)
                if break_point > start:
                    end = break_point
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap if end - overlap > start else end
        
        return chunks
    
    @staticmethod
    def _find_break_point(text, start, end):
        """Find a good break point (paragraph, sentence, or word boundary)"""
        # Look for paragraph break
        para_break = text.rfind('\n\n', start, end)
        if para_break > start + 100:
            return para_break + 2
        
        # Look for sentence break
        for punct in ['. ', '! ', '? ']:
            sent_break = text.rfind(punct, start, end)
            if sent_break > start + 100:
                return sent_break + 2
        
        # Look for line break
        line_break = text.rfind('\n', start, end)
        if line_break > start + 100:
            return line_break + 1
        
        # Look for word break
        word_break = text.rfind(' ', start, end)
        if word_break > start:
            return word_break + 1
        
        return end


class DocumentIngestion:
    """Main class for document ingestion pipeline"""
    
    def __init__(self, vector_store):
        """
        Initialize ingestion pipeline
        
        Args:
            vector_store: VectorStore instance for storing documents
        """
        self.vector_store = vector_store
        self.parser = DocumentParser()
        self.chunker = TextChunker()
    
    def ingest_file(self, file_path=None, file_content=None, filename=None):
        """
        Ingest a single file into the knowledge base
        
        Args:
            file_path: Path to file (for local files)
            file_content: File content bytes (for uploaded files)
            filename: Name of the file
            
        Returns:
            Number of chunks added
        """
        # Parse the file
        text = self.parser.parse_file(
            file_path=file_path,
            file_content=file_content,
            filename=filename
        )
        
        # Chunk the text
        chunks = self.chunker.chunk_text(text)
        
        # Get source name
        source_name = filename if filename else os.path.basename(file_path)
        
        # Add to vector store
        num_chunks = self.vector_store.add_documents(chunks, source_name)
        
        return num_chunks
    
    def ingest_html(self, html_content, filename="checkout.html"):
        """
        Ingest HTML content with special handling for structure
        
        Args:
            html_content: HTML content as string or bytes
            filename: Name for the HTML file
            
        Returns:
            Number of chunks added
        """
        if isinstance(html_content, str):
            html_content = html_content.encode('utf-8')
        
        return self.ingest_file(file_content=html_content, filename=filename)
    
    def get_html_structure(self, html_content):
        """
        Get the full HTML content for script generation
        
        Args:
            html_content: HTML content
            
        Returns:
            Original HTML content
        """
        if isinstance(html_content, bytes):
            return html_content.decode('utf-8')
        return html_content