import sqlite3
from datetime import datetime
import pytz
import random

tz = pytz.timezone("America/Sao_Paulo")


def criar_banco_de_dados():
    # Conectar ou criar o banco de dados na pasta root
    conexao = sqlite3.connect("cloudzonebd.db")
    cursor = conexao.cursor()

    # Criar a tabela de usuários
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS usuarios (
                        codigo TEXT,
                        email TEXT,
                        nome TEXT,
                        data_inscricao TEXT,
                        tempo_expiracao INTEGER
                    )"""
    )

    # Criar a tabela de resultados
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS resultados (
                        data TEXT,
                        log_completo TEXT,
                        sim_completo TEXT,
                        log_retracao TEXT,
                        sim_retracao TEXT
                    )"""
    )

    usuarios_padrao = [
        (
            "9959ROB",
            "bejr2002@gmail.com",
            "Roberto Luis",
            datetime.now(tz).strftime("%d %m %Y"),
            9999,
        ),
        (
            "2459VIC",
            "belmorvictor@gmail.com",
            "Victor Belmor",
            datetime.now(tz).strftime("%d %m %Y"),
            9999,
        ),
        (
            "7594REN",
            "rey.iqop@gmail.com",
            "Renan Macedo",
            datetime.now(tz).strftime("%d %m %Y"),
            9999,
        ),
        (
            "2133FLO",
            "neto_paixao2013@hotmail.com",
            "Florisvaldo Neto",
            datetime.now(tz).strftime("%d %m %Y"),
            9999,
        ),
    ]

    for usuario in usuarios_padrao:
        codigo, email, nome, data_inscricao, tempo_expiracao = usuario
        cursor.execute(
            """INSERT INTO usuarios (codigo, email ,nome, data_inscricao, tempo_expiracao) 
                            SELECT ?, ?, ?, ?, ? 
                            WHERE NOT EXISTS (
                                SELECT 1 FROM usuarios WHERE codigo = ? OR email = ?
                            )""",
            (codigo, email, nome, data_inscricao, tempo_expiracao, codigo, email),
        )

    # Salvar as alterações e fechar a conexão
    conexao.commit()
    conexao.close()
def pesquisar_usuario(codigo):
    # Conectar ao banco de dados
    conexao = sqlite3.connect("cloudzonebd.db")
    cursor = conexao.cursor()

    # Executar a consulta
    try:
        cursor.execute("SELECT * FROM usuarios WHERE codigo=?", (codigo,))
        usuario = cursor.fetchone()  # Retorna a primeira linha correspondente
        cod, email, nome, data_inscricao, tempo_expiracao = usuario

        data_inscricao = datetime.strptime(data_inscricao, '%d %m %Y')
        today = datetime.strptime(datetime.now(tz).strftime('%d %m %Y'), '%d %m %Y')
        dif = (today-data_inscricao).days
        licenca_ativa = dif<tempo_expiracao

        print(f"Hoje: {today}")
        print(f"Data Obtida: {data_inscricao}")
        print(f"Diff: {dif}")
        print(f"Licença ativa: {licenca_ativa}")

        response = {
            'email': email,
            'nome': nome,
            'data': data_inscricao,
            'tempo_expiracao': tempo_expiracao,
            'diferenca_dias': dif,
            'licenca_ativa': licenca_ativa
        }
        # Fechar a conexão
        conexao.close()
        return response
    except Exception as e:
        print(e)
        return None
    
def criar_usuario(nome, email, tempo_expiracao):
    letras_nome = nome[0:3].upper()
    usuario_pesquisado = True

    conexao = sqlite3.connect("cloudzonebd.db")
    cursor = conexao.cursor()

    while usuario_pesquisado:
        digitos = random.randint(0, 9999)
        digitos_formatados = '{:04}'.format(digitos)
        novo_codigo = digitos_formatados+letras_nome
        usuario_pesquisado = pesquisar_usuario(novo_codigo)

    novo_usuario = (novo_codigo, email, nome, datetime.now(tz).strftime('%d %m %Y'), tempo_expiracao)
    try:
        cursor.execute(
                """INSERT INTO usuarios (codigo, email ,nome, data_inscricao, tempo_expiracao) 
                                SELECT ?, ?, ?, ?, ?""",
                (novo_codigo, email, nome, datetime.now(tz).strftime('%d %m %Y'), tempo_expiracao),
            )
        conexao.commit()
        conexao.close()
        return (True, novo_codigo)
    except Exception as e:
        print(e)
        conexao.close()
        return (False, f"Erro ao inserir novo usuário: {e}")
    
    

def renovar_usuario(codigo, tempo_expiracao):
    conexao = sqlite3.connect("cloudzonebd.db")
    cursor = conexao.cursor()

    # Executar a consulta
    usuario = pesquisar_usuario(codigo)
    if usuario:
        try:
            dif = usuario['tempo_expiracao'] - usuario['diferenca_dias']
            tempo_expiracao += usuario['tempo_expiracao'] if dif>0 else tempo_expiracao
            cursor.execute(
                """UPDATE usuarios 
                SET data_inscricao = ?, tempo_expiracao = ? 
                WHERE codigo = ?""",
                (datetime.now(tz).strftime('%d %m %Y'), tempo_expiracao, codigo)
            )
            conexao.commit()
            conexao.close()
            return (True, "Renovado com sucesso")
        except Exception as e:
            print(e)
            conexao.close()
            return (False, "Erro ao atualizar o banco")
        
    else:
        conexao.close()
        return (None, "Usuario não encontrado")
    
    




'''if __name__ == "__main__":
    criar_banco_de_dados()

    # Teste de pesquisa
    codigo_pesquisar = "9959ROB"
    resultado_pesquisa = pesquisar_usuario(codigo_pesquisar)
    if resultado_pesquisa:
        print("Usuário encontrado:")
        print(resultado_pesquisa)
    else:
        print("Usuário não encontrado.")
'''