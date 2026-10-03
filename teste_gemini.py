import os
from dotenv import load_dotenv
from google import genai

# Carrega a chave guardada no arquivo .env
load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Faz uma pergunta simples de teste
resposta = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Em uma frase, o que é Tesouro Direto?"
)

print(resposta.text)