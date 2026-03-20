from __future__ import annotations

import os
import re
from textwrap import dedent

from django.conf import settings


class ReviewService:
    def review_code(
        self,
        *,
        code: str,
        action: str,
        prompt: str,
        model: str,
        language: str,
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, str]:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return self._fallback_review(
                code=code,
                action=action,
                prompt=prompt,
                language=language,
                warning="GEMINI_API_KEY is missing, so the app is using local review mode.",
            )

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            return self._fallback_review(
                code=code,
                action=action,
                prompt=prompt,
                language=language,
                warning="The google-genai package is not available, so the app is using local review mode.",
            )

        client = genai.Client(api_key=api_key)
        selected_model = model if model in settings.GEMINI_MODELS else settings.GEMINI_DEFAULT_MODEL
        prompt_body = self._build_user_prompt(
            code=code,
            action=action,
            prompt=prompt,
            language=language,
            history=history or [],
        )

        try:
            response = client.models.generate_content(
                model=selected_model,
                contents=prompt_body,
                config=types.GenerateContentConfig(
                    system_instruction=self._system_prompt(),
                    max_output_tokens=self._max_output_tokens(action, prompt, code),
                ),
            )
        except Exception as exc:
            handled = self._handle_gemini_exception(
                exc=exc,
                code=code,
                action=action,
                prompt=prompt,
                language=language,
            )
            if handled is not None:
                return handled
            raise

        answer = getattr(response, "text", "").strip()

        if not answer:
            answer = self._flatten_response(response)

        if self._is_code_request(action=action, prompt=prompt) and not self._has_nonempty_code_block(answer):
            repaired_answer = self._repair_missing_code_block(
                client=client,
                types_module=types,
                model=selected_model,
                prompt=prompt,
                code=code,
                language=language,
            )
            if repaired_answer:
                answer = repaired_answer

        answer = self._postprocess_answer(
            answer=answer,
            action=action,
            prompt=prompt,
            language=language,
        )

        return {
            "answer": answer or "The model returned an empty response.",
            "model": selected_model,
        }

    def _fallback_review(self, *, code: str, action: str, prompt: str, language: str, warning: str) -> dict[str, str]:
        analyzer = LocalReviewService()
        return {
            "answer": analyzer.build_review(code=code, action=action, prompt=prompt, language=language),
            "model": "local-fallback",
            "warning": warning,
        }

    def _system_prompt(self) -> str:
        return dedent(
            """
            You are CodeBuddy, a practical coding assistant for a third-year college student.
            First do exactly what the user asked. Do not force a review when the user asked for conversion, rewrite, refactor, or explanation.
            Preserve the original program behavior unless the user explicitly asks you to fix bugs or optimize it.
            Keep explanations clear, structured, and complete.
            Here "compact" means clean formatting and easy scanning, not shorter or incomplete content.
            Always return the full answer needed to satisfy the request.
            Follow KISS: no filler, no giant paragraphs, no repeated points.
            Use plain English and explain the root cause simply when you mention a bug.
            Use a small stable Markdown structure so the preview renders well.
            Never create dangling headings or unfinished sentences.
            Never say you converted or fixed code unless you include the code block in the same reply.
            If code is requested, return the full answer with result, code, and short explanation.
            Never add comments inside code unless the user explicitly asks for comments.
            When rewriting or converting code, do not preserve old comments unless the user explicitly asks for that.
            Never wrap the whole response in ```markdown fences.
            """
        ).strip()

    def _build_user_prompt(
        self,
        *,
        code: str,
        action: str,
        prompt: str,
        language: str,
        history: list[dict[str, str]],
    ) -> str:
        history_block = self._format_history(history)
        chat_instructions = self._chat_instructions(prompt=prompt, language=language)
        action_instructions = {
            "find_error": dedent(
                """
                Give a clear bug review with exactly these sections:
                ## Main Bug
                (Explicitly mention the exact line number and the piece of code where the bug is found)
                ## Why It Breaks
                (Explain why the code fails)
                ## Fix
                (Explain how to fix the issue)
                ## Corrected Code
                (Provide the full corrected code in a fenced block)
                Rules:
                - Keep each section short but complete
                - Explain the bug in plain English
                - Always state the line number of the exact faulty line
                - You MUST return the full corrected code
                """
            ).strip(),
            "create_report": dedent(
                """
                Create a clear full report with exactly these sections:
                ## Summary
                ## Main Issues
                ## Better Approach
                ## Corrected Code
                ## Complexity
                ## Test And Dry Run
                Rules:
                - Maximum 2 bullets per section
                - 1 short paragraph is allowed when clarity needs it
                - Keep dry run to 3 short steps
                - Use only one compact corrected code block
                - Do not repeat the same bug in multiple sections
                - Return full meaning, not an over-short summary
                """
            ).strip(),
            "chat": chat_instructions,
        }

        return dedent(
            f"""
            Language: {language}
            Selected mode: {action}

            {action_instructions.get(action, action_instructions["chat"])}

            Important output rules:
            - Keep the final answer preview-friendly with a few complete sections only
            - Do not create extra headings unless needed
            - Do not leave a heading without its explanation
            - If code is requested, include one full fenced code block
            - "Compact" means structured display, not reduced content

            Conversation history:
            {history_block}

            User prompt:
            {prompt or "Review this code and help me understand it better."}

            Code to analyze:
            ```{language}
            {code}
            ```
            """
        ).strip()

    def _chat_instructions(self, *, prompt: str, language: str) -> str:
        if self._is_code_request(action="chat", prompt=prompt):
            target_language = self._target_language(prompt=prompt, fallback=language)
            return dedent(
                f"""
                Do the exact task asked by the user.
                This request needs code output.
                Use exactly this format:
                ## Result
                One short sentence saying what was done.
                ## Code
                ```{target_language}
                full code here
                ```
                ## Explanation
                2-4 short bullets covering important changes, assumptions, or fixes.
                Rules:
                - Return the full code, not a partial snippet
                - Do not leave the code block empty
                - Do not add comments inside the code unless the user explicitly asked for comments
                - Preserve behavior unless the user explicitly asked for a fix or optimization
                - If the requested language is C++, use #include <bits/stdc++.h> and using namespace std;
                """
            ).strip()

        return dedent(
            """
            Do the exact task asked by the user.
            If the user asks for explanation only, use:
            ## Answer
            short explanation
            ## Notes
            1-3 short bullets if useful.
            Keep the reply complete and easy to preview.
            "Compact" means organized display, not removing important details.
            """
        ).strip()

    def _max_output_tokens(self, action: str, prompt: str, code: str) -> int:
        if self._is_code_request(action=action, prompt=prompt):
            estimated = max(2200, min(5000, 1600 + len(code)))
            return estimated

        if action == "chat":
            return 900

        limits = {
            "find_error": 780,
            "create_report": 980,
        }
        return limits.get(action, 620)

    def _postprocess_answer(self, *, answer: str, action: str, prompt: str, language: str) -> str:
        if not answer:
            return answer

        if self._is_code_request(action=action, prompt=prompt):
            target_language = self._target_language(prompt=prompt, fallback=language)
            if target_language == "cpp":
                return self._normalize_cpp_answer(answer)

        return answer

    def _is_code_request(self, *, action: str, prompt: str) -> bool:
        # Tell the system that both Find Error and Create Report return code
        if action in ("find_error", "create_report"):
            return True
            
        if action != "chat":
            return False

        prompt_lower = (prompt or "").lower()
        keywords = [
            "convert",
            "rewrite",
            "refactor",
            "translate",
            "give code",
            "full code",
            "write code",
            "implement",
            "c++",
            "cpp",
            "java",
            "javascript",
            "js",
            "python",
        ]
        return any(keyword in prompt_lower for keyword in keywords)

    def _target_language(self, *, prompt: str, fallback: str) -> str:
        prompt_lower = (prompt or "").lower()
        if "c++" in prompt_lower or "cpp" in prompt_lower:
            return "cpp"
        if "javascript" in prompt_lower or re.search(r"\bjs\b", prompt_lower):
            return "javascript"
        if "typescript" in prompt_lower or re.search(r"\bts\b", prompt_lower):
            return "typescript"
        if "java" in prompt_lower:
            return "java"
        if "python" in prompt_lower:
            return "python"
        if "c#" in prompt_lower or "csharp" in prompt_lower:
            return "csharp"
        return fallback

    def _has_nonempty_code_block(self, text: str) -> bool:
        code_blocks = re.findall(r"```[^\n]*\n([\s\S]*?)```", text or "")
        return any(block.strip() for block in code_blocks)

    def _normalize_cpp_answer(self, answer: str) -> str:
        match = re.search(r"```([^\n]*)\n([\s\S]*?)```", answer)
        if not match:
            return answer

        normalized_code = self._normalize_cpp_code(match.group(2))
        replacement = f"```cpp\n{normalized_code}\n```"
        return f"{answer[:match.start()]}{replacement}{answer[match.end():]}"

    def _normalize_cpp_code(self, code: str) -> str:
        code = self._strip_cpp_comments(code)
        lines = []
        for raw_line in code.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                lines.append("")
                continue
            if stripped.startswith("#include"):
                continue
            if stripped == "using namespace std;":
                continue
            lines.append(raw_line.rstrip())

        body = "\n".join(lines).strip()
        prefix = "#include <bits/stdc++.h>\nusing namespace std;"
        return f"{prefix}\n\n{body}" if body else prefix

    def _strip_cpp_comments(self, code: str) -> str:
        code = re.sub(r"/\*[\s\S]*?\*/", "", code)
        cleaned_lines = [re.sub(r"//.*$", "", line).rstrip() for line in code.splitlines()]
        return "\n".join(cleaned_lines)

    def _repair_missing_code_block(
        self,
        *,
        client: object,
        types_module: object,
        model: str,
        prompt: str,
        code: str,
        language: str,
    ) -> str:
        target_language = self._target_language(prompt=prompt, fallback=language)
        repair_prompt = dedent(
            f"""
            The last answer missed the actual code body.
            Return a corrected full answer using exactly this format:
            ## Result
            one short sentence
            ## Code
            ```{target_language}
            full code here
            ```
            ## Explanation
            1-3 short bullets

            Rules:
            - The code block must be complete and non-empty
            - Do not add comments inside the code unless the user explicitly asked for comments
            - If the requested language is C++, use #include <bits/stdc++.h> and using namespace std;
            Preserve the original program behavior unless the user explicitly asked for a fix or optimization.

            User request:
            {prompt}

            Source code:
            ```{language}
            {code}
            ```
            """
        ).strip()

        try:
            response = client.models.generate_content(
                model=model,
                contents=repair_prompt,
                config=types_module.GenerateContentConfig(
                    system_instruction=(
                        "Return a corrected full answer with one complete non-empty fenced code block "
                        "and no comments inside the code unless explicitly asked."
                    ),
                    max_output_tokens=max(2600, min(6000, 2200 + len(code))),
                ),
            )
        except Exception:
            return ""

        answer = getattr(response, "text", "").strip() or self._flatten_response(response)
        return answer if self._has_nonempty_code_block(answer) else ""

    def _format_history(self, history: list[dict[str, str]]) -> str:
        if not history:
            return "No previous conversation."

        lines: list[str] = []
        for message in history[-8:]:
            role = message.get("role", "user").title()
            content = message.get("content", "").strip()
            if content:
                lines.append(f"{role}: {content}")
        return "\n".join(lines) if lines else "No previous conversation."

    def _flatten_response(self, response: object) -> str:
        parts: list[str] = []
        for candidate in getattr(response, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", []) or []:
                text = getattr(part, "text", "")
                if text:
                    parts.append(text)
        return "\n".join(parts).strip()

    def _handle_gemini_exception(
        self,
        *,
        exc: Exception,
        code: str,
        action: str,
        prompt: str,
        language: str,
    ) -> dict[str, str] | None:
        message = str(exc)
        lowered = message.lower()

        if "api key not valid" in lowered or "permission denied" in lowered or "unauthenticated" in lowered:
            raise ValueError("Your Gemini API key is invalid. Check GEMINI_API_KEY in the .env file and try again.") from exc

        if "quota" in lowered or "resource_exhausted" in lowered or "429" in lowered:
            return self._fallback_review(
                code=code,
                action=action,
                prompt=prompt,
                language=language,
                warning=(
                    "Gemini quota or rate limit was hit, so the app switched to local review mode. "
                    "Check your Google AI Studio quota and billing if this should not happen."
                ),
            )

        if "connection" in lowered or "timeout" in lowered or "unavailable" in lowered:
            return self._fallback_review(
                code=code,
                action=action,
                prompt=prompt,
                language=language,
                warning="Gemini could not be reached right now, so the app switched to local review mode.",
            )

        return None


class LocalReviewService:
    def build_review(self, *, code: str, action: str, prompt: str, language: str) -> str:
        findings = self._findings(code)
        complexity = self._complexity_guess(code)
        corrected_code = self._corrected_code(code)
        test_case = self._example_test_case(code, language)
        dry_run = self._dry_run(findings, test_case)

        if action == "find_error":
            return dedent(
                f"""
                ## Local Review Mode
                Gemini is unavailable, so this is a short local review.

                ## Main Bug
                {self._bullet_block(findings[:2])}
                *(Line numbers approximated by analyzer)*

                ## Why It Breaks
                - The wrong initial value or boundary causes the logic to fail on edge cases.

                ## Fix
                - Patch the root cause first, then test one edge case immediately.
                
                ## Corrected Code
                ```{language}
                {corrected_code}
                ```
                """
            ).strip()

        if action == "chat":
            user_note = prompt.strip() or "No extra question provided."
            return dedent(
                f"""
                ## Local Review Mode
                Gemini is unavailable, so this is a short local review.

                ## Your Question
                {user_note}

                ## Review
                {self._bullet_block(findings[:3])}

                ## Why
                - The issue appears because the current logic does not protect an edge case clearly.

                ## Complexity
                - Time Complexity: {complexity["time"]}
                - Space Complexity: {complexity["space"]}
                """
            ).strip()

        return dedent(
            f"""
            ## Local Review Mode
            Gemini is unavailable, so this is a short local report.

            ## Summary
            - Language: {language}
            - Lines: {len([line for line in code.splitlines() if line.strip()])}

            ## Main Issues
            {self._bullet_block(findings[:2])}

            ## Better Approach
            - Check edge cases early.
            - Keep the fix minimal and explain the root cause before optimizing.

            ## Corrected Code
            ```{language}
            {corrected_code}
            ```

            ## Complexity
            - Time: {complexity["time"]}
            - Space: {complexity["space"]}

            ## Test And Dry Run
            ```text
            {test_case}
            ```
            {dry_run}
            """
        ).strip()

    def _findings(self, code: str) -> list[str]:
        findings: list[str] = []
        lowered = code.lower()

        if "max_num = 0" in code and "return max_num" in code:
            findings.append(
                "The code initializes `max_num` with `0`, so an all-negative list can return the wrong answer."
            )
        if "right = len(" in code and "while left <= right" in code:
            findings.append(
                "Binary search likely has an off-by-one bug because `right` should usually start at `len(nums) - 1`."
            )
        if "nums[mid]" in code and "while left <= right" in code and "right = len(" in code:
            findings.append("This can access an index outside the array and raise an error.")
        if "input(" in code:
            findings.append("The terminal runner does not provide stdin yet, so `input()` based programs can hang or fail.")
        if "== None" in code or "!= None" in code:
            findings.append("Use `is None` or `is not None` instead of equality checks with `None`.")
        if "except:" in lowered:
            findings.append("A bare `except:` hides real errors and makes debugging harder.")
        if "range(len(" in code:
            findings.append("`range(len(...))` may be replaceable with direct iteration for cleaner code.")

        if not findings:
            findings.append(
                "No obvious pattern-based bug was detected, but you should still test boundary cases and invalid input."
            )

        return findings

    def _complexity_guess(self, code: str) -> dict[str, str]:
        loop_count = len(re.findall(r"\b(for|while)\b", code))
        nested_hint = code.count("for ") >= 2 or code.count("while ") >= 2

        if nested_hint or loop_count >= 2:
            time_complexity = "Likely O(n^2) in the worst visible path."
        elif loop_count == 1:
            time_complexity = "Likely O(n) for the visible main loop."
        else:
            time_complexity = "Likely O(1) to O(log n), depending on hidden operations."

        if any(token in code for token in ["append(", "{", "[", "dict(", "set("]):
            space_complexity = "Likely O(n) auxiliary space in common cases."
        else:
            space_complexity = "Likely O(1) auxiliary space."

        return {"time": time_complexity, "space": space_complexity}

    def _corrected_code(self, code: str) -> str:
        if "max_num = 0" in code and "return max_num" in code:
            return code.replace("max_num = 0", "max_num = nums[0] if nums else None")
        if "right = len(" in code and "while left <= right" in code:
            return code.replace("right = len(nums)", "right = len(nums) - 1")
        return code

    def _example_test_case(self, code: str, language: str) -> str:
        if "binary_search" in code:
            return "Input: nums = [2, 4, 7, 9, 13], target = 13\nExpected output: 4"
        if "find_max" in code:
            return "Input: nums = [-3, -7, -1]\nExpected output: -1"
        if language == "python":
            return "Input: a small valid input, an empty input, and one edge case.\nExpected: check all three outputs."
        return "Run one normal test case and one boundary test case."

    def _dry_run(self, findings: list[str], test_case: str) -> str:
        first_issue = findings[0] if findings else "Review the first failing step carefully."
        return dedent(
            f"""
            - Start with the sample test case: {test_case.splitlines()[0]}
            - Track the important variables after each iteration.
            - Watch the point where this issue appears: {first_issue}
            """
        ).strip()

    def _bullet_block(self, items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items)
