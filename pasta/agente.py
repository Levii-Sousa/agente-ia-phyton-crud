# agente.py

import google.generativeai as genai
import os

class AgenteDeDados:
    """Gerencia a comunicação com o modelo Gemma."""

    def __init__(self, api_key, model_name='gemini-1.5-flash'):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def traduzir_para_sql(self, pergunta_usuario):
        """Usa o Gemma para traduzir a pergunta para SQL com RAG."""
        prompt = f"""
        Você é um tradutor de perguntas em linguagem natural para consultas SQL. Sua única e estrita tarefa é converter a pergunta do usuário em uma consulta SQL válida, sem adicionar nenhum outro texto.

        Regras e Formato da Resposta:
        1. A resposta deve conter SOMENTE a consulta SQL, sem aspas, blocos de código ou explicações.
        2. A consulta deve ser completa e válida para o MySQL.

        Instruções Detalhadas sobre o Banco de Dados:
        A tabela principal que você deve usar é 'clientes'.
        - colunas:
          - id (INT): identificador único
          - nome (VARCHAR(255)): nome completo do cliente
          - renda (FLOAT): renda mensal em reais
          - status (VARCHAR(50)): status do cliente. Os valores possíveis são 'ativo' ou 'nome sujo'.
          - genero (VARCHAR(50)): o sexo do cliente. Os valores possíveis são 'masculino' ou 'feminino'.

        Exemplos de Tradução:
        - Pergunta: Qual o número de clientes com nome sujo?
        - SQL: SELECT COUNT(*) FROM clientes WHERE status = 'nome sujo';

        - Pergunta: Qual a renda do cliente de nome 'João da Silva'?
        - SQL: SELECT renda FROM clientes WHERE nome = 'João da Silva';

        - Pergunta: Me diga o nome dos clientes que têm uma renda maior que 2000?
        - SQL: SELECT nome FROM clientes WHERE renda > 2000;

        - Pergunta: Qual a média de renda de todos os clientes?
        - SQL: SELECT AVG(renda) FROM clientes;

        - Pergunta: Quantos clientes do sexo masculino com nome sujo existem?
        - SQL: SELECT COUNT(*) FROM clientes WHERE genero = 'masculino' AND status = 'nome sujo';

        Pergunta do Usuário:
        {pergunta_usuario}

        Sua Resposta (APENAS o código SQL):
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except genai.types.APIError as e:
            print(f"Erro na API do Gemma: {e}")
            return None
        except genai.types.RateLimitError as e:
            print(f"Limite de requisições atingido: {e}")
            return None
        except genai.types.AuthenticationError as e:
            print(f"Erro de autenticação com a API do Gemma: {e}")
            return None
        except Exception as e:
            print(f"Erro na API do Gemma: {e}")
            return None