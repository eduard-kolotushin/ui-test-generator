from langchain_gigachat import GigaChat

from src.config import get_gigachat_credentials, get_gigachat_verify_ssl

model = GigaChat(
    credentials="MGNiMzZlN2ItNDkzNS00OTNlLTk4MjItOTQ4NzEwMGZkNmUxOjRjZDcxZjQ1LTNlZDktNDEyYy05ZDE1LTdhMzU1NTc1MWZhZg==",
    verify_ssl_certs=False,
    scope="GIGACHAT_API_CORP",
)

if __name__ == "__main__":
    print(model.invoke("Hello!"))