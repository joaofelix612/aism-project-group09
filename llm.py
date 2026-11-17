"""Cliente mínimo para o Ollama (modelo local, sem chave de API) com cache em disco."""
import hashlib
import json
import os
import urllib.request

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")


class LLM:
    def __init__(self, model=DEFAULT_MODEL, use_cache=True, cache_dir=".cache"):
        self.model = model
        self.use_cache = use_cache
        self.cache_dir = cache_dir
        if use_cache:
            os.makedirs(cache_dir, exist_ok=True)

    def chat(self, system: str, user: str, json_mode: bool = False) -> str:
        key = hashlib.sha256(
            json.dumps([self.model, system, user, json_mode], ensure_ascii=False).encode()
        ).hexdigest()
        path = os.path.join(self.cache_dir, key + ".json")
        if self.use_cache and os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)["response"]

        payload = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": 0},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            payload["format"] = "json"
        req = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                response = json.load(r)["message"]["content"]
        except Exception as e:
            raise RuntimeError(
                f"Falha a contactar o Ollama ({e}). Está a correr? "
                f"Tente: ollama serve && ollama pull {self.model}"
            )
        if self.use_cache:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"response": response}, f, ensure_ascii=False)
        return response
