import io
import time
import typing
import base64
import aiohttp
import google.genai
import google.genai.types as genai_types
from .. import _base as base

MAX_FILE_SIZE = 20 * 1000 * 1000

class GenerativeAi(base.CompletionService):
    client : google.genai.Client

    def format_config(self, model: base.Model, **kwargs) -> genai_types.GenerateContentConfigDict:
        return {
            "temperature": kwargs.get("temperature", 1.0),
            "top_p": kwargs.get("top_p", 0.95),
            "top_k": kwargs.get("top_k", 50),
            "candidate_count": kwargs.get("n", 1),
            "max_output_tokens": min(kwargs.get("max_tokens", 4096), model.output_token_limit or 4096),
            "safety_settings": [
                {
                    "category": genai_types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                    "threshold": genai_types.HarmBlockThreshold.OFF,
                },
                {
                    "category": genai_types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    "threshold": genai_types.HarmBlockThreshold.OFF,
                },
                {
                    "category": genai_types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    "threshold": genai_types.HarmBlockThreshold.OFF,
                },
                {
                    "category": genai_types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    "threshold": genai_types.HarmBlockThreshold.OFF,
                },
                {
                    "category": genai_types.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
                    "threshold": genai_types.HarmBlockThreshold.OFF,
                },
            ],
        }
    
    async def chat_completion(self, model: base.Model, messages: list[base.Candidate], **kwargs) -> list[base.Completion]:
        response = await self.client.aio.models.generate_content(
            model=model.id,
            contents=messages,
            config=self.format_config(model, **kwargs),
        )

        return [
            base.Completion(
                index=candidate.index,
                content=candidate.content.parts[0].text or "",
                role=candidate.content.role,
                id=response.response_id,
                object="chat.completion",
                model=model.id,
                created=response.create_time.timestamp() if response.create_time else time.time(),
                finish_reason=candidate.finish_reason.name,
                token_count=candidate.token_count,
            )
            for candidate in response.candidates if candidate.content and candidate.content.parts
        ]
    
    async def chat_completion_stream(self, model: base.Model, messages: list[base.Candidate], **kwargs) -> typing.AsyncGenerator[base.Completion, None]:
        streaming = await self.client.aio.models.generate_content_stream(
            model=model.id,
            contents=messages,
            config=self.format_config(model, **kwargs),
        )

        async for chunk in streaming:
            assert isinstance(chunk, genai_types.GenerateContentResponse)
            for candidate in chunk.candidates:
                if candidate.content and candidate.content.parts:
                    yield base.Completion(
                        index=candidate.index,
                        content=candidate.content.parts[0].text or "",
                        role=candidate.content.role,
                        id=chunk.response_id,
                        object="chat.completion.chunk",
                        model=model.id,
                        created=chunk.create_time.timestamp() if chunk.create_time else time.time(),
                        finish_reason=candidate.finish_reason.name if candidate.finish_reason else None,
                        token_count=candidate.token_count,
                    )
    
    async def format_messages(self, messages: list[base.Message], **kwargs) -> list[base.Candidate]:
        results : list[base.Candidate] = []
        for message in messages:
            if isinstance(message["content"], str):
                results.append(base.Candidate({
                    "parts": [genai_types.Part.from_text(text=message["content"])],
                }))
            elif isinstance(message["content"], list):
                parts : list[genai_types.Part] = []
                for part in message["content"]:
                    if isinstance(part, str):
                        parts.append(genai_types.Part.from_text(text=part))
                    elif isinstance(part, dict):
                        match part["type"]:
                            case "text":
                                parts.append(genai_types.Part.from_text(text=part["text"]))
                            case "image_url":
                                parts.append({
                                    "file_data": await self.upload_file(part["image_url"]["url"]),
                                })
                
                results.append(base.Candidate({
                    "parts": parts,
                }))
    
    async def upload_file(self, image_uri: str) -> genai_types.FileDataDict:
        if image_uri.startswith("http"):
            async with aiohttp.ClientSession() as session:
                async with session.get(image_uri) as response:
                    data = await response.read()
                    mime_type = response.content_type or "application/octet-stream"
        else:
            mime_type, data = image_uri.split(";base64,", 2)
            data = base64.b64decode(data)

        if len(data) < MAX_FILE_SIZE:
            return genai_types.FileDataDict({
                "file_uri": base64.b64encode(data).decode("utf-8"),
                "mime_type": mime_type,
            })

        if len(data) > MAX_FILE_SIZE:
            data = await self.client.aio.files.upload(
                file=io.BytesIO(data),
                config={
                    "mime_type": mime_type,
                },
            )

            while data.name:
                file = await self.client.aio.files.get(data.name)
                if file.state == genai_types.FileState.PROCESSING:
                    continue

                if file.state == genai_types.FileState.FAILED:
                    raise RuntimeError(f"Failed to upload file: {file.error}")
                
                break

            return genai_types.FileDataDict({
                "file_uri": file.uri,
                "mime_type": mime_type,
            })
    
    async def count_tokens(self, model: base.Model, messages: list[base.Candidate], **kwargs) -> int:
        response = await self.client.aio.models.count_tokens(
            model=model.id,
            contents=messages,
        )

        return response.total_tokens
    
    async def models(self, **kwargs) -> list[base.Model]:
        response = await self.client.aio.models.list()
        return [
            base.Model({
                "id": model.name,
                "name": model.display_name,
                "description": model.description,
                "input_token_limit": model.input_token_limit,
                "output_token_limit": model.output_token_limit,
            })
            async for model in response
        ]
