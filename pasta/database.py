# database.py

import mysql.connector
import os

class ConexaoBancoDados:
    """Gerencia a conexão com o banco de dados MySQL."""

    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
    
    def get_connection(self):
        """Retorna uma nova conexão com o banco de dados MySQL."""
        try:
            conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            return conn
        except mysql.connector.Error as err:
            print(f"Erro de conexão com o MySQL: {err}")
            return None

    def get_connection_no_db(self):
        """Retorna uma conexão sem um banco de dados específico."""
        try:
            conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            return conn
        except mysql.connector.Error as err:
            print(f"Erro de conexão com o MySQL: {err}")
            return None

class GerenciadorClientes:
    """Lida com as operações CRUD na tabela de clientes."""

    def __init__(self, db_conn):
        self.db_conn = db_conn

    def configurar_tabela(self):
        """Cria o banco de dados e a tabela de clientes no MySQL."""
        conn = None
        cursor = None
        try:
            conn = self.db_conn.get_connection_no_db()
            if conn is None: return
            cursor = conn.cursor()
            
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.db_conn.database}`")
            print(f"Banco de dados '{self.db_conn.database}' verificado/criado com sucesso.")

            create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS `{self.db_conn.database}`.clientes (
                    id INT PRIMARY KEY,
                    nome VARCHAR(255),
                    renda FLOAT,
                    status VARCHAR(50),
                    genero VARCHAR(50)
                );
            """
            cursor.execute(create_table_sql)
            
            conn.commit()
            print("Tabela 'clientes' verificada/criada com sucesso.")
            
        except mysql.connector.Error as err:
            print(f"Erro ao configurar o banco de dados: {err}")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    def adicionar_cliente(self, id, nome, renda, status, genero):
        """Insere um novo cliente na tabela."""
        conn = self.db_conn.get_connection()
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

    def atualizar_cliente(self, id, nome, renda, status, genero):
        """Atualiza os dados de um cliente existente de forma parcial."""
        conn = self.db_conn.get_connection()
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
    
    def deletar_cliente(self, id):
        """Deleta um cliente da tabela."""
        conn = self.db_conn.get_connection()
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

    def contar_clientes(self):
        """Conta o número de clientes na tabela."""
        conn = self.db_conn.get_connection()
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

    def executar_query(self, query_sql):
        """Executa uma consulta SQL no banco de dados e retorna o resultado."""
        conn = self.db_conn.get_connection()
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