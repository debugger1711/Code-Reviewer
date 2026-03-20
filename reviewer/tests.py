import os
from unittest.mock import patch

from django.test import Client, TestCase

from .services import ReviewService


class ReviewerViewTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()

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
        self.assertFalse(service._is_code_request(action="find_error", prompt="convert it into c++"))

    def test_non_empty_code_block_detection(self) -> None:
        service = ReviewService()
        self.assertTrue(service._has_nonempty_code_block("## Code\n```cpp\nint main() { return 0; }\n```"))
        self.assertFalse(service._has_nonempty_code_block("## Code\n```cpp\n```"))

    def test_system_prompt_disallows_comments_by_default(self) -> None:
        prompt = ReviewService()._system_prompt()
        self.assertIn("Never add comments inside code unless the user explicitly asks", prompt)
        self.assertIn('"compact" means clean formatting and easy scanning, not shorter or incomplete content', prompt)

    def test_code_request_instructions_return_full_answer(self) -> None:
        instructions = ReviewService()._chat_instructions(prompt="convert it into c++", language="python")
        self.assertIn("## Result", instructions)
        self.assertIn("## Code", instructions)
        self.assertIn("## Explanation", instructions)
        self.assertIn("#include <bits/stdc++.h>", instructions)
        self.assertIn("using namespace std;", instructions)

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
