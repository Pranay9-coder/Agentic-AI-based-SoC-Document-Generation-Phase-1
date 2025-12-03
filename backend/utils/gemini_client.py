import base64
from typing import List, Optional


class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.5-pro"):
        self.api_key = api_key
        self.model = model
        self._client = None
        self._legacy_model = None
        self._init_clients()

    def _init_clients(self):
        try:
            from google import genai  # type: ignore
            self._client = genai.Client(api_key=self.api_key)
        except Exception:
            try:
                import google.generativeai as genai  # type: ignore
                genai.configure(api_key=self.api_key)
                self._legacy_model = genai.GenerativeModel(self.model)
            except Exception:
                raise RuntimeError("No Gemini client available. Install 'google-genai' or 'google-generativeai'.")

    def _b64(self, data: bytes) -> str:
        return base64.b64encode(data).decode("utf-8")

    def caption_image(self, image_bytes: bytes) -> Optional[str]:
        prompt = (
            "Provide a concise, accessible caption (<= 20 words) that describes the image content for technical documentation."
        )
        if self._client is not None:
            try:
                contents = [
                    {"role": "user", "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/png", "data": self._b64(image_bytes)}}
                    ]}
                ]
                resp = self._client.models.generate_content(model=self.model, contents=contents)
                text = getattr(resp, "text", None)
                return (text or "").strip() or None
            except Exception:
                return None
        elif self._legacy_model is not None:
            try:
                resp = self._legacy_model.generate_content([
                    prompt,
                    {"mime_type": "image/png", "data": image_bytes}
                ])
                text = getattr(resp, "text", None)
                return (text or "").strip() or None
            except Exception:
                return None
        return None

    def title_table(self, rows: List[List[str]]) -> Optional[str]:
        sample = "\n".join([" | ".join(r) for r in rows[:2]])
        prompt = (
            "Given this table preview, generate a short, descriptive table title (<= 12 words).\n" + sample
        )
        if self._client is not None:
            try:
                resp = self._client.models.generate_content(model=self.model, contents=[prompt])
                text = getattr(resp, "text", None)
                return (text or "").strip() or None
            except Exception:
                return None
        elif self._legacy_model is not None:
            try:
                resp = self._legacy_model.generate_content(prompt)
                text = getattr(resp, "text", None)
                return (text or "").strip() or None
            except Exception:
                return None
        return None

    def simplify_text(self, text: str) -> Optional[str]:
        prompt = (
            "Rewrite the following paragraph to be clear and concise for a non-expert audience, preserving meaning:\n" + text
        )
        if self._client is not None:
            try:
                resp = self._client.models.generate_content(model=self.model, contents=[prompt])
                t = getattr(resp, "text", None)
                return (t or "").strip() or None
            except Exception:
                return None
        elif self._legacy_model is not None:
            try:
                resp = self._legacy_model.generate_content(prompt)
                t = getattr(resp, "text", None)
                return (t or "").strip() or None
            except Exception:
                return None
        return None


