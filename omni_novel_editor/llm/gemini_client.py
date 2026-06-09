import requests


class GeminiClient:
    def __init__(self, api_key: str, model: str, timeout: int = 180) -> None:
        self.api_key = api_key.strip()
        self.model = model
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("Thiếu Gemini API key.")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.35,
                "topP": 0.9,
                "maxOutputTokens": 8192,
            },
        }
        response = requests.post(url, params={"key": self.api_key}, json=payload, timeout=self.timeout)
        if response.status_code >= 400:
            raise RuntimeError(f"Gemini API lỗi {response.status_code}: {response.text[:500]}")
        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini không trả về candidate nào.")
        parts = candidates[0].get("content", {}).get("parts", [])
        text_parts = [part.get("text", "") for part in parts if part.get("text")]
        output = "\n".join(text_parts).strip()
        if not output:
            raise RuntimeError("Gemini trả về output rỗng.")
        return output
