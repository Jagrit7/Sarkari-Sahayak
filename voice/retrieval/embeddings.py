import os
from dotenv import load_dotenv
from langchain_cloudflare.embeddings import CloudflareWorkersAIEmbeddings

load_dotenv()

cloudflare_account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
cloudflare_api_token = os.getenv("CLOUDFLARE_API_TOKEN")

embeddings = CloudflareWorkersAIEmbeddings(
    account_id=cloudflare_account_id,
    api_token=cloudflare_api_token,
    model_name="@cf/baai/bge-large-en-v1.5",
)
