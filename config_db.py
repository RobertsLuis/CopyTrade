import sqlite3
from datetime import datetime
import pytz

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

    cursor.executemany(
        """INSERT INTO usuarios (codigo, email ,nome, data_inscricao, tempo_expiracao) 
                          VALUES (?, ?, ?, ?, ?)""",
        usuarios_padrao,
    )

    # Salvar as alterações e fechar a conexão
    conexao.commit()
    conexao.close()


def teste_pesquisar_usuario_por_codigo(codigo):
    # Conectar ao banco de dados
    conexao = sqlite3.connect("cloudzonebd.db")
    cursor = conexao.cursor()

    # Executar a consulta
    cursor.execute("SELECT * FROM usuarios WHERE codigo=?", (codigo,))
    usuario = cursor.fetchone()  # Retorna a primeira linha correspondente
    cod, email, nome, data, tempo_expiracao = usuario

    data = datetime.strptime(data, '%d %m %Y')
    today = datetime.strptime('26 01 2024', '%d %m %Y')
    print(f"Hoje: {today}")
    print(f"Data Obtida: {data}")
    print(f"Diff: {abs((today-data).days)}")
    # Fechar a conexão
    conexao.close()

    return usuario


if __name__ == "__main__":
    criar_banco_de_dados()

    # Teste de pesquisa
    codigo_pesquisar = "9959ROB"
    resultado_pesquisa = teste_pesquisar_usuario_por_codigo(codigo_pesquisar)
    if resultado_pesquisa:
        print("Usuário encontrado:")
        print(resultado_pesquisa)
    else:
        print("Usuário não encontrado.")
