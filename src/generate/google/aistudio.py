import genai
import google.genai

class AiStudio(genai.GenerativeAi):
    def __init__(self, token: str):
        self.client = google.genai.Client(token)
