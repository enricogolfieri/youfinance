"""Base Agent class for AI-powered analysis"""

import json
import modules.logger as logger


class Agent:
    """Base class for all AI agents"""

    def __init__(self, ai_engine):
        """
        Initialize agent with AI engine and optional prompt

        Args:
            ai_engine: DeepSeek AI engine instance
            prompt: Prompt template (optional, can be set by subclass)
        """
        self.ai_engine = ai_engine

    def ask(self, prompt=None, max_tokens=4000, temperature=0.3, expect_json=True):
        """
        Send prompt to AI and get response

        Args:
            prompt: Prompt to send (uses self.prompt if not provided)
            max_tokens: Max tokens in response
            temperature: AI temperature
            expect_json: Whether to parse JSON response

        Returns:
            tuple: (success: bool, result: dict/str or error_message: str)
        """

        if not prompt:
            return False, "No prompt provided"

        try:
            response = self.ai_engine.send(
                prompt, max_tokens=max_tokens, temperature=temperature
            )

            if expect_json:
                # Extract and parse JSON
                json_start = response.find("{")
                json_end = response.rfind("}") + 1

                if json_start == -1 or json_end == 0:
                    return False, "AI response did not contain valid JSON"

                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                return True, result
            else:
                return True, response

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            return False, f"AI returned invalid JSON: {str(e)}"
        except Exception as e:
            logger.error(f"Error during AI request: {str(e)}")
            return False, f"Error during AI request: {str(e)}"
