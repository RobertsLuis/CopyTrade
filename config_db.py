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
    try:
        cursor.execute("SELECT * FROM usuarios WHERE codigo=?", (codigo,))
        usuario = cursor.fetchone()  # Retorna a primeira linha correspondente
        cod, email, nome, data_inscricao, tempo_expiracao = usuario

        data_inscricao = datetime.strptime(data_inscricao, '%d %m %Y')
        today = datetime.strptime('28 03 2024', '%d %m %Y')
        dif = abs((today-data_inscricao).days)
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
            'licenca_ativa': licenca_ativa
        }
        # Fechar a conexão
        conexao.close()
        return response
    except Exception as e:
        print(e)
        return None


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
