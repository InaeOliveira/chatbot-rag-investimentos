import os
import time
import pickle
import numpy as np
import faiss
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Carrega o índice FAISS e os documentos que já foram processados pelo indexar.py
indice = faiss.read_index("indice.faiss")
with open("documentos.pkl", "rb") as arquivo:
    documentos = pickle.load(arquivo)

print(f"Índice carregado com {indice.ntotal} documentos.")


def chamar_gemini_com_retry(prompt, modelo="gemini-3.8-flash", tentativas=3):
    for tentativa in range(1, tentativas + 1):
        try:
            resposta = client.models.generate_content(
                model=modelo,
                contents=prompt
            )
            return resposta.text
        except Exception as erro:
            if tentativa < tentativas:
                print(f"(Servidor ocupado, tentando de novo... {tentativa}/{tentativas})")
                time.sleep(3)
            else:
                raise erro


def classificar_pergunta(pergunta):
    prompt_classificador = f"""Classifique a mensagem do usuário em exatamente UMA das categorias abaixo. Responda apenas com a palavra da categoria (em minúsculas), sem nenhum outro texto.

Categorias:
- saudacao: é apenas uma saudação ou mensagem social (oi, bom dia, tudo bem, obrigado), sem nenhuma pergunta sobre investimentos.
- dentro: a mensagem inteira é uma pergunta técnica sobre investimentos e mercado financeiro.
- fora: a mensagem inteira é sobre um assunto sem nenhuma relação com investimentos.
- fronteirico: a mensagem menciona investimentos, mas pede algo que não é uma explicação técnica (ex: recomendação de filme, livro, notícia, opinião pessoal).
- misto: a mensagem contém, ao mesmo tempo, uma parte com pergunta técnica sobre investimentos E outra parte sobre um assunto completamente não relacionado.

Mensagem do usuário: {pergunta}

Categoria:"""

    texto_resposta = chamar_gemini_com_retry(prompt_classificador, modelo="gemini-3-flash-lite")
    categoria = texto_resposta.strip().lower()
    categorias_validas = ["saudacao", "dentro", "fora", "fronteirico", "misto"]

    for c in categorias_validas:
        if c in categoria:
            return c

    # Se o Gemini responder algo inesperado, assume "dentro" como caminho mais seguro
    return "dentro"


def buscar_documento_relevante(pergunta):
    # Transforma a pergunta num vetor, do mesmo jeito que fizemos com os documentos
    resultado = client.models.embed_content(
        model="gemini-embedding-001",
        contents=pergunta
    )
    vetor_pergunta = np.array([resultado.embeddings[0].values]).astype("float32")

    # Busca o documento mais parecido (1 resultado, o mais próximo)
    distancias, indices_encontrados = indice.search(vetor_pergunta, k=1)

    indice_do_documento = indices_encontrados[0][0]
    documento_encontrado = documentos[indice_do_documento]

    return documento_encontrado


def gerar_resposta(pergunta, documento, historico, categoria):
    # Monta o histórico da conversa em texto, pra dar contexto ao Gemini
    contexto_conversa = ""
    for turno in historico:
        contexto_conversa += f"Usuário: {turno['pergunta']}\n"
        contexto_conversa += f"Assistente: {turno['resposta']}\n"

    instrucao_extra = ""
    if categoria == "misto":
        instrucao_extra = "\nIMPORTANTE: essa mensagem contém uma parte sobre investimentos e outra parte sobre um assunto sem relação nenhuma com o tema. Primeiro, decline educadamente a parte fora do escopo, deixando claro que seu foco é investimentos. Depois, na mesma resposta, responda normalmente a parte sobre investimentos usando o documento de referência abaixo.\n"

    prompt = f"""Você é um assistente especializado em investimentos.
Responda à pergunta do usuário com empatia e convicção, usando o documento de referência abaixo.
Se o documento não tiver a informação necessária, diga isso claramente, sem inventar.
{instrucao_extra}
Histórico da conversa até agora:
{contexto_conversa}

Documento de referência ({documento['caminho']}):
{documento['texto']}

Pergunta atual do usuário: {pergunta}

Resposta:"""

    return chamar_gemini_com_retry(prompt)


def gerar_resposta_saudacao(pergunta, historico):
    contexto_conversa = ""
    for turno in historico:
        contexto_conversa += f"Usuário: {turno['pergunta']}\n"
        contexto_conversa += f"Assistente: {turno['resposta']}\n"

    prompt = f"""Você é um assistente especializado em investimentos, com um tom empático e caloroso.
O usuário te enviou uma saudação ou mensagem social, não uma pergunta técnica.
Responda de forma breve e amigável, e convide a pessoa a perguntar sobre investimentos.

Histórico da conversa até agora:
{contexto_conversa}

Mensagem do usuário: {pergunta}

Resposta:"""

    return chamar_gemini_com_retry(prompt)


# Lista que guarda o histórico da conversa (pergunta + resposta de cada rodada)
historico = []

print("\nChatbot de investimentos pronto! Digite 'sair' para encerrar.\n")

while True:
    pergunta = input("Você: ")

    if pergunta.lower() == "sair":
        print("Até mais!")
        break

    try:
        categoria = classificar_pergunta(pergunta)

        if categoria == "saudacao":
            resposta = gerar_resposta_saudacao(pergunta, historico)
            print(f"Chatbot: {resposta}\n")

        elif categoria == "fora":
            resposta = "Essa pergunta está fora do que posso responder aqui, que é sobre investimentos."
            print(f"Chatbot: {resposta}\n")

        elif categoria == "fronteirico":
            resposta = "Fico feliz com seu interesse nesse tema! Mas especificamente essa resposta eu ainda não tenho. Meu foco é te ajudar com a parte técnica e de definição dos investimentos."
            print(f"Chatbot: {resposta}\n")

        else:
            # categoria "dentro" ou "misto" seguem para a busca normal
            documento = buscar_documento_relevante(pergunta)
            resposta = gerar_resposta(pergunta, documento, historico, categoria)
            print(f"Chatbot: {resposta}\n")

    except Exception as erro:
        print(f"Ocorreu um erro ao gerar a resposta. Tente novamente. ({erro})\n")
        continue

    historico.append({"pergunta": pergunta, "resposta": resposta})