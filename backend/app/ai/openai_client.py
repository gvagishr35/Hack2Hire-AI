from openai import AsyncOpenAI


def get_openai_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key="dummy")