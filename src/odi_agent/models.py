"""Model construction."""

# from langchain_google_genai import ChatGoogleGenerativeAI

from odi_agent.auth import get_google_credentials
from odi_agent.config import PROJECT_ID, LOCATION, MODEL_ID


# def create_brain():
#     """Create our Gemini model through Vertex AI."""
#     return ChatGoogleGenerativeAI(
#         model=MODEL_ID,
#         vertexai=True,
#         project=PROJECT_ID,
#         location=LOCATION,
#         credentials=get_google_credentials(),
#         max_retries=2,
#     )

"""Create the configured LangChain chat model."""

from odi_agent.auth import get_google_credentials
from odi_agent.config import (
    MODEL_PROVIDER,
    MODEL_ID,
    PROJECT_ID,
    LOCATION,
)


def create_brain():
    """Create the model using the selected provider's connector."""

    if MODEL_PROVIDER == "gemini_vertex":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=MODEL_ID,
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION,
            credentials=get_google_credentials(),
            max_retries=2,
        )

    if MODEL_PROVIDER == "anthropic_vertex":
        from langchain_google_vertexai.model_garden import (
            ChatAnthropicVertex,
        )

        return ChatAnthropicVertex(
            model_name=MODEL_ID,
            project=PROJECT_ID,
            location=LOCATION,
            credentials=get_google_credentials(),
            max_tokens=4096,
            max_retries=2,
        )

    if MODEL_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=MODEL_ID,
            max_retries=2,
        )

    if MODEL_PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=MODEL_ID,
            max_tokens=4096,
            max_retries=2,
        )

    raise ValueError(
        f"Unsupported model provider: {MODEL_PROVIDER!r}. "
        "Choose gemini_vertex, anthropic_vertex, openai, or anthropic."
    )