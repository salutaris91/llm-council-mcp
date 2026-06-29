import unittest
from unittest.mock import MagicMock
import sys
import os

# Add project root to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import council_core
import server

class TestCouncil(unittest.TestCase):
    def test_generate_internal_council_prompt(self):
        # Test prompt generation with question and context
        question = "Should we use Redis or Memcached?"
        code_context = "def get_cache(): pass"
        
        prompt = council_core.generate_internal_council_prompt(question, code_context)
        
        self.assertIn(question, prompt)
        self.assertIn(code_context, prompt)
        self.assertIn("Der Pragmatiker", prompt)
        self.assertIn("Der Software-Architekt", prompt)
        self.assertIn("Der Skeptiker", prompt)
        self.assertIn("Der Clean-Code-Verfechter", prompt)
        self.assertIn("Der Produkt- & UX-Optimierer", prompt)
        self.assertIn("Diversitäts-Hinweis", prompt)

    def test_register_configured_tools(self):
        # Mock mcp instance
        mock_mcp = MagicMock()
        mock_mcp.add_tool = MagicMock()
        
        # Test both tools exposed
        settings = {
            "expose_internal_council": True,
            "expose_council": True
        }
        
        server.register_configured_tools(mock_mcp, settings)
        
        # Verify both tools were added
        self.assertEqual(mock_mcp.add_tool.call_count, 2)
        
        # Check specific tool names registered
        added_tools = [call[1].get("name") or call[0][1] for call in mock_mcp.add_tool.call_args_list]
        self.assertIn("ask_internal_council", added_tools)
        self.assertIn("ask_council", added_tools)
        
        # Check that annotations were passed to ask_council
        # Find the call for ask_council
        council_call = None
        for call in mock_mcp.add_tool.call_args_list:
            name = call[1].get("name") or call[0][1]
            if name == "ask_council":
                council_call = call
                break
        
        self.assertIsNotNone(council_call)
        annotations = council_call[1].get("annotations")
        self.assertIsNotNone(annotations)
        # FastMCP uses ToolAnnotations or a dict or custom class under the hood. 
        # In our implementation we pass it, so we verify it's present.

    def test_register_configured_tools_disabled(self):
        # Mock mcp instance
        mock_mcp = MagicMock()
        mock_mcp.add_tool = MagicMock()
        
        # Test tools disabled
        settings = {
            "expose_internal_council": False,
            "expose_council": False
        }
        
        server.register_configured_tools(mock_mcp, settings)
        self.assertEqual(mock_mcp.add_tool.call_count, 0)

if __name__ == "__main__":
    unittest.main()
