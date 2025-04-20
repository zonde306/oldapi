import genai
import google.genai
import google.oauth2.credentials as credentials

class Vertex(genai.GenerativeAi):
    def __init__(self, json: str):
        self.client = google.genai.Client(
            vertexai=True,
            credentials=credentials.Credentials.from_authorized_user_info(
                json, scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
        )
