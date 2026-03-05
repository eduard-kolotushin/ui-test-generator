from __future__ import annotations

from openai import OpenAI


def main() -> None:
    """
    Simple script to talk to a locally running Docker LLM that exposes
    an OpenAI-compatible HTTP API.

    By default it assumes the Docker Model Runner is available at
    http://localhost:12434/v1 and that the model is named \"ai/gemma3\".
    Adjust base_url and model name if your setup differs.
    """

    client = OpenAI(
        base_url="http://localhost:12434/v1",  # Port exposed by your Docker LLM
        api_key="sk-local",  # Dummy key; required by OpenAI client but not validated by most local servers
    )

    response = client.chat.completions.create(
        model="ai/gemma3",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain the concept of context length in LLMs."},
        ],
    )

    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
