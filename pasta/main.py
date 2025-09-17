# chat_agente.py

import mysql.connector
import google.generativeai as genai
import os
from dotenv import load_dotenv

# --- Configurações do MySQL ---
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "1407"
DB_DATABASE = "agente-ia"

# Carrega a chave de API do arquivo .env
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("A chave de API do Google não foi encontrada. Verifique seu arquivo .env.")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_db_connection(database=None):
    """Retorna uma nova conexão com o banco de dados MySQL."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=database
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Erro de conexão com o MySQL: {err}")
        return None

def configurar_banco_de_dados():
    """Cria o banco de dados e a tabela de clientes no MySQL."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection(database=None)
        if conn is None: return
        cursor = conn.cursor()
        
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_DATABASE}`")
        cursor.execute(f"USE `{DB_DATABASE}`")

        create_table_sql = """
            CREATE TABLE IF NOT EXISTS clientes (
                id INT PRIMARY KEY,
                nome VARCHAR(255),
                renda FLOAT,
                status VARCHAR(50),
                genero VARCHAR(50)
            );
        """
        cursor.execute(create_table_sql)
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Erro ao configurar o banco de dados: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def adicionar_cliente(id, nome, renda, status, genero):
    """Insere um novo cliente na tabela."""
    conn = get_db_connection(database=DB_DATABASE)
    if conn is None: return
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO clientes (id, nome, renda, status, genero) VALUES (%s, %s, %s, %s, %s)"
        data = (id, nome, renda, status, genero)
        cursor.execute(sql, data)
        conn.commit()
        print(f"Cliente '{nome}' adicionado com sucesso!")
    except mysql.connector.Error as err:
        print(f"Erro ao adicionar cliente: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def atualizar_cliente(id, nome, renda, status, genero):
    """Atualiza os dados de um cliente existente de forma parcial."""
    conn = get_db_connection(database=DB_DATABASE)
    if conn is None: return
    cursor = conn.cursor()
    try:
        updates = []
        values = []
        if nome:
            updates.append("nome = %s")
            values.append(nome)
        if renda is not None:
            updates.append("renda = %s")
            values.append(renda)
        if status:
            updates.append("status = %s")
            values.append(status)
        if genero:
            updates.append("genero = %s")
            values.append(genero)

        if not updates:
            print("Nenhum campo para atualizar.")
            return

        sql = f"UPDATE clientes SET {', '.join(updates)} WHERE id = %s"
        values.append(id)
        cursor.execute(sql, tuple(values))
        conn.commit()
        print(f"Cliente de ID {id} atualizado com sucesso!")
    except mysql.connector.Error as err:
        print(f"Erro ao atualizar cliente: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def deletar_cliente(id):
    """Deleta um cliente da tabela."""
    conn = get_db_connection(database=DB_DATABASE)
    if conn is None: return
    cursor = conn.cursor()
    try:
        sql = "DELETE FROM clientes WHERE id = %s"
        cursor.execute(sql, (id,))
        conn.commit()
        print(f"Cliente de ID {id} deletado com sucesso!")
    except mysql.connector.Error as err:
        print(f"Erro ao deletar cliente: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def contar_clientes():
    """Conta o número de clientes na tabela."""
    conn = get_db_connection(database=DB_DATABASE)
    if conn is None: return 0
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM clientes")
        count = cursor.fetchone()[0]
        return count
    except mysql.connector.Error as err:
        print(f"Erro ao contar clientes: {err}")
        return 0
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def executar_query(query_sql):
    """Executa uma consulta SQL no banco de dados e retorna o resultado."""
    conn = get_db_connection(database=DB_DATABASE)
    if conn is None: return None
    cursor = conn.cursor()
    try:
        cursor.execute(query_sql)
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Erro ao executar a query: {err}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def agente_gemma_com_rag(pergunta_usuario):
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
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Erro na API do Gemma: {e}")
        return None

def iniciar_chat():
    print("Olá! Sou um agente de IA para o banco de dados de clientes.")
    print("Você pode me fazer perguntas, como 'Quantos estão com o nome sujo?'.")
    print("Para adicionar um cliente, digite 'adicionar cliente'.")
    print("Para atualizar um cliente, digite 'atualizar cliente'.")
    print("Para deletar um cliente, digite 'deletar cliente'.")
    print("Digite 'sair' para terminar.")
    print("-" * 50)
    
    while True:
        pergunta = input("Você: ")
        comando = pergunta.lower().strip()
        
        # Lógica para orientar o usuário
        if comando.startswith('atualize') or comando.startswith('mude') or comando.startswith('altere'):
            print("Agente: Para atualizar um cliente, por favor, digite o comando 'atualizar cliente'.")
            print("-" * 50)
            continue
        elif comando.startswith('deletar') or comando.startswith('remova') or comando.startswith('apague'):
            print("Agente: Para deletar um cliente, por favor, digite o comando 'deletar cliente'.")
            print("-" * 50)
            continue
        elif comando.startswith('adicione') or comando.startswith('crie'):
            print("Agente: Para adicionar um cliente, por favor, digite o comando 'adicionar cliente'.")
            print("-" * 50)
            continue
        
        # Comandos diretos de CRUD
        if comando == 'sair':
            print("Até a próxima!")
            break
        elif comando == 'adicionar cliente':
            try:
                novo_id = int(input("Digite o ID: "))
                novo_nome = input("Digite o nome: ")
                nova_renda = float(input("Digite a renda: "))
                novo_status = input("Digite o status ('ativo' ou 'nome sujo'): ")
                novo_genero = input("Digite o gênero ('masculino' ou 'feminino'): ")
                adicionar_cliente(novo_id, novo_nome, nova_renda, novo_status, novo_genero)
            except ValueError:
                print("Entrada inválida. ID e renda devem ser números.")
            print("-" * 50)
            continue
        elif comando == 'atualizar cliente':
            try:
                id_para_atualizar = int(input("Digite o ID do cliente que deseja atualizar: "))
                print("Digite as novas informações (deixe em branco para campos que não irá mudar):")
                novo_nome = input("Novo nome: ") or None
                nova_renda_str = input("Nova renda: ") or None
                novo_status = input("Novo status ('ativo' ou 'nome sujo'): ") or None
                novo_genero = input("Novo gênero ('masculino' ou 'feminino'): ") or None
                nova_renda = float(nova_renda_str.replace(',', '.')) if nova_renda_str else None
                atualizar_cliente(id_para_atualizar, novo_nome, nova_renda, novo_status, novo_genero)
            except ValueError:
                print("Entrada inválida. O ID e a renda devem ser números.")
            print("-" * 50)
            continue
        elif comando == 'deletar cliente':
            try:
                id_para_deletar = int(input("Digite o ID do cliente que deseja deletar: "))
                deletar_cliente(id_para_deletar)
            except ValueError:
                print("Entrada inválida. O ID deve ser um número inteiro.")
            print("-" * 50)
            continue

        # Lógica para perguntas que usam o agente de IA
        query_sql = agente_gemma_com_rag(pergunta)
        
        if query_sql:
            resultado = executar_query(query_sql)
            if resultado:
                print("Agente: Aqui está o resultado da sua pergunta:")
                for linha in resultado:
                    print(f"    - {linha}")
            else:
                print("Agente: Não foi possível obter os dados. Verifique a query ou o banco.")
        else:
            print("Agente: Desculpe, não entendi a pergunta ou houve um erro. Tente ser mais específico.")

if __name__ == "__main__":
    configurar_banco_de_dados()
    if contar_clientes() == 0:
        print("Tabela de clientes vazia. Adicionando dados iniciais...")
        adicionar_cliente(1, 'João da Silva', 5000.00, 'ativo', 'masculino')
        adicionar_cliente(2, 'Maria Souza', 1200.50, 'nome sujo', 'feminino')
        adicionar_cliente(3, 'Carlos Santos', 8500.75, 'ativo', 'masculino')
        adicionar_cliente(4, 'Ana Rodrigues', 2500.00, 'nome sujo', 'feminino')
        adicionar_cliente(5, 'Pedro Almeida', 3200.00, 'ativo', 'masculino')
        adicionar_cliente(6, 'Fernanda Lima', 900.00, 'nome sujo', 'feminino')
    else:
        print("Tabela de clientes já contém dados. Pulando a inserção inicial.")
    
    iniciar_chat()