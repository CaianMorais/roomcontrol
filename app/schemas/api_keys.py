from pydantic import BaseModel, Field

class CreateApiKeySchema(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nome identificador da API Key"
    )