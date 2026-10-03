\# chatbot-rag-investimentos



Agente de IA conversacional para o domínio financeiro: combina RAG, busca por similaridade (FAISS) e um filtro de escopo para respostas confiáveis e dentro do contexto certo.



\## O que é



Um chatbot que responde perguntas sobre investimentos usando apenas uma base de 20 documentos próprios (RAG - Retrieval-Augmented Generation), em vez de depender só do conhecimento geral do modelo. Isso reduz alucinação e mantém as respostas ancoradas em conteúdo verificável.



O projeto também implementa um gate de entrada que classifica cada pergunta em 5 categorias antes de decidir como responder - inspirado no conceito do Jev (TypeSafe AI), um modelo especializado em decisões tipadas, mas implementado com o Gemini por não exigir custo adicional.



\## Arquitetura



O fluxo de cada pergunta segue 2 etapas: classificação de escopo, depois resposta.



\*\*1. Classificação\*\* - toda pergunta passa primeiro por um classificador (`gemini-3-flash-lite`), que a enquadra em uma de 5 categorias:



| Categoria | O que é | O que acontece a seguir |

|---|---|---|

| Saudação | "oi", "bom dia", sem pergunta técnica | Resposta direta, sem buscar documento |

| Dentro do escopo | Pergunta técnica sobre investimentos | Busca no FAISS, Gemini gera a resposta |

| Fora do escopo | Sem nenhuma relação com investimentos | Mensagem fixa de recusa, sem gastar busca |

| Fronteiriça | Menciona investimentos, mas não é técnica | Mensagem própria, explicando o foco do assistente |

| Mista | Parte técnica + parte sem relação, na mesma mensagem | Busca no FAISS, Gemini declina a parte fora e responde a parte dentro |



\*\*2. Resposta\*\* - nas categorias que chegam até aqui (dentro ou mista), o FAISS busca o documento mais relevante entre os 20 indexados (usando embeddings do `gemini-embedding-001`), e o `gemini-3.8-flash` gera a resposta final, com tom empático e convicto, usando esse documento como referência.



Em todos os casos, a resposta final é gerada pelo Gemini - a diferença entre as categorias está em se e com que contexto ele é chamado.



```mermaid

flowchart TD

&#x20;   A\[Pergunta do usuario] --> B{Classificador}

&#x20;   B -->|saudacao| C\[Gemini gera saudacao]

&#x20;   B -->|dentro do escopo| D\[FAISS busca documento]

&#x20;   B -->|mista| D

&#x20;   B -->|fora do escopo| E\[Mensagem fixa de recusa]

&#x20;   B -->|fronteirica| F\[Mensagem de foco do assistente]

&#x20;   D --> G\[Gemini gera a resposta final]

&#x20;   C --> H\[Resposta ao usuario]

&#x20;   G --> H

&#x20;   E --> H

&#x20;   F --> H

```



\- \*\*Classificador\*\*: `gemini-3-flash-lite` decide se a pergunta é uma saudação, está dentro do escopo de investimentos, está totalmente fora, é fronteiriça (menciona investimentos mas pede algo não técnico) ou é mista (parte dentro, parte fora, na mesma mensagem).

\- \*\*FAISS\*\*: busca por similaridade entre a pergunta e os 20 documentos indexados.

\- \*\*Gemini (`gemini-3.8-flash`)\*\*: gera a resposta final, com tom empático e convicto.

\- \*\*Memória de conversa\*\*: mantida em lista na memória do programa (reinicia a cada execução).

\- \*\*Retry automático\*\*: até 3 tentativas com espera entre elas, para lidar com instabilidade do servidor (erro 503).



\## Como rodar



1\. Clone o repositório e crie um ambiente virtual:



```

python -m venv venv

venv\\Scripts\\Activate

```



2\. Instale as dependências:



```

python -m pip install -r requirements.txt

```



3\. Crie um arquivo `.env` na raiz do projeto com sua chave gratuita do Google AI Studio:



```

GOOGLE\_API\_KEY=sua\_chave\_aqui

```



4\. Gere o índice de busca (só precisa rodar uma vez):



```

python indexar.py

```



5\. Rode o chatbot:



```

python chatbot.py

```



\## Exemplos de uso



\*\*Pergunta técnica simples:\*\*



> Você: CDB

> Chatbot: explica o CDB com base no documento, incluindo tipos de rentabilidade, liquidez e cobertura do FGC



\*\*Pergunta de acompanhamento (testando a memória):\*\*



> Você: Quero investir no tesouro selic, ele é pra perfil conservador?

> Chatbot: confirma que sim, e explica por quê

> Você: e qual a tributação dele?

> Chatbot: entende que "dele" se refere ao Tesouro Selic, sem precisar repetir o nome



\*\*Pergunta fora do escopo:\*\*



> Você: Qual a capital da França?

> Chatbot: Essa pergunta está fora do que posso responder aqui, que é sobre investimentos.



\## Decisões de design



\- \*\*Gemini em vez de Anthropic\*\*: a API da Anthropic exige compra mínima de $5 em créditos, sem camada gratuita. O Gemini tem camada gratuita genuína, sem cartão de crédito.

\- \*\*Gemini como classificador, em vez do Jev real\*\*: o Jev (TypeSafe AI) é um modelo nativo para decisões tipadas, com probabilidade calibrada, e seria tecnicamente mais adequado para a classificação em 5 categorias. Porém, não tem camada gratuita em nenhuma rota de acesso ($0,042 por milhão de tokens de entrada). A solução implementada usa o próprio Gemini, instruído via prompt a responder apenas com a categoria - funciona, mas sem a mesma garantia de confiança calibrada que o Jev ofereceria nativamente.

\- \*\*Modelo mais leve para classificação\*\*: `gemini-3-flash-lite` é usado especificamente na função de classificação, por ter uma cota gratuita diária muito maior (\~500/dia) que o `gemini-3.8-flash` (20/dia).

\- \*\*5 categorias em vez de só "dentro/fora do escopo"\*\*: testes revelaram que perguntas fora do domínio não são todas iguais.

\- \*\*Tom "empático e convicto"\*\*: decisão intencional de comportamento do assistente, não só de conteúdo técnico.



\## Limitações conhecidas



\- A memória de conversa não persiste entre execuções do programa.

\- A memória não realimenta a busca FAISS.

\- O classificador de escopo usa correspondência de texto simples, sem a calibração de confiança que um modelo como o Jev ofereceria nativamente.



\## Próximos passos



\- Interface simples com Streamlit.

\- Casos de teste automatizados para validar o classificador de 5 categorias.

\- Avaliar migração do classificador para o Jev real, caso o custo deixe de ser um impeditivo.

