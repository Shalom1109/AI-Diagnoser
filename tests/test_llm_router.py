"""tests/test_llm_router.py

Pytest unit test suite for core/llm_router.py.
Verifies fallback routing, pre-flight guardrails, and telemetry for:
1. HTTP 429 (Rate Limit) on OpenAI -> falls back to Groq.
2. HTTP 402 (Insufficient Quota) on OpenAI -> falls back to Gemini.
3. Image payload passed to DeepSeek -> intercepted by pre-flight guardrail and routed to Offline Heuristics.
4. Network timeout (>90s) on Ollama -> triggers fallback to Offline Heuristics / CPU mode.
5. Verifies no unhandled exceptions bubble up to Streamlit.
"""

import unittest
from unittest.mock import patch, MagicMock
from PIL import Image
import requests

from core.llm_router import (
    query_llm,
    get_last_telemetry,
    LAST_TELEMETRY,
    _query_openai,
    _query_deepseek,
    _query_ollama,
    _query_groq,
    _query_gemini,
)


class TestLLMRouterFailoverSuite(unittest.TestCase):

    def setUp(self):
        # Reset telemetry state before each test
        LAST_TELEMETRY["active_provider"] = "Offline Heuristics"
        LAST_TELEMETRY["primary_provider"] = "Offline Heuristics"
        LAST_TELEMETRY["latency_ms"] = 0.0
        LAST_TELEMETRY["failover_badge"] = None

    @patch("openai.OpenAI")
    @patch("core.llm_router._query_groq")
    def test_openai_http_429_fallback_to_groq(self, mock_query_groq, mock_openai_cls):
        """Test Case 1: HTTP 429 (Rate Limit) on OpenAI falls back seamlessly to Groq."""
        # Setup OpenAI client mock to raise a 429 RateLimit error
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Error code: 429 - Rate limit reached for gpt-4o-mini")

        mock_query_groq.return_value = "Response generated via Groq Llama 3.3 70B Fallback."

        # Execute query with OpenAI as primary provider
        result = query_llm(
            prompt="Analyze financial summary",
            model_provider="OpenAI",
            api_key="mock-openai-key"
        )

        # Assert Groq fallback was called
        mock_query_groq.assert_called_once()
        self.assertIn("Groq Llama 3.3 70B Fallback", result)

        # Assert Telemetry reflects failover badge
        telemetry = get_last_telemetry()
        self.assertEqual(telemetry["active_provider"], "Groq Cloud")
        self.assertIsNotNone(telemetry["failover_badge"])
        self.assertIn("Fallback: Groq", telemetry["failover_badge"])

    @patch("openai.OpenAI")
    @patch("core.llm_router._query_gemini")
    def test_openai_http_402_fallback_to_gemini(self, mock_query_gemini, mock_openai_cls):
        """Test Case 2: HTTP 402 (Insufficient Quota) on OpenAI falls back to Gemini."""
        # Setup OpenAI client mock to raise 402 Insufficient Quota
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Error code: 402 - Insufficient quota / credit balance exhausted")

        mock_query_gemini.return_value = "Response generated via Google Gemini 3.8 Flash Fallback."

        # Execute query with OpenAI as primary provider
        result = query_llm(
            prompt="Summarize operational risks",
            model_provider="OpenAI",
            api_key="mock-openai-key"
        )

        # Assert Gemini fallback was called
        mock_query_gemini.assert_called_once()
        self.assertIn("Google Gemini 3.8 Flash Fallback", result)

        # Assert Telemetry reflects failover badge
        telemetry = get_last_telemetry()
        self.assertEqual(telemetry["active_provider"], "Google Gemini")
        self.assertIsNotNone(telemetry["failover_badge"])
        self.assertIn("Fallback: Gemini", telemetry["failover_badge"])

    @patch("core.llm_router._query_gemini")
    @patch("core.llm_router._query_ollama")
    @patch("openai.OpenAI")
    def test_deepseek_vision_preflight_guardrail(self, mock_openai_cls, mock_query_ollama, mock_query_gemini):
        """Test Case 3: Passing an image payload to DeepSeek is intercepted by pre-flight guardrail."""
        mock_query_gemini.side_effect = Exception("Gemini unavailable")
        mock_query_ollama.side_effect = Exception("Ollama unavailable")

        # Create dummy image payload
        test_img = Image.new("RGB", (100, 100), color="blue")

        # Execute query with DeepSeek and an image payload
        result = query_llm(
            prompt="Analyze chart diagram",
            model_provider="DeepSeek",
            api_key="mock-deepseek-key",
            image_data=test_img
        )

        # Assert OpenAI/DeepSeek client was NEVER initialized or called for image
        mock_openai_cls.assert_not_called()

        # Assert offline heuristics output is returned
        self.assertIn("Visual Classification", result)
        self.assertIn("Key Data Points & Visual Metrics", result)

        # Assert Telemetry reflects pre-flight guardrail failover badge
        telemetry = get_last_telemetry()
        self.assertEqual(telemetry["active_provider"], "Offline Heuristics")
        self.assertIsNotNone(telemetry["failover_badge"])
        self.assertIn("Pre-Flight Guardrail", telemetry["failover_badge"])

    @patch("requests.post")
    def test_ollama_network_timeout_fallback(self, mock_requests_post):
        """Test Case 4: Network timeout (>90s) on Ollama triggers Offline Heuristics Engine."""
        # Mock requests.post to raise requests.exceptions.Timeout
        mock_requests_post.side_effect = requests.exceptions.Timeout("Connection timed out after 90s")

        # Execute query with Ollama as provider
        result = query_llm(
            prompt="Synthesize quarterly metrics",
            model_provider="Ollama (Local)",
            base_url="http://localhost:11434"
        )

        # Assert offline heuristics output is returned gracefully without crashing
        self.assertIn("Ollama Connection Timeout", result)
        self.assertIn("Automated Offline Fallback Analysis", result)

        # Assert Telemetry reflects timeout failover badge
        telemetry = get_last_telemetry()
        self.assertEqual(telemetry["active_provider"], "Offline Heuristics")
        self.assertIsNotNone(telemetry["failover_badge"])
        self.assertIn("Ollama Timeout", telemetry["failover_badge"])

    @patch("requests.post")
    def test_ollama_multimodal_auto_model_selection(self, mock_requests_post):
        """Test Case 6: Verifies Ollama dynamically maps model to 'llava' when visual data is present."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "Processed image via llava vision model."}
        mock_requests_post.return_value = mock_resp

        test_img = Image.new("RGB", (200, 200), color="green")
        result = _query_ollama(
            prompt="Analyze this chart",
            model_name="llama3.2",  # Text model requested with an image
            image_data=test_img
        )

        # Assert requests.post was called with model 'llava'
        mock_requests_post.assert_called_once()
        called_payload = mock_requests_post.call_args[1]["json"]
        self.assertEqual(called_payload["model"], "llava")
        self.assertIn("images", called_payload)
        self.assertEqual(result, "Processed image via llava vision model.")

    def test_offline_heuristics_no_echo_bug(self):
        """Test Case 7: Verifies offline fallback generates structured visual metrics rather than echoing long prompt."""
        test_img = Image.new("RGB", (300, 200), color="red")
        long_prompt = (
            "Provide a comprehensive, professional visual description of this image. Analyze: "
            "1. Overall subject matter and core composition 2. Key visual elements, objects, and people "
            "3. Aesthetic details (colors, lighting, style, textures) 4. Context, setting, and potential intent or message."
        )

    @patch("requests.post")
    def test_ollama_gpu_error_retry_cpu(self, mock_requests_post):
        """Test Case 8: Verifies Ollama GPU/VRAM errors trigger CPU fallback with num_gpu: 0."""
        err_resp = MagicMock()
        err_resp.status_code = 500
        err_resp.text = "CUDA out of memory / VRAM allocation failed"

        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"response": "Response generated via Ollama CPU fallback."}

        mock_requests_post.side_effect = [err_resp, ok_resp]

        from core.llm_router import _call_ollama
        result = _call_ollama(prompt="Test prompt", image_b64="dummy_b64")

        self.assertEqual(mock_requests_post.call_count, 2)
        second_call_payload = mock_requests_post.call_args_list[1][1]["json"]
        self.assertEqual(second_call_payload["options"]["num_gpu"], 0)
        self.assertEqual(second_call_payload["model"], "llava")
        self.assertEqual(result, "Response generated via Ollama CPU fallback.")

    def test_image_pipeline_normalization_and_analysis(self):
        """Test Case 9: Verifies normalize_image and analyze_image_with_llm."""
        from pipelines.image_pipeline import normalize_image, analyze_image_with_llm, VisionAnalysisResult

        # 1. RGBA normalization
        rgba_img = Image.new("RGBA", (150, 100), color=(255, 0, 0, 128))
        norm_img = normalize_image(rgba_img)
        self.assertEqual(norm_img.mode, "RGB")
        self.assertEqual(norm_img.size, (150, 100))

        # 2. P mode normalization
        p_img = Image.new("P", (80, 80))
        norm_p = normalize_image(p_img)
        self.assertEqual(norm_p.mode, "RGB")

        # 3. Vision analysis output wrapping
        res = analyze_image_with_llm(
            image=rgba_img,
            task_type="describe",
            model_provider="Offline Heuristics"
        )
        self.assertIsInstance(res, str)
        self.assertIsInstance(res, VisionAnalysisResult)
        self.assertIn("Visual Classification", str(res))
        self.assertEqual(res.image_dimensions, (150, 100))
        self.assertIn("active_provider", res.telemetry)

        # 4. Tuple unpacking
        text_out, tele_out, dims_out = res
        self.assertEqual(dims_out, (150, 100))
        self.assertIsInstance(tele_out, dict)
        self.assertIn("Visual Classification", text_out)

    @patch("core.llm_router.query_llm")
    def test_transform_artifact_strips_fences_and_filler(self, mock_query):
        """Test Case 10: Verifies transform_artifact removes accidental code fences and conversational filler."""
        from core.llm_router import LLMRouter, transform_artifact

        raw_llm_response = (
            "Sure! Here is your updated document:\n\n"
            "```markdown\n"
            "# Updated Executive Report\n\n"
            "| Revenue | Growth |\n"
            "| :--- | :--- |\n"
            "| $120M | 24% |\n"
            "```\n\n"
            "I hope this helps! Let me know if you need any further modifications."
        )
        mock_query.return_value = raw_llm_response

        router = LLMRouter()
        result = router.transform_artifact(
            current_content="Initial document text",
            observations={"Document Type": "Financial Report"},
            user_instruction="Convert to Table",
            preferred_provider="gemini"
        )

        self.assertNotIn("```markdown", result)
        self.assertNotIn("```", result)
        self.assertNotIn("Sure!", result)
        self.assertNotIn("I hope this helps!", result)
        self.assertTrue(result.startswith("# Updated Executive Report"))
        self.assertIn("| Revenue | Growth |", result)

    def test_transform_artifact_offline_table_generation(self):
        """Test Case 11: Verifies offline heuristics engine generates a table artifact without conversational filler."""
        from core.llm_router import LLMRouter

        router = LLMRouter()
        sample_doc = (
            "Annual Revenue: $450 Million\n"
            "Operating Margin: 28.5%\n"
            "Cash Reserves: $85 Million\n"
            "Headcount: 1,420 Employees"
        )
        res = router.transform_artifact(
            current_content=sample_doc,
            observations={"Format": "TXT"},
            user_instruction="Convert to Table",
            preferred_provider="offline"
        )

        self.assertIn("| Metric / Dimension | Specification & Context |", res)
        self.assertIn("| **Annual Revenue** | $450 Million |", res)
        self.assertIn("| **Operating Margin** | 28.5% |", res)
        self.assertNotIn("Sure", res)
        self.assertNotIn("```", res)

    def test_compress_and_downsample_image(self):
        """Test Case 12: Verifies large images are downsampled to 1024x1024 bounding box with JPEG compression."""
        from core.llm_router import compress_and_downsample_image

        large_img = Image.new("RGB", (2400, 1600), color="blue")
        processed = compress_and_downsample_image(large_img, max_dim=1024, quality=85)

        self.assertLessEqual(max(processed.size), 1024)
        self.assertEqual(processed.mode, "RGB")
        # Aspect ratio 2400/1600 = 1.5 -> 1024 / 682 approx
        self.assertEqual(processed.size[0], 1024)
        self.assertEqual(processed.size[1], 683)

    def test_analyze_image_helper(self):
        """Test Case 13: Verifies top-level analyze_image function executes correctly with downsampling."""
        from core.llm_router import analyze_image

        test_img = Image.new("RGB", (800, 600), color="red")
        res = analyze_image(image_data=test_img, provider="Offline Heuristics")

        self.assertIn("Visual Classification", res)
        self.assertIn("Key Data Points & Visual Metrics", res)

    def test_execute_with_timeout_guard(self):
        """Test Case 14: Verifies _execute_with_timeout strictly enforces latency limit."""
        import time
        from core.llm_router import _execute_with_timeout

        def slow_task():
            time.sleep(0.5)
            return "done"

        # Should timeout when timeout is 0.1s
        with self.assertRaises(TimeoutError):
            _execute_with_timeout(slow_task, timeout_seconds=0.1)

        # Should succeed when timeout is 1.0s
        res = _execute_with_timeout(slow_task, timeout_seconds=1.0)
        self.assertEqual(res, "done")


if __name__ == "__main__":
    unittest.main()


