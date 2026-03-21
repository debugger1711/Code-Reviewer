import os
from types import SimpleNamespace
from unittest.mock import PropertyMock
from unittest.mock import patch

from django.core.exceptions import RequestDataTooBig
from django.http import HttpRequest
from django.test import Client, RequestFactory, TestCase

from . import views
from .services import ReviewService


class ReviewerViewTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.factory = RequestFactory()

    def test_index_page_loads(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Code Reviewer")

    @patch("reviewer.views.ReviewService.review_code")
    def test_review_endpoint_returns_json(self, mocked_review) -> None:
        mocked_review.return_value = {"answer": "Looks good", "model": "gemini-2.5-flash"}
        response = self.client.post(
            "/api/review/",
            data='{"code":"print(1)","action":"chat","model":"gemini-2.5-flash","language":"python"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"answer": "Looks good", "model": "gemini-2.5-flash"})

    def test_large_request_body_returns_clear_413_error(self) -> None:
        request = self.factory.post("/api/review/", data="{}", content_type="application/json")
        with patch.object(HttpRequest, "body", new_callable=PropertyMock, side_effect=RequestDataTooBig("too large")):
            payload, error_response = views._load_json_payload(request)
        self.assertIsNone(payload)
        self.assertEqual(error_response.status_code, 413)
        self.assertIn("Request is too large", error_response.content.decode("utf-8"))

    @patch.dict(os.environ, {}, clear=True)
    def test_service_falls_back_without_api_key(self) -> None:
        result = ReviewService().review_code(
            code="def find_max(nums):\n    max_num = 0\n    return max_num",
            action="create_report",
            prompt="",
            model="gemini-2.5-flash",
            language="python",
        )
        self.assertEqual(result["model"], "local-fallback")
        self.assertIn("Local Review Mode", result["answer"])
        self.assertIn("GEMINI_API_KEY is missing", result["warning"])

    def test_code_request_detection(self) -> None:
        service = ReviewService()
        self.assertTrue(service._is_code_request(action="chat", prompt="convert it into c++"))
        self.assertTrue(service._is_code_request(action="find_error", prompt="convert it into c++"))

    def test_non_empty_code_block_detection(self) -> None:
        service = ReviewService()
        self.assertTrue(service._has_nonempty_code_block("## Code\n```cpp\nint main() { return 0; }\n```"))
        self.assertFalse(service._has_nonempty_code_block("## Code\n```cpp\n```"))

    def test_unclosed_code_block_detection(self) -> None:
        service = ReviewService()
        self.assertTrue(service._has_unclosed_code_block("## Code\n```python\nprint(1)"))
        self.assertFalse(service._has_unclosed_code_block("## Code\n```python\nprint(1)\n```"))

    def test_system_prompt_disallows_comments_by_default(self) -> None:
        prompt = ReviewService()._system_prompt()
        self.assertIn("Default to comment-free code", prompt)
        self.assertIn("do not include inline comments, block comments, docstrings", prompt)
        self.assertIn('"compact" means clean formatting and easy scanning, not shorter or incomplete content', prompt)

    def test_code_request_instructions_return_full_answer(self) -> None:
        instructions = ReviewService()._chat_instructions(prompt="convert it into c++", language="python")
        self.assertIn("## Result", instructions)
        self.assertIn("## Code", instructions)
        self.assertIn("## Explanation", instructions)
        self.assertIn("#include <bits/stdc++.h>", instructions)
        self.assertIn("using namespace std;", instructions)
        self.assertIn("Return comment-free code by default", instructions)

    def test_code_request_output_budget_is_larger_for_full_code(self) -> None:
        service = ReviewService()
        code = "print('x')\n" * 1600
        tokens = service._max_output_tokens("chat", "give full code", code)
        self.assertGreaterEqual(tokens, 4096)
        self.assertLessEqual(tokens, 8192)
        self.assertGreater(tokens, 5000)

    def test_history_formatting_compacts_previous_code_blocks(self) -> None:
        service = ReviewService()
        history = [
            {
                "role": "assistant",
                "content": "## Code\n```python\n" + "\n".join(f"print({index})" for index in range(120)) + "\n```",
            }
        ]
        formatted = service._format_history(history)
        self.assertIn("code block omitted from history", formatted)
        self.assertNotIn("print(119)", formatted)

    def test_response_was_cut_off_when_finish_reason_hits_max_tokens(self) -> None:
        service = ReviewService()
        response = SimpleNamespace(
            candidates=[
                SimpleNamespace(finish_reason=SimpleNamespace(name="MAX_OUTPUT_TOKENS"))
            ]
        )
        self.assertTrue(service._response_was_cut_off(response))

    def test_code_response_needs_repair_when_answer_is_incomplete(self) -> None:
        service = ReviewService()
        response = SimpleNamespace(
            candidates=[
                SimpleNamespace(finish_reason=SimpleNamespace(name="MAX_OUTPUT_TOKENS"))
            ]
        )
        answer = "## Code\n```python\nprint('half')"
        self.assertTrue(service._code_response_needs_repair(response=response, answer=answer))

    def test_cpp_code_is_normalized(self) -> None:
        service = ReviewService()
        answer = "## Code\n```cpp\n#include <iostream>\n#include <vector> // old include\n\nint main() {\n    // comment\n    std::cout << 1;\n}\n```"
        normalized = service._postprocess_answer(
            answer=answer,
            action="chat",
            prompt="convert it into c++",
            language="python",
        )
        self.assertIn("#include <bits/stdc++.h>", normalized)
        self.assertIn("using namespace std;", normalized)
        self.assertNotIn("#include <iostream>", normalized)
        self.assertNotIn("// comment", normalized)
