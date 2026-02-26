from dotenv import load_dotenv
from langchain_gigachat import GigaChat

from src.config import get_gigachat_credentials, get_gigachat_verify_ssl


def build_test_model() -> GigaChat:
    return GigaChat(
        credentials=get_gigachat_credentials(),
        verify_ssl_certs=get_gigachat_verify_ssl(),
        scope="GIGACHAT_API_CORP",
    )


if __name__ == "__main__":
    load_dotenv()
    model = build_test_model()
    print(model.invoke("Hello from GigaChat test!"))