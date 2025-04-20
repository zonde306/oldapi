import abc
import typing

class Completion(typing.TypedDict):
    index: int
    content: str
    object: typing.Literal["chat.completion", "chat.completion.chunk"]
    model: str
    created: float
    role: str | None
    id: str | None
    token_count: int | None
    finish_reason: str | None

class Model(typing.TypedDict):
    id: str
    name: str | None
    description: str | None
    input_token_limit: int | None
    output_token_limit: int | None

class MessageContent(typing.TypedDict):
    type: typing.Literal["text", "image_url"]
    image_url: str | None
    text: str | None

class Message(typing.TypedDict):
    role: str | None
    content: str | list[MessageContent]

Candidate = typing.TypeVar("Candidate", dict)

class CandidateData(typing.TypedDict):
    candidates: list[Candidate]
    system_prompt: str | None
    role_table: dict[str, str]

class CompletionService(abc.ABC):
    @abc.abstractmethod
    async def models(self, **kwargs) -> list[Model]:
        ...

    @abc.abstractmethod
    async def chat_completion(self, model: Model, messages: list[Candidate], **kwargs) -> list[Completion]:
        ...
    
    @abc.abstractmethod
    async def chat_completion_stream(self, model: Model, messages: list[Candidate], **kwargs) -> typing.AsyncGenerator[Completion, None]:
        ...
    
    @abc.abstractmethod
    async def count_tokens(self, model: Model, messages: list[Candidate], **kwargs) -> int:
        ...
    
    @abc.abstractmethod
    async def format_messages(self, messages: list[Message], **kwargs) -> list[Candidate]:
        ...
