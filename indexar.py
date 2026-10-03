import os
import glob
import pickle
import numpy as np
import faiss
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
# Lista todos os arquivos .md dentro da pasta docs/
caminhos = glob.glob("docs/*.md")

# Lê o conteúdo de cada um e guarda numa lista
documentos = []
for caminho in caminhos:
    with open(caminho, "r", encoding="utf-8") as arquivo:
        texto = arquivo.read()
        documentos.append({"caminho": caminho, "texto": texto})

print(f"Encontrados {len(documentos)} documentos.")
# Gera o embedding (vetor numérico) de cada documento
vetores = []
for doc in documentos:
    resultado = client.models.embed_content(
        model="gemini-embedding-001",
        contents=doc["texto"]
    )
    vetor = resultado.embeddings[0].values
    vetores.append(vetor)
    print(f"Vetor criado para: {doc['caminho']}")

# Converte a lista de vetores para o formato que o FAISS espera
vetores_np = np.array(vetores).astype("float32")
print(f"Matriz de vetores pronta, formato: {vetores_np.shape}")

# Cria o índice do FAISS
dimensao = vetores_np.shape[1]
indice = faiss.IndexFlatL2(dimensao)
indice.add(vetores_np)
print(f"Índice criado com {indice.ntotal} vetores.")

# Salva o índice FAISS em disco
faiss.write_index(indice, "indice.faiss")

# Salva os textos originais (pra recuperar depois de uma busca)
with open("documentos.pkl", "wb") as arquivo:
    pickle.dump(documentos, arquivo)

print("Índice e documentos salvos com sucesso!")