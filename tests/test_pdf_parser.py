"""Tests for PDF parser module."""
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import io
import sys

from financial_tracker.pdf_parser import extract_text_from_pdf


class TestExtractTextFromPdf:
    """Test PDF text extraction."""
    
    def test_extract_text_single_page(self):
        """Test extracting text from single page PDF."""
        # Mock PDF structure
        mock_page = Mock()
        mock_page.extract_text.return_value = "Transaction Date: 2025-01-15\nAmount: $50.00"
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        # Mock pdfplumber module
        with patch.dict('sys.modules', {'pdfplumber': Mock(open=Mock(return_value=mock_pdf))}):
            # Test extraction
            pdf_bytes = b"fake pdf content"
            result = extract_text_from_pdf(pdf_bytes)
            
            assert "Transaction Date: 2025-01-15" in result
            assert "Amount: $50.00" in result
    
    def test_extract_text_multiple_pages(self):
        """Test extracting text from multi-page PDF."""
        # Mock multiple pages
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content"
        
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 content"
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        with patch.dict('sys.modules', {'pdfplumber': Mock(open=Mock(return_value=mock_pdf))}):
            pdf_bytes = b"fake pdf content"
            result = extract_text_from_pdf(pdf_bytes)
            
            assert "Page 1 content" in result
            assert "Page 2 content" in result
            assert "\n\n" in result  # Pages separated by double newline
    
    def test_extract_text_empty_pages_skipped(self):
        """Test that empty pages are skipped."""
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Content"
        
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "   "  # Whitespace only
        
        mock_page3 = Mock()
        mock_page3.extract_text.return_value = None
        
        mock_page4 = Mock()
        mock_page4.extract_text.return_value = "More content"
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page1, mock_page2, mock_page3, mock_page4]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        with patch.dict('sys.modules', {'pdfplumber': Mock(open=Mock(return_value=mock_pdf))}):
            pdf_bytes = b"fake pdf content"
            result = extract_text_from_pdf(pdf_bytes)
            
            assert "Content" in result
            assert "More content" in result
            # Should not have extra separators from empty pages
            assert result == "Content\n\nMore content"
    
    def test_fallback_to_pypdf(self):
        """Test fallback to pypdf when pdfplumber fails."""
        # Mock pdfplumber to fail
        mock_pdfplumber = Mock()
        mock_pdfplumber.open.side_effect = Exception("pdfplumber error")
        
        # Mock pypdf reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "Text from pypdf"
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        
        mock_pypdf = Mock()
        mock_pypdf.PdfReader.return_value = mock_reader
        
        with patch.dict('sys.modules', {'pdfplumber': mock_pdfplumber, 'pypdf': mock_pypdf}):
            pdf_bytes = b"fake pdf content"
            result = extract_text_from_pdf(pdf_bytes)
            
            assert result == "Text from pypdf"
    
    def test_both_extractors_fail(self):
        """Test when both extractors fail."""
        mock_pdfplumber = Mock()
        mock_pdfplumber.open.side_effect = Exception("pdfplumber error")
        
        mock_pypdf = Mock()
        mock_pypdf.PdfReader.side_effect = Exception("pypdf error")
        
        with patch.dict('sys.modules', {'pdfplumber': mock_pdfplumber, 'pypdf': mock_pypdf}):
            pdf_bytes = b"fake pdf content"
            result = extract_text_from_pdf(pdf_bytes)
            
            assert result == ""
    
    def test_extract_text_none_return(self):
        """Test when page.extract_text() returns None."""
        mock_page = Mock()
        mock_page.extract_text.return_value = None
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        # Also mock pypdf to fail so we get empty string
        mock_pypdf = Mock()
        mock_pypdf.PdfReader.side_effect = Exception("pypdf error")
        
        with patch.dict('sys.modules', {'pdfplumber': Mock(open=Mock(return_value=mock_pdf)), 'pypdf': mock_pypdf}):
            pdf_bytes = b"fake pdf content"
            result = extract_text_from_pdf(pdf_bytes)
            
            # Should fallback to pypdf or return empty
            assert isinstance(result, str)
    
    def test_pypdf_multiple_pages(self):
        """Test pypdf with multiple pages."""
        mock_pdfplumber = Mock()
        mock_pdfplumber.open.side_effect = Exception("pdfplumber error")
        
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "PyPDF Page 1"
        
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "PyPDF Page 2"
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page1, mock_page2]
        
        mock_pypdf = Mock()
        mock_pypdf.PdfReader.return_value = mock_reader
        
        with patch.dict('sys.modules', {'pdfplumber': mock_pdfplumber, 'pypdf': mock_pypdf}):
            pdf_bytes = b"fake pdf content"
            result = extract_text_from_pdf(pdf_bytes)
            
            assert "PyPDF Page 1" in result
            assert "PyPDF Page 2" in result
    
    def test_extract_preserves_formatting(self):
        """Test that text formatting is preserved."""
        mock_page = Mock()
        mock_page.extract_text.return_value = "Date       Description       Amount\n01/15/25   Grocery Store     -$50.00"
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        with patch.dict('sys.modules', {'pdfplumber': Mock(open=Mock(return_value=mock_pdf))}):
            pdf_bytes = b"fake pdf content"
            result = extract_text_from_pdf(pdf_bytes)
            
            assert "Date       Description       Amount" in result
            assert "01/15/25   Grocery Store     -$50.00" in result
