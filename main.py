#!/usr/bin/python3

import telegram
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, \
    InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, \
    CallbackQueryHandler, Updater
from iqoptionapi.stable_api import IQ_Option

import time
import math
from datetime import datetime
import threading
from multiprocessing import Process, Event, Manager, set_start_method, Lock
import os
import pytz
import sys

import asyncio

token = "6485467359:AAFZZuUeP846mDcyhKs887Hs-LqjGoKJHrw"
botUsername = "@wzTaxa_bot"
tz = pytz.timezone('America/Sao_Paulo')

# TEM QUE TER THREAD PARA VERIFICAR EM TODAS AS CONTAS SE TEM STOP WIN OU STOP LOSS
#TODO MONTAR UMA LÓGICA PARA ENVIAR INFORMAÇÕES DE CONTAS QUE PEDIRAM PARA SER STOPADAS ABRUPTAMENTE -> 
MENU_OPTIONS, CODIGO_BOT, CADASTRO_SENHA, REAL_DEMO, FIXO_PERCENTUAL, TRADE_MODE,CONFIG_STAKE, STOP_WIN, STOP_LOSS, CONFIRMACAO_CONFIG, MENU_STOP = range(11)


# Comandos
def showConfigs(context):
    context.user_data['ultima_modificacao'] = datetime.now(tz).strftime("%H:%M:%S")
    linhas = [
        f"📩 Conta: {context.user_data['email']}",
        # f"💰 Banca inicial: {context.user_data['banca_inicial']}",
        "⚙️ Tipo de conta: REAL 🟢" if context.user_data['tipo_conta'] == 'REAL' else "⚙️ Tipo de conta: DEMO 🟠",
        "▶️ Modo operacional: RT+RV" if context.user_data['trade_rv'] == True else "▶️ Modo operacional: Apenas RT",
        f"\n📍 Stake: R${context.user_data['stake']}" if context.user_data['modo_config'] == 'Valor' else f"📍 Stake: {context.user_data['stake']}%",
        f"📍 Stop Win: R${context.user_data['stop_win']}" if context.user_data['modo_config'] == 'Valor' else f"📍 Stop Win: {context.user_data['stop_win']}%",
        f"📍 Stop Loss: R${context.user_data['stop_loss']}" if context.user_data['modo_config'] == 'Valor' else f"📍 Stop Loss: {context.user_data['stop_loss']}%",

        f"\n⏱️ Última modificação: {context.user_data['ultima_modificacao']}"
    ]

    return "\n".join(linhas)


async def main_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(context.user_data)
    keyboard = [
        [KeyboardButton("Iniciar Bot")],
        [KeyboardButton("Ver placar")],
        [KeyboardButton("Parar Bot")],
        [KeyboardButton("Suporte")]
    ]
    mainMenu = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    # Enviando a mensagem com o menu
    await update.message.reply_text("Selecione uma opção:", reply_markup=mainMenu, parse_mode='Markdown')

    # Definindo o estado para a etapa do menu
    return MENU_OPTIONS

async def partial_result_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global resultados
    partial_result = f"Placar até o momento: ✅ {resultados.count('✅')} | ❌ {resultados.count('❌')} | ⚪ {resultados.count('⚪')}"
    # Enviando a mensagem com o menu
    await update.message.reply_text(f"{partial_result}", reply_markup=ReplyKeyboardRemove())
    # Definindo o estado para a etapa do menu
    return ConversationHandler.END

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Definindo o estado para a etapa do menu
    print('set')
    return MENU_STOP

def resultado_separado(trade_rv, mensagem):
    aux_finalMessage = mensagem.split("\n")
    
    for i,line in enumerate(aux_finalMessage):
        if line.startswith("M5"):
            spaces = len(line.split(' '))
            if trade_rv == True:
                if '*' in line:
                    spaces = len(line.split(' '))
                    line = line.replace("*", "")
                    if spaces == 9:
                        aux_finalMessage[i] = " ".join(line.split(" ")[0:4]+line.split(" ")[5:])
                    else:
                        aux_finalMessage[i] = " ".join(line.split(" ")[0:4]+line.split(" ")[8:])
            else:
                if '*' in line:
                    #print(line)
                    spaces = len(line.split(' '))
                    line = line.replace("*", "")
                    if spaces == 9:
                        aux_finalMessage[i] = " ".join(line.split(" ")[0:5])
                    else:
                        aux_finalMessage[i] = " ".join(line.split(" ")[0:8])

    return aux_finalMessage


async def listaDeTransmissao(context: ContextTypes.DEFAULT_TYPE):
    # Beep the person who called this alarm:
    global mensagemTransmissao, mensagensEnviadas, contasStopadas
    if mensagemTransmissao != [] and not(context.job.data['email'] in contasStopadas) and not(f"{context.job.chat_id}: {mensagemTransmissao}" in mensagensEnviadas):
        

        mensagemParaEnviar = ""
        mensagensFiltradas = []
        for titulo, mensagem in mensagemTransmissao:
            match titulo:
                #🎯 TRADE REALIZADA - RETRAÇÃO M5 🎯 NÃO PRECISA DE TRATAMENTO
                #🎯 TRADE(S) REALIZADA(S) - REVERSÃO M5 🎯 V
                #⏱️ TRADE AGENDADA - REVERSÃO M5 ⏱️ V
                #🎯 RESULTADO DA TRADE 🎯 V
                #🔐 MENSAGEM PRIVADA 🔐 V
                case '🔐 MENSAGEM PRIVADA 🔐':
                    if context.job.data['email'] in mensagem:
                        mensagensFiltradas.append(mensagem)
                case '⏱️ TRADE AGENDADA - REVERSÃO M5 ⏱️':
                    if context.job.data['trade_rv'] == False:
                        mensagensFiltradas.append(mensagem.replace('⏱️ TRADE AGENDADA - REVERSÃO M5 ⏱️','🎯 TRADE REALIZADA - RETRAÇÃO M5 🎯'))
                    else:
                        mensagensFiltradas.append(mensagem)
                case '🎯 TRADE(S) REALIZADA(S) - REVERSÃO M5 🎯':
                    if context.job.data['trade_rv'] == True:
                        mensagensFiltradas.append(mensagem)
                case '🎯 RESULTADO DA TRADE 🎯':
                    if 'RT*' in mensagem.split("\n")[-1]:
                        if context.job.data['trade_rv'] == False:
                            mensagensFiltradas.append(mensagem)
                    elif 'RV' in mensagem.split("\n")[-1]:
                        if context.job.data['trade_rv'] == True:
                            mensagensFiltradas.append(mensagem)
                    else:
                        mensagensFiltradas.append(mensagem)
                case '🚨 TRADE CANCELADA 🚨':
                    if "Motivo: Taxa atingida no fechamento da vela" in mensagem:
                        if context.job.data['trade_rv'] == False:
                            mensagensFiltradas.append(mensagem)
                    else:
                        mensagensFiltradas.append(mensagem)
                case _:
                    mensagensFiltradas.append(mensagem)

        if len(mensagensFiltradas) == 0:
            pass
        else:
            trades_canceladas = ''
            if len(mensagensFiltradas)==1:
                mensagemParaEnviar  = mensagensFiltradas[0]
            elif len(mensagensFiltradas)>1:
                for i,info in enumerate(mensagensFiltradas):
                    if "🚨 TRADE CANCELADA 🚨" in info:    
                        trades_canceladas += " ".join(info.split("\n")[1:4])
                    elif " ".join(info.split('\n')[1:4]) in trades_canceladas:        
                        continue
                    mensagemParaEnviar +=f"\n\n{'-' * 43}\n\n{info}" if i > 0 else f"{info}"
            
            if not("📝 RESULTADOS" in mensagemParaEnviar):
                await context.bot.send_message(chat_id=context.job.chat_id, text=f'{mensagemParaEnviar}')
            else:
                aux_finalMessage = mensagemParaEnviar.split('\n')
                for i,line in enumerate(aux_finalMessage):
                    if line.startswith("M5"):
                        spaces = len(line.split(' '))
                        if context.job.data['trade_rv'] == True:
                            if '*' in line:
                                spaces = len(line.split(' '))
                                line = line.replace("*", "")
                                if spaces == 9:
                                    aux_finalMessage[i] = " ".join(line.split(" ")[0:4]+line.split(" ")[5:])
                                else:
                                    aux_finalMessage[i] = " ".join(line.split(" ")[0:4]+line.split(" ")[8:])
                        else:
                            if '*' in line:
                                #print(line)
                                spaces = len(line.split(' '))
                                line = line.replace("*", "")
                                if spaces == 9:
                                    aux_finalMessage[i] = " ".join(line.split(" ")[0:5])
                                else:
                                    aux_finalMessage[i] = " ".join(line.split(" ")[0:8])
                #aux_finalMessage.pop(-1)
                try:
                    for message in str(aux_finalMessage).split('-'*43):
                        if '📝 RESULTADOS' in message:
                            results_aux_finalMessage = message
                except:
                    results_aux_finalMessage = str(aux_finalMessage)
                    
                acc_wins = results_aux_finalMessage.count('✅')
                acc_loses = results_aux_finalMessage.count('❌')
                acc_dojis =results_aux_finalMessage.count('⚪')
                aux_finalMessage.append(f"\n✅ {acc_wins} | ❌ {acc_loses} | ⚪ {acc_dojis}")
                
                mensagemParaEnviar = '\n'.join(aux_finalMessage)
                await context.bot.send_message(chat_id=context.job.chat_id, text=f"{mensagemParaEnviar}")
                
                lucro = round((context.job.data['stake']*acc_wins)*0.85,2)
                prejuizo = round(context.job.data['stake']*acc_loses,2)

                mensagemParaEnviar = f"📝 SIMULAÇÃO DE RESULTADO 📝\n⏱️ {datetime.now(tz).strftime('%d/%m/%Y')}:"
                mensagemParaEnviar += f"\nModo de trade: RT+RV" if context.job.data['trade_rv'] else f"\nModo de trade: Apenas RT\nPayout Médio: 85%"

                eng_unit = 'R$' if context.job.data['modo_config'] == 'Valor' else '%'
                mensagemParaEnviar += f"\nSua stake: {context.job.data['stake']}{eng_unit}\nResultado diário: {round(lucro-prejuizo,2)}{eng_unit}" 
                await context.bot.send_message(chat_id=context.job.chat_id, text=f"{mensagemParaEnviar}")


            if "Stop Win" in mensagemParaEnviar or "Stop Loss" in mensagemParaEnviar:
                contasStopadas.append(context.job.data['email'])
        print("Conta: {} | Mensagens filtradas: {} | Mensagem para enviar: {}".format(context.job.data['email'], mensagensFiltradas, mensagemParaEnviar))
        mensagensEnviadas.append(f"{context.job.chat_id}: {mensagemTransmissao}")
    # context.user_data['messagesReceived'] += f' {mensagemTransmissao}'


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Link ytb como usar\nCaso tenha algum outro problema que não esteja presente no vídeo, entre em contato com @Winnerzone_83", reply_markup=ReplyKeyboardRemove())


# Função para lidar com a escolha no menu
async def menu_options_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global resultados
    # Obtendo a escolha do usuário
    user_choice = update.message.text.lower()

    if user_choice == 'iniciar bot':
        # Pedindo que o usuário forneça o email
        try:
            if contas[context.user_data['email']] == True:
                await update.message.reply_text(f"Você já tem um bot rodando nesse chat, não é permitido iniciar 2 contas ao mesmo tempo", reply_markup=ReplyKeyboardRemove())
                return ConversationHandler.END
        except:

            await update.message.reply_text("Ok! Antes disso, forneça o seu código do bot da WZ. (Esse código foi passado para você no momento da compra da licença)", reply_markup=ReplyKeyboardRemove())
            # Definindo o estado para a etapa do email no cadastro
            return CODIGO_BOT
    elif user_choice == 'suporte':
        await update.message.reply_text(
            "Link ytb como usar\nCaso tenha algum outro problema que não esteja presente no vídeo, entre em contato com @Winnerzone_83")
    elif user_choice == 'ver placar':
        
        result = "\n".join(resultado_separado(context.user_data['trade_rv'],resultados))
        print(result)
        partial_result = f"Placar até o momento: ✅ {result.count('✅')} | ❌ {result.count('❌')} | ⚪ {result.count('⚪')}"

        # Enviando a mensagem com o menu
        await update.message.reply_text(f"{partial_result}", reply_markup=ReplyKeyboardRemove())

        # Definindo o estado para a etapa do menu
        return ConversationHandler.END
    elif user_choice == 'parar bot':
        result = "\n".join(resultado_separado(context.user_data['trade_rv'],resultados))
        print(result)
        partial_result = f"Placar até o momento: ✅ {result.count('✅')} | ❌ {result.count('❌')} | ⚪ {result.count('⚪')}"
        keyboard = [
            [KeyboardButton("Parar bot")],
            [KeyboardButton("Continuar operando")]
        ]
        stopBotMenu = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    # Enviando a mensagem com o menu
        await update.message.reply_text(f"Tem certeza que deseja parar?\n\n{partial_result}", reply_markup=stopBotMenu)
        return MENU_STOP
    else:
        # Opção inválida, reinicie a conversa
        #await update.message.reply_text("Opção inválida. Por favor, selecione uma opção válida.")
        pass
    # Reiniciando a conversa
    return ConversationHandler.END


async def codigo_bot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("Iniciar Bot")],
        [KeyboardButton("Ver placar")],
        [KeyboardButton("Parar Bot")],
        [KeyboardButton("Suporte")]
    ]
    mainMenu = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    # Obtendo o email do usuário
    codigo = update.message.text

    lista_codigos = ['1', '2', '3', '4', 'teste1', 'teste2']
    if codigo in lista_codigos:
        if codigo == '1':
            context.user_data['email'] = 'bejr2002@gmail.com'
        elif codigo == '2':
            context.user_data['email'] = 'rey.iqop@gmail.com'
        elif codigo == '3':
            context.user_data['email'] = 'belmorvictor@gmail.com'
        elif codigo == '4':
            context.user_data['email'] = 'neto_paixao2013@hotmail.com'
        elif codigo == 'teste1':
            context.user_data['trades'] = []
            informacoes_conta = {
                'email': 'bejr2002@gmail.com',
                'senha': 'Bejr2002!',
                'tipo_conta': 'DEMO',
                'trade_rv': False,
                'modo_config': 'Valor',
                'stake': 150,
                'stop_win': 200,
                'stop_loss': 200,
            }
            x = Process(target=aguardar_compra, args=(informacoes_conta, tradeEvent, info_trade, contas, buy, buy_multi, monitorStopThread, pendingTrades, aux_mensagemTransmissao,))
            x.start()
            contas[informacoes_conta['email']] = True

            email = informacoes_conta['email']
            chat_id = update.message.chat_id

            context.job_queue.run_repeating(listaDeTransmissao, data=informacoes_conta, chat_id=chat_id, interval=1, first=1)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Configurações salvas com sucesso!", reply_markup=mainMenu)
            print(f"{showConfigs(context)}")
            return MENU_OPTIONS
        elif codigo == 'teste2':
            context.user_data['trades'] = []
            informacoes_conta = {
                'email': 'rey.iqop@gmail.com',
                'senha': 'IQ@08840051511',
                'tipo_conta': 'DEMO',
                'trade_rv': True,
                'modo_config': 'Valor',
                'stake': 150,
                'stop_win': 0,
                'stop_loss': 0,
            }
            x = Process(target=aguardar_compra, args=(informacoes_conta, tradeEvent, info_trade, contas, buy, buy_multi, monitorStopThread, pendingTrades, aux_mensagemTransmissao,))
            x.start()
            contas[informacoes_conta['email']] = True

            email = informacoes_conta['email']
            chat_id = update.message.chat_id

            context.job_queue.run_repeating(listaDeTransmissao, data=informacoes_conta, chat_id=chat_id, interval=1, first=1)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Configurações salvas com sucesso!",
                                        reply_markup=mainMenu)
            print(f"{showConfigs(context)}")
            return MENU_OPTIONS

        await update.message.reply_text(f"Código validado com sucesso!\n\nAgora, digite a sua senha da IQ OPTION")
        return CADASTRO_SENHA
    else:
        await update.message.reply_text(f"Código incorreto. Por favor tente novamente ou entre em contato com o suporte")
        return CODIGO_BOT 
    # Logica para validação do código pelo BD!
    # ...
    # retorna para o usuário o e-mail que está associoado ao código dele (no BD) para ele fazer login na IQ OPTION e sinaliza que caso queira trocar o e-mail da IQ Option, entre em contato com o suporte

    # Pede a senha dele para entrar na IQ Option
    # await update.message.reply_text(f"")
    # Definindo o estado para a etapa da senha no cadastro
async def menu_stop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('here')
    # Obtendo a escolha do usuário
    user_choice = update.message.text.lower()
    print(user_choice)
    if user_choice == 'parar bot':
        # Pedindo que o usuário forneça o email
        try:
            global contasStopadas
            contas[context.user_data['email']] = False
            contasStopadas.append(context.user_data['email'])
            await update.message.reply_text("Ok, bot parado com sucesso!", reply_markup=ReplyKeyboardRemove())
        except:
             await update.message.reply_text("Seu bot já estava parado, nenhuma alteração foi feita.", reply_markup=ReplyKeyboardRemove())
        # Definindo o estado para a etapa do email no cadastro
        return ConversationHandler.END
    elif user_choice == 'continuar operando':
        await update.message.reply_text("Ok, nenhuma alteração foi feita.", reply_markup=ReplyKeyboardRemove())
    elif "_czbotstop" in user_choice:
        try:
            motivo = user_choice.split("_czbotstop ")[1]
        except:
            motivo = 'Admin do canal parou o bot manualmente.'
        stopBot(motivo=motivo)
        await update.message.reply_text('Bot encerrado para todos os usuários com sucesso.')
    else:
        # Opção inválida, reinicie a conversa
        #await update.message.reply_text("Opção inválida. Por favor, selecione uma opção válida.")
        pass
    # Reiniciando a conversa
    return ConversationHandler.END   

def fazer_login(email, senha, pending_login_accs):
    print(f"INSIDE LOGIN PROCESS - Tentativa de login: {email} {senha}")
    acc = IQ_Option(email, senha)
    try:
        acc_check, acc_reason = acc.connect()
        print(pending_login_accs)
        pending_login_accs[email] = (acc_check, acc_reason)
        print(f"INSIDE LOGIN PROCESS - Tentativa finalizada: {email} {acc_check} {acc_reason}")
    except:
        pass

# Função para lidar com o fornecimento da senha
async def cadastro_senha_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    
    # Obtendo a senha do usuário
    senha = update.message.text

    # Salvando a senha no contexto para uso posterior, se necessário
    context.user_data['senha'] = senha

    # Realizando qualquer ação necessária com as informações coletadas
    # ...
    print(context.user_data['email'], context.user_data['senha'])
    #api = IQ_Option(context.user_data['email'], context.user_data['senha'])
    manager = Manager()
    pending_login_accs = manager.dict()
    login_p = Process(target=fazer_login, args=(context.user_data['email'], context.user_data['senha'],pending_login_accs,))
    login_p.start()
    result = False
    tries = 0
    while not(result):
        try:
            bot_check, bot_reason = pending_login_accs[context.user_data['email']]
            result = True
        except:
            tries +=1
            if tries>=5:
                bot_reason = "Timeout on IQ Option login reached"
                bot_check = False
        time.sleep(1)
    login_p.terminate()
    print(bot_check, bot_reason)
    
    if bot_check:
        context.user_data['api'] = IQ_Option(context.user_data['email'], context.user_data['senha'])
        keyboard = [
            [KeyboardButton("REAL")],
            [KeyboardButton("DEMO")],
        ]
        menuRealDemo = ReplyKeyboardMarkup(keyboard)

        await update.message.reply_text(f"Login efetuado com sucesso! \n\nEscolha em qual conta o bot irá operar: ",
                                        reply_markup=menuRealDemo)
        return REAL_DEMO
    # Informando ao usuário que o processo foi concluído
    else:
        if 'invalid_credentials' in bot_reason:
            await update.message.reply_text(f"Senha incorreta.")
        else:
            await update.message.reply_text(f"Erro ao realizar login. {bot_reason}")
        # Reiniciando a conversa
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Digite novamente a senha associada ao e-mail {context.user_data['email']} para tentar efetuar o login novamente")
        return CADASTRO_SENHA


async def real_demo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """print("real/demo")
    query = update.callback_query
    await query.answer()
    print(query)"""
    # tipo_conta = query.data

    tipo_conta = update.message.text.lower()

    if 'demo' in tipo_conta:
        context.user_data['tipo_conta'] = 'DEMO'
        #context.user_data['api'].change_balance('PRACTICE')
        
        #await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Você escolheu operar na conta DEMO.\nSaldo atual: R${context.user_data['api'].get_balance()}", reply_markup = ReplyKeyboardRemove())
    elif 'real' in tipo_conta:
        context.user_data['tipo_conta'] = 'REAL'
        #context.user_data['api'].change_balance('REAL')
        #print(context.user_data['api'].get_balance())
        #await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Você escolheu operar na conta REAL.\nSaldo atual: R${context.user_data['api'].get_balance()}", reply_markup = ReplyKeyboardRemove())
    else:
        context.user_data['tipo_conta'] = 'DEMO'
        #context.user_data['api'].change_balance('PRACTICE')
        #print(context.user_data['api'].get_balance())
        #await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Como não entendi sua resposta, o login foi feito na conta DEMO.\nSaldo atual: R${context.user_data['api'].get_balance()}", reply_markup = ReplyKeyboardRemove())
    # context.user_data['banca_inicial'] = context.user_data['api'].get_balance()

    keyboard = [
        [KeyboardButton("Reversão + Retração")],
        [KeyboardButton("Apenas retração")],
    ]

    menuTradeMode = ReplyKeyboardMarkup(keyboard)
    texto_informativo_trade_mode = """Na WINNER ZONE, utilizamos 2 tipos de entradas:
   - Retração (entrada assim que atingir a taxa, para a mesma vela)
   - Reversão (entrada para a próxima vela)

Para determinar qual entrada fazer, utilizamos o tempo restante de vela quando a taxa é atingida.

Caso a taxa seja atingida 1 minuto e meio antes do final da vela, utilizamos a reversão (próxima vela). Ex: 8h23m46s, 9h59m10s
Caso contrário, efetuamos a trade na mesma vela.

Qual das opções abaixo deseja que o seu bot efetue as entradas?

_Se ainda tiver dúvidas, acesse: link youtube_
"""
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f"{texto_informativo_trade_mode}",
                                   reply_markup=menuTradeMode, parse_mode='Markdown')
    return TRADE_MODE

async def trade_mode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """print("real/demo")
    query = update.callback_query
    await query.answer()
    print(query)"""
    # tipo_conta = query.data

    modo_trade = update.message.text.lower()

    if 'reversão' in modo_trade:
        context.user_data['trade_rv'] = True
        #context.user_data['api'].change_balance('PRACTICE')
        
        #await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Você escolheu operar na conta DEMO.\nSaldo atual: R${context.user_data['api'].get_balance()}", reply_markup = ReplyKeyboardRemove())
    else:
        context.user_data['trade_rv'] = False

    keyboard = [
        [KeyboardButton("VALOR FIXO (R$)")],
        [KeyboardButton("PERCENTUAL (%)")],
    ]

    menuFixoPercentual = ReplyKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f"Como serão feitas a configuração das entradas?\n\n_(Essa informação será utilizada para estipular stake, stopWin e stopLoss)_",
                                   reply_markup=menuFixoPercentual, parse_mode='Markdown')
    return FIXO_PERCENTUAL


async def fixo_percentual_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''query = update.callback_query
    await query.answer()
    print(query)
    modo_escolhido = query.data'''

    modo_escolhido = update.message.text.lower()

    if 'valor' in modo_escolhido:
        context.user_data['modo_config'] = 'Valor'
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Digite o VALOR desejado para as ENTRADAS (valor máximo 10% da sua banca)\n\n_ex: 10.5, 150, 250, 1000_",
                                       parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())
    elif 'percentual' in modo_escolhido or 'porcento' in modo_escolhido or 'porcentagem' in modo_escolhido:
        context.user_data['modo_config'] = 'Percentual'
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Digite a PORCENTAGEM desejada para as ENTRADAS (valor máximo 10%)\n\n_ex: 1, 1.5, 2, 2.5_",
                                       parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())

    return CONFIG_STAKE


async def stake_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stake = float(str(update.message.text).lower().replace("r$", "").replace("%", "").replace("reais", "").strip())

    print(stake)
    if context.user_data['modo_config'] == 'Valor':
        '''if stake > context.user_data['banca_inicial']/10:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Valor incorreto, por favor, digite um valor menor que 10% sua banca ({context.user_data['banca_inicial']})")
            return CONFIG_STAKE
        else:'''
        context.user_data['stake'] = round(stake, 2)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Digite o VALOR desejado para o STOP WIN\n_Caso não queira, digite 0._",
                                       parse_mode='Markdown')

    elif context.user_data['modo_config'] == 'Percentual':
        if stake > 100 or stake <= 0:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=f"Porcentagem incorreta!\nPor favor, digite uma porcentagem entre 1 e 10")
            return CONFIG_STAKE
        else:
            context.user_data['stake'] = round(stake, 2)
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=f"Digite o PERCENTUAL desejado para o STOP WIN\n_Caso não queira, digite 0._",
                                           parse_mode='Markdown')

    return STOP_WIN


async def stop_win_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stopWin = float(str(update.message.text).lower().replace("r$", "").replace("%", "").replace("reais", "").strip())
    if context.user_data['modo_config'] == 'Valor':
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Digite o VALOR desejado para o STOP LOSS\n_Caso não queira, digite 0._",
                                       parse_mode='Markdown')
    elif context.user_data['modo_config'] == 'Percentual':
        # context.user_data['stop_win'] = round(context.user_data['banca_inicial']*stopWin/100,2) if stopWin != 0 else None
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Digite o PERCENTUAL desejado para o STOP LOSS\n_Caso não queira, digite 0._",
                                       parse_mode='Markdown')
    context.user_data['stop_win'] = stopWin
    return STOP_LOSS


async def stop_loss_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stopLoss = float(str(update.message.text).lower().replace("r$", "").replace("%", "").replace("reais", "").strip())

    '''if context.user_data['modo_config'] == 'Valor':
        context.user_data['stop_loss'] = stopLoss
    elif context.user_data['modo_config'] == 'Percentual':
        context.user_data['stop_loss'] = round(context.user_data['banca_inicial']*stopLoss/100,2) if stopLoss != 0 else None'''

    context.user_data['stop_loss'] = stopLoss
    keyboard = [
        [KeyboardButton("CONFIRMAR ✅")],
        [KeyboardButton("EDITAR ↩️")],
    ]

    menuConfirmacao = ReplyKeyboardMarkup(keyboard)
    print(context.user_data['email'], context.user_data['modo_config'])
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f"*CONFIGURAÇÕES:*\n\n {showConfigs(context)}", reply_markup=menuConfirmacao,
                                   parse_mode='Markdown')

    return CONFIRMACAO_CONFIG


async def confirmacao_config_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    confirmacao = update.message.text.lower()
    if 'confirmar' in confirmacao or 'sim' in confirmacao:
        context.user_data['trades'] = []
        informacoes_conta = {
            'email': context.user_data['email'],
            'senha': context.user_data['senha'],
            'tipo_conta': context.user_data['tipo_conta'],
            'trade_rv': context.user_data['trade_rv'],
            'modo_config': context.user_data['modo_config'],
            'stake': context.user_data['stake'],
            'stop_win': context.user_data['stop_win'],
            'stop_loss': context.user_data['stop_loss'],
        }
        x = Process(target=aguardar_compra, args=(informacoes_conta, tradeEvent, info_trade, contas, buy, buy_multi, monitorStopThread, pendingTrades, aux_mensagemTransmissao,))
        x.start()
        contas[informacoes_conta['email']] = True

        email = informacoes_conta['email']
        chat_id = update.message.chat_id

        context.job_queue.run_repeating(listaDeTransmissao, data=informacoes_conta, chat_id=chat_id, interval=1, first=1)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Configurações salvas com sucesso!",
                                       reply_markup=ReplyKeyboardRemove())
        print(f"{showConfigs(context)}")
        return ConversationHandler.END
    else:
        keyboard = [
            [KeyboardButton("REAL")],
            [KeyboardButton("DEMO")],
        ]
        menuRealDemo = ReplyKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Ok, redirecionando para o menu de configurações...",
                                       reply_markup=menuRealDemo)
        time.sleep(0.5)
        return REAL_DEMO

def monitorStopThread(conta, informacoes_conta, sinal_stop, pendingTrades, aux_mensagemTransmissao):
    print(f"Monitorando stops {informacoes_conta['email']} {conta.get_balance()}\nStop WIN: {informacoes_conta['stop_win']}\nStop LOSS: {informacoes_conta['stop_loss']}")
    while True:
        if informacoes_conta['stop_win'] == 99999 or informacoes_conta['stop_loss'] == 0:
            print(f"No stops configured in {informacoes_conta['email']}")
            break
        time.sleep(5)
        tradesPendentes_atualizadas = pendingTrades.value
        if tradesPendentes_atualizadas > 0:
            #print(f"TRADES PENDENTES: {tradesPendentes_atualizadas}") 
            continue
        
        banca_atual = conta.get_balance()
        if int(datetime.now().strftime("%M"))%5==0:
            print(f"Conta: {informacoes_conta['email']}\nBanca Atual: {banca_atual}\nStop Win: {informacoes_conta['stop_win']}\nStop Loss: {informacoes_conta['stop_loss']}")

        if banca_atual>=informacoes_conta['stop_win']:
            print(f"Stop win: {informacoes_conta['email']}")
            sinal_stop.set()

            print("STOP THREAD: MENSAGEM CHEGOU \n   Antes: {}".format(aux_mensagemTransmissao.value))
            mensagemStop = f"🔐 MENSAGEM PRIVADA 🔐\n\n{informacoes_conta['email']}: Stop Win Atingido!"
            aux_mensagemTransmissao.value = aux_mensagemTransmissao.value + ["🔐 MENSAGEM PRIVADA 🔐",mensagemStop]
            print("   Depois: {}".format(aux_mensagemTransmissao.value))
            break
        if banca_atual<=informacoes_conta['stop_loss']:
            print(f"Stop loss: {informacoes_conta['email']}")
            sinal_stop.set()
            mensagemStop = f"🔐 MENSAGEM PRIVADA 🔐\n\n{informacoes_conta['email']}: Stop Loss Atingido!"
            aux_mensagemTransmissao.value = aux_mensagemTransmissao.value + ["🔐 MENSAGEM PRIVADA 🔐",mensagemStop]
            break
        time.sleep(60)


def aguardar_compra(informacoes_conta, sinal_compra, info_compra, contas, func_compra, func_compra_multi, func_monitorStops, pendingTrades, aux_mensagemTransmissao):
    acc_api = IQ_Option(informacoes_conta['email'], informacoes_conta['senha'])
    check, reason = acc_api.connect()
    acc_trades = []
    if check:
        acc_api.change_balance('REAL') if informacoes_conta['tipo_conta'] == 'REAL' else acc_api.change_balance(
            'PRACTICE')
        acc_banca_inicial = acc_api.get_balance()

        acc_stake = informacoes_conta['stake'] if informacoes_conta['modo_config'] == 'Valor' else round(acc_banca_inicial * informacoes_conta['stake'] / 100, 2)
        
        if informacoes_conta['stop_win'] != 0:
            informacoes_conta['stop_win'] = (acc_banca_inicial + informacoes_conta['stop_win'] if informacoes_conta['modo_config'] == 'Valor' else acc_banca_inicial + round(acc_banca_inicial * informacoes_conta['stop_win'] / 100, 2))
        else:
            informacoes_conta['stop_win'] = 99999

        if informacoes_conta['stop_loss'] != 0:
            informacoes_conta['stop_loss'] = acc_banca_inicial - informacoes_conta['stop_loss'] if informacoes_conta['modo_config'] == 'Valor' else acc_banca_inicial - round(acc_banca_inicial * informacoes_conta['stop_loss'] / 100, 2)

        stop_signal = Event()   
        stop_thread = threading.Thread(target=func_monitorStops, args=(acc_api,informacoes_conta, stop_signal, pendingTrades,aux_mensagemTransmissao,))
        stop_thread_is_running = False
        log_m = f"""CONTA AGUARDANDO TRADES
Conta: {informacoes_conta['email']}
Stake: {acc_stake}
RT+RV: {informacoes_conta['trade_rv']}
Stop Win: {informacoes_conta['stop_win']}
Stop Loss: {informacoes_conta['stop_loss']}
"""
        print(log_m)
        while True:
            if not (acc_api.check_connect()):
                acc_api.connect()

            sinal_compra.wait()

            

            if not(contas[informacoes_conta['email']]) or stop_signal.is_set():
                break
            infos_compra_atualizadas = info_compra.value
            print(f"{informacoes_conta['email']} {informacoes_conta['trade_rv']} {infos_compra_atualizadas['type']}")

            if infos_compra_atualizadas['type'] == 'immediate' or (informacoes_conta['trade_rv'] == False and infos_compra_atualizadas['type'] == 'rv-immediate'):
                if not (f"{infos_compra_atualizadas['pair']} {infos_compra_atualizadas['direction']}" in acc_trades):
                    print(f"{informacoes_conta['email']} TRADE RT - {infos_compra_atualizadas['pair']} {infos_compra_atualizadas['direction']}")
                    func_compra(acc_api, acc_stake, infos_compra_atualizadas['pair'], infos_compra_atualizadas['direction'])
                    acc_trades.append(f"{infos_compra_atualizadas['pair']} {infos_compra_atualizadas['direction']}")
                    
            elif informacoes_conta['trade_rv'] == True and infos_compra_atualizadas['type'] != 'rv-immediate':
                    for i, trade_pair in enumerate(infos_compra_atualizadas['pair']):
                        if f"{trade_pair} {infos_compra_atualizadas['direction'][i]}" in acc_trades:
                            infos_compra_atualizadas['type'].pop(i)
                            infos_compra_atualizadas['pair'].pop(i)
                            infos_compra_atualizadas['direction'].pop(i)

                    print(f"{informacoes_conta['email']} TRADE RV - {infos_compra_atualizadas['pair']} {infos_compra_atualizadas['direction']}")
                    func_compra_multi(acc_api, acc_stake, infos_compra_atualizadas['pair'], infos_compra_atualizadas['direction'])
                    acc_trades.append(' '.join([f'{pair} {infos_compra_atualizadas["direction"][i]}' for i, pair in enumerate(infos_compra_atualizadas['pair'])]))
                
            if not(stop_thread_is_running):
                stop_thread.start()
                stop_thread_is_running = True
            time.sleep(0.1)

        print(f"Stop monitoring pairs: {informacoes_conta['email']}")

def buy(conta, stake, pair, direction):
    """Does the trade and add the trade informations on log

    Args:
        pair (str): Witch pair its going to do the trade action
        stake (float): How many money will be traded
        direction (string): 'put' or 'call' to set the direction
        time (int): Period of candle
        currentPrice (float): Pair price at the moment just to avoid consulting it againg (it would take some time to do it)
    """
    # TEM QUE TER O TRATAMENTO DO TRADETIME
    # TEM QUE TER O TRATAMENTO DO TRADETIME
    # TEM QUE TER O TRATAMENTO DO TRADETIME
    # TEM QUE TER O TRATAMENTO DO TRADETIME

    direction = direction.casefold()

    buy_api = conta
    print(pair, stake, direction, 5)
    completeHour = datetime.fromtimestamp(buy_api.get_server_timestamp()).strftime("%H:%M:%S")
    minutes = int(completeHour.split(":")[1][-1]) % 5
    seconds = math.ceil(float(completeHour.split(":")[2]))

    time_to_buy = 5 - minutes if seconds <= 30 else 5 - minutes - 1
    time_to_buy = 5 if time_to_buy == 0 else time_to_buy  # reset to the last option if the option is 0 (0min<30sec -> can't trade)

    id = buy_api.buy_multi([stake], [pair], [direction], [time_to_buy])
    
    if id[0] != None:
        # __updateLog(f"TRADE -  {pair} {direction} at {currentPrice}")
        # tradesToCheck.append((id, pair, direction, tradeTime, "immediate"))
        # pendingTrades += 1
        print(f"BINARY TRADE -  {pair} {direction}")
        # trades.append(f'{pair} {direction}')
    else:
        # if not (f"ERROR on digital trade {pair} {direction}" in logText):
        # __updateLog(f"ERROR on digital trade {pair} {direction} at {currentPrice} - {id}, trying binary")
        print(f"ERROR on binary trade {pair} {direction} - {id}, trying digital")
        check, id = buy_api.buy_digital_spot_v2(pair, stake, direction, 5)
        if check:
            '''__updateLog(f"TRADE -  {pair} {direction} at {currentPrice}")
            tradesToCheck.append((id, pair, direction, tradeTime, "immediate"))
            pendingTrades += 1'''

            print(f"DIGITAL TRADE -  {pair} {direction}")
        #    trades.append(f'{pair} {direction}')
        else:
            # if not (f"ERROR on binary trade {pair} {direction}" in logText):
            # __updateLog(f"ERROR on binary trade {pair} {direction} at {currentPrice} - {id}")
            print(f"ERROR on BINARY AND DIGITAL {pair} {direction} - {id}")
        #        trades.append(f'{pair} {direction} error')


def buy_multi(conta, stake, pairs, directions):
    print(pairs, directions)
    tamanho_compra = len(pairs)
    ids = conta.buy_multi(
        [stake] * tamanho_compra,
        pairs,
        directions,
        [5] * tamanho_compra
    )
    noneIndexes = [i for i, id in enumerate(ids) if id is None]
    try:
        for i in noneIndexes:
            check, id = conta.buy_digital_spot_v2(
                pairs[i],
                stake,
                directions[i],
                5
            )
            if check:
                ids[i] = id
    except:
        pass
    print(ids)


# Responses
def handle_response(text: str) -> str:
    processed_text = text.lower()

    """"'if 'hello' in processed_text:
        return 'hello boy'
    if 'are you ok' in processed_text:
        return 'of course'
    if 'taxas vip' in processed_text and len(taxas) != 0:
        return 'Taxas computadas'"""


async def handle_message(update: Update, context=ContextTypes.DEFAULT_TYPE):
    global taxas, linhas_taxas
    try:
        message_type: str = update.message.chat.type
        text: str = update.message.text
        print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')
    except:
        message_type: str = update.channel_post.chat.type
        text: str = update.channel_post.text
        print(f'User ({update.channel_post.chat.id}) in {message_type}: "{text}"')
    

    if message_type == 'group' or message_type == 'channel':
        if botUsername in text:
            new_text: str = text.replace(botUsername, '').strip()
            response: str = handle_response(new_text)
        else:
            if "TAXAS VIP" in text:
                linhas = text.split("\n")
                linhas_taxas = [linha for linha in linhas if linha.startswith("M5")]

                
                ativos = list(set([sinal.split(" ")[1].strip() for sinal in linhas_taxas]))
                ativos.sort()

                qtSinais = 0
                for ativo in ativos:
                    taxaAtivoAtual = [taxa for taxa in linhas_taxas if ativo in taxa]
                    taxas[ativo] = {"PUT": None, "CALL": None}
                    try:
                        taxas[ativo]["PUT"] = [
                            "".join(sign).split(f" {ativo}")[1].replace("PUT", "").replace("\n", "").strip()
                            for sign in taxaAtivoAtual if "PUT" in sign][0]
                    except:
                        pass
                    try:
                        taxas[ativo]["CALL"] = [
                            "".join(sign).split(f" {ativo}")[1].replace("CALL", "").replace("\n", "").strip()
                            for sign in taxaAtivoAtual if "CALL" in sign][0]
                    except:
                        pass

                    if taxas[ativo]["PUT"] != None:
                        qtSinais += 1

                    if taxas[ativo]["CALL"] != None:
                        qtSinais += 1

                response: str = handle_response(text)
                startBot()
                mensagemListaTransmissao("Taxas computadas")
                

            else:
                return
            
          


async def error(update: Update, context=ContextTypes.DEFAULT_TYPE):
    print(f'Update: {update} caused error {context.error}')


def mensagemListaTransmissao(mensagem):
    global aux_mensagemTransmissao, lock_msgTransmissao
    try:
        lock_msgTransmissao.acquire()
        print("MENSAGEM CHEGOU \n   Antes: {}".format(aux_mensagemTransmissao.value))
        titulo = mensagem.split('\n')[0]
        aux_mensagemTransmissao.value = aux_mensagemTransmissao.value + [(titulo, mensagem)]
        print("   Depois: {}".format(aux_mensagemTransmissao.value))
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")
    finally:
        lock_msgTransmissao.release()

def monitorarListaTransmissao(aux_mensagemTransmissao, lock_msgTransmissao):
    while True:
        time.sleep(10)
        global mensagemTransmissao, stopListaTransmissao
        try:
            lock_msgTransmissao.acquire()
            aux_mensagemTransmissao_atualizado = aux_mensagemTransmissao.value

            if aux_mensagemTransmissao_atualizado != mensagemTransmissao and aux_mensagemTransmissao_atualizado != []:
                mensagemTransmissao = aux_mensagemTransmissao_atualizado
                print(f'Mensagens GLOBAIS: {mensagemTransmissao}')
                aux_mensagemTransmissao.value = []
                #print(f"Overview das trades:\nAgendadas: {scheduledTrades}\nPara checar: {tradesToCheck}")
            #else:
            #    print(f"{__getCurrentTime()} Sem mudanças na mensagem")
        except Exception as e:
            print(f"Erro ao processar mensagem: {e}")
        finally:
            lock_msgTransmissao.release()
            if stopListaTransmissao:
                break

def startBot():
    global thread_pares, thread_agendamentos, thread_transmissao, statusBot
    thread_pares.start()
    thread_agendamentos.start()
    thread_transmissao.start()
    statusBot = True

def stopBot(motivo):
    global stopThreadSignal, stopListaTransmissao, resultados, thread_pares, thread_agendamentos, thread_transmissao, aux_mensagemTransmissao, statusBot
    print("Stopping...")
    stopThreadSignal = True
    time.sleep(1)
    
    if motivo == "Timeout":
        mensagemFinal = f"📝 RESULTADOS TAXAS VIP SEM GALE 📝\n⏱️ {datetime.now(tz).strftime('%d/%m/%Y')}\n\n{resultados}"
    else:
        mensagemFinal = f"📝 RESULTADOS TAXAS VIP SEM GALE 📝\n⏱️ {datetime.now(tz).strftime('%d/%m/%Y')}\n\n{resultados}\n\nMotivo da parada: {motivo}"
    mensagemListaTransmissao(mensagemFinal)

    time.sleep(11)
    stopListaTransmissao = True
    statusBot = False
    sys.exit()

def __getCurrentTime():
    """Gets the current time of IQ Option server to prevent misunderstandings while logging
    bots action
Returns:
    str: IQ Option server time on this format H:M:S"""
    global tz
    time = datetime.fromtimestamp(api.get_server_timestamp(), tz).strftime("%H:%M:%S")
    if "14:30:1" in time:
        __updateResultsCallRow(pair='stop')
        stopBot("Timeout")
    return time

def __updateResultsCallRow(pair='', direction='', message=''):
    global linhas_taxas, resultados
    if pair == 'stop':
        for callRowIndex, call in enumerate(linhas_taxas):
            if len(call.split(" ")) == 4:
                linhas_taxas[callRowIndex] += f" ⏱️"
    else:   
        aux = f"{pair} {direction.upper()}"
        for callRowIndex, call in enumerate(linhas_taxas):
            if aux in call:
                linhas_taxas[callRowIndex] += f" {message}"
    
    resultados = "\n".join(linhas_taxas)

def __monitorScheduledTrades():
    """Does multitrade (BINARY) with every trade scheduled on the next 5min candle, that are stored on the scheduledTrades.

    By Default, is inactive, just waiting for a signal to start pooling. This signal is sent by monitorPairs when it has any trade scheduled, otherwise, it stays waiting for a signal.
    """
    while True:
        global scheduledTrades, stopThreadSignal
        if stopThreadSignal:
            break
        scheduleSign.wait()
        while scheduleSign.is_set():
            if stopThreadSignal:
                scheduledTrades = [[], [], []]
                scheduleSign.clear()
                break
            time.sleep(0.1)
            currentTime = __getCurrentTime()
            hour = int(currentTime.split(":")[0])
            minute = int(currentTime.split(":")[1])
            seconds = int(currentTime.split(":")[2])
            if (minute+1) % 5 == 0 and seconds == 59:

                if minute == 59:
                    hour += 1
                    minute = 0
                else:
                    minute+=1

                scheduleTradeTime = f"{hour}:{str(minute).zfill(2)}:00"
                print(scheduledTrades)
                info_trade.value = {'type': 'scheduled', 'pair': scheduledTrades[0], 'direction': scheduledTrades[1]}
                tradeEvent.set()

                scheduledTradesLog = "\n".join(
                    [f'   - {pair} {scheduledTrades[1][i].upper()}' for i, pair in enumerate(scheduledTrades[0])])

                mensagem = f"🎯 TRADE(S) REALIZADA(S) - REVERSÃO M5 🎯\n📊 Transações: \n{scheduledTradesLog}\n⏱️ Horário: {scheduleTradeTime}"
                mensagemListaTransmissao(mensagem)
                time.sleep(0.2)
                tradeEvent.clear()

                aux_list = list(zip(scheduledTrades[0],  # PAIRS
                                    [scheduleTradeTime] * len(scheduledTrades[1]),
                                    scheduledTrades[2],
                                    scheduledTrades[1],  # DIRECTIONS
                                    ["scheduled"] * len(scheduledTrades[1])
                                    )
                                )
                # (checkedPair, tradeTime, tradePrice, tradeDirection, tradeType)
                tradesToCheck.extend(aux_list)
                pendingTrades.value += len(scheduledTrades[1])
                
                time.sleep(1)
                scheduledTrades = [[], [], []]
                scheduleSign.clear()


def monitorPairs():
    global api
    
    startTime = __getCurrentTime()
    print(f"{startTime}: Monitoring pairs...")
    while True:
        global stopThreadSignal
        if stopThreadSignal:
                break
        time.sleep(0.1)
        if len(taxas) == 0:
            continue
        for monitored_pair in taxas:
            if len(tradesToCheck) != 0:
                currentTime = __getCurrentTime()
                for tradeIndex, (checkedPair, tradeTime, tradePrice, tradeDirection, tradeType) in enumerate(
                        tradesToCheck):
                    if checkedPair == monitored_pair:
                        # 11:50
                        # deltaTFiveMinutes = ((5 - int(tradeTime.split(":")[1][-1])%5)*60)-int(tradeTime.split(":")[2])+3
                        deltaTCurrentTime = (datetime.strptime(currentTime, "%H:%M:%S") - datetime.strptime(tradeTime,
                                                                                                            "%H:%M:%S")).total_seconds()

                        if deltaTCurrentTime >= 305:

                            lastCandle = api.get_candles(checkedPair, 300, 2, time.time())

                            lastCandleCloseValue = lastCandle[0]['close']
                            if not("immediate" in tradeType):
                                tradePrice = lastCandle[0]['open']

                            print(f"Checando {checkedPair}...")
                            print(lastCandle)
                            print("Trade em: {}\nValor atual: {}".format(tradePrice, lastCandleCloseValue))

                            if lastCandleCloseValue < tradePrice:
                                # down
                                print("Abaixou")
                                if "immediate" in tradeType:
                                    result = "WIN RT" if tradeDirection == 'put' else "HIT RT"
                                else:
                                    result = "WIN RV" if tradeDirection == 'put' else "HIT RV"

                            elif lastCandleCloseValue > tradePrice:
                                # up
                                print("Aumentou")
                                if "immediate" in tradeType:
                                    result = "WIN RT" if tradeDirection == 'call' else "HIT RT"
                                else:
                                    result = "WIN RV" if tradeDirection == 'call' else "HIT RV"

                                # print("Win") if tradeDirection == 'call' else print("Lose")
                            else:
                                # draw
                                print("Igual")
                                if "immediate" in tradeType:
                                    result = "DOJI RT"
                                else:
                                    result = "DOJI RV"

                            print(f"Resultado: {result}")
                            result = (f"✅ {':'.join(tradeTime.split(':')[0:2])} {result}" if "WIN" in result 
                                        else f"❌ {':'.join(tradeTime.split(':')[0:2])} {result}" if "HIT" in result
                                        else f"⚪ {':'.join(tradeTime.split(':')[0:2])} {result}"
                                        )
                            result = result+"*" if tradeType == 'rv-immediate' else result #Especial trade identifier
                            tradesToCheck.pop(tradeIndex)
                            tradeDirectionMessage = "🔴 PUT" if tradeDirection == 'put' else "🟢 CALL"
                            menssagemResultado = f"🎯 RESULTADO DA TRADE 🎯\n\n📊 Ativo: {monitored_pair} \n📍 Direção: {tradeDirectionMessage}\n📝 Resultado: {result}"
                            mensagemListaTransmissao(menssagemResultado)
                            __updateResultsCallRow(checkedPair, tradeDirection, result)
                            pendingTrades.value -= 1
                            

            if not (api.check_connect()):
                print("tentando reconexão")
                api.connect()
            candle = api.get_candles(monitored_pair, 300, 1, time.time())  # current price
            upper_limit, bottom_limit = None, None
            try:
                upper_limit = float(taxas[monitored_pair]["PUT"])
            except:
                pass
            try:
                bottom_limit = float(taxas[monitored_pair]["CALL"])
            except:
                pass
            try:
                current_price = candle[0]["close"]
            except:
                print("Couldn't find {} candles".format(monitored_pair), end='\r')
                time.sleep(2)
                continue
            currentTime = __getCurrentTime()
            minute = int(currentTime[-4])
            seconds = int(currentTime[-2:])
            
            if minute%5==0 and seconds <=5:
                print(f"{currentTime}: Monitoring... {monitored_pair} {current_price}")
                
            if ((upper_limit != None and current_price < upper_limit) and (
                    bottom_limit != None and current_price > bottom_limit)):
                continue

            elif upper_limit != None and current_price >= upper_limit:

                if (f"{monitored_pair} put") not in trades:
                    print(f"{currentTime}: {monitored_pair} at {current_price} touched the upper limit ({upper_limit})")
                    if (minute % 5 == 0) and (seconds <= 5) or ((datetime.strptime(currentTime,"%H:%M:%S") - datetime.strptime(startTime, '%H:%M:%S')).total_seconds() < 10):
                        taxas[monitored_pair]["PUT"] = None
                        if (minute % 5 == 0) and (seconds <= 10):
                            mensagem = f"🚨 TRADE CANCELADA 🚨\n\n📊 Ativo: {monitored_pair}\n📍 Direção: 🔴 PUT\n❓ Motivo: Taxa atingida na abertura da vela\n⏱️ Horário: {currentTime}\n💰 Preço atual: {current_price}"
                        else:
                            mensagem = f"🚨 TRADE CANCELADA 🚨\n\n📊 Ativo: {monitored_pair}\n📍 Direção: 🔴 PUT\n❓ Motivo: Taxa atingida no momento de início do bot\n⏱️ Horário: {currentTime}\n💰 Preço atual: {current_price}"
                        mensagemListaTransmissao(mensagem)
                        __updateResultsCallRow(monitored_pair, 'PUT', f"cancelada")
                        continue

                    elif (minute == 9 or minute == 4) or (
                            (minute == 8 and seconds >= 35) or (minute == 3 and seconds >= 35)):
                        
                        if not((minute == 9 or minute == 4) and seconds >= 30):
                            info_trade.value = {'type': 'rv-immediate', 'pair': monitored_pair, 'direction': 'put'}
                            tradeEvent.set()
                            time.sleep(0.1)
                            tradeEvent.clear()
                            aux_hour = int(currentTime.split(":")[0])
                            aux_minutes = int(currentTime.split(":")[1])
                            aux_minutes = aux_minutes - aux_minutes % 5
                            tradesToCheck.append((monitored_pair, f"{aux_hour}:{aux_minutes}:00", current_price, 'put', 'rv-immediate'))
                        else:
                            mensagem = f"🚨 TRADE CANCELADA 🚨\n\n📊 Ativo: {monitored_pair}\n📍 Direção: 🔴 PUT\n❓ Motivo: Taxa atingida no fechamento da vela\n⏱️ Horário: {currentTime}\n💰 Preço atual: {current_price}"
                            __updateResultsCallRow(monitored_pair, 'PUT', f"cancelada*")
                            mensagemListaTransmissao(mensagem)

                        scheduledTrades[0].append(monitored_pair)
                        scheduledTrades[1].append("put")
                        scheduledTrades[2].append(current_price)

                        trades.append(f"{monitored_pair} put")
                        if not (scheduleSign.is_set()):
                            scheduleSign.set()
                        mensagem = f"⏱️ TRADE AGENDADA - REVERSÃO M5 ⏱️\n\n📊 Ativo: {monitored_pair}\n📍 Direção: 🔴 PUT\n⏱️ Horário: {currentTime}\n💰 Preço atual: {current_price}"

                    else:
                        info_trade.value = {'type': 'immediate', 'pair': monitored_pair, 'direction': 'put'}
                        tradeEvent.set()
                        time.sleep(0.1)
                        tradeEvent.clear()
                        info_trade.value = {'type': '', 'pair': '', 'direction': ''}
                        trades.append(f"{monitored_pair} put")

                        aux_hour = int(currentTime.split(":")[0])
                        aux_minutes = int(currentTime.split(":")[1])
                        aux_minutes = aux_minutes - aux_minutes % 5
                        tradesToCheck.append((monitored_pair, f"{aux_hour}:{aux_minutes}:00", current_price, 'put', 'immediate'))

                        mensagem = f"🎯 TRADE REALIZADA - RETRAÇÃO M5 🎯\n\n📊 Ativo: {monitored_pair}\n📍 Direção: 🔴 PUT\n⏱️ Horário: {currentTime}\n💰 Preço atual: {current_price}"
                        pendingTrades.value += 1
                        

                    mensagemListaTransmissao(mensagem)

            elif bottom_limit != None and current_price <= bottom_limit:

                if (f"{monitored_pair} call") not in trades:
                    print(f"{currentTime}: {monitored_pair} at {current_price} touched the bottom limit ({bottom_limit})")
                    if (minute % 5 == 0) and (seconds <= 5) or ((datetime.strptime(currentTime,
                                                                                   "%H:%M:%S") - datetime.strptime(
                            startTime, '%H:%M:%S')).total_seconds() < 10):
                        taxas[monitored_pair]["CALL"] = None
                        if (minute % 5 == 0) and (seconds <= 10):
                            mensagem = f"🚨 TRADE CANCELADA 🚨\n\n📊 Ativo: {monitored_pair}\n📍 Direção: 🟢 CALL\n❓ Motivo: Taxa atingida na abertura da vela\n⏱️ Horário: {currentTime}\n💰 Preço atual: {current_price}"
                        else:
                            mensagem = f"🚨 TRADE CANCELADA 🚨\n\n📊 Ativo: {monitored_pair}\n📍 Direção: 🟢 CALL\n❓ Motivo: Taxa atingida no momento de início do bot\n⏱️ Horário: {currentTime}\n💰 Preço atual: {current_price}"
                        mensagemListaTransmissao(mensagem)
                        __updateResultsCallRow(monitored_pair, 'CALL', f"cancelada")
                        continue

                    elif (minute == 9 or minute == 4) or (
                            (minute == 8 and seconds >= 35) or (minute == 3 and seconds >= 35)):   
                        
                        if not((minute == 9 or minute == 4) and seconds >= 30):
                            info_trade.value = {'type': 'rv-immediate', 'pair': monitored_pair, 'direction': 'call'}
                            tradeEvent.set()
                            time.sleep(0.1)
                            tradeEvent.clear()
                            aux_hour = int(currentTime.split(":")[0])
                            aux_minutes = int(currentTime.split(":")[1])
                            aux_minutes = aux_minutes - aux_minutes % 5
                            tradesToCheck.append((monitored_pair, f"{aux_hour}:{aux_minutes}:00", current_price, 'call', 'rv-immediate'))
                        else:
                            mensagem = f"🚨 TRADE CANCELADA 🚨\n\n📊 Ativo: {monitored_pair}\n📍 Direção: 🟢 CALL\n❓ Motivo: Taxa atingida no fechamento da vela\n⏱️ Horário: {currentTime}\n💰 Preço atual: {current_price}"
                            __updateResultsCallRow(monitored_pair, 'CALL', f"cancelada*")
                            mensagemListaTransmissao(mensagem)

                        scheduledTrades[0].append(monitored_pair)
                        scheduledTrades[1].append("call")
                        scheduledTrades[2].append(current_price)
                        trades.append(f"{monitored_pair} call")

                        if not (scheduleSign.is_set()):
                            scheduleSign.set()
                        mensagem = f"⏱️ TRADE AGENDADA - REVERSÃO M5 ⏱️\n\n📊 Ativo: {monitored_pair}\n📍 Direção: 🟢 CALL\n⏱️ Horário: {currentTime}\n💰 Preço atual: {current_price}"

                    else:
                        info_trade.value = {'type': 'immediate', 'pair': monitored_pair, 'direction': 'call'}
                        tradeEvent.set()
                        mensagem = f"🎯 TRADE REALIZADA - RETRAÇÃO M5 🎯\n\n📊 Ativo: {monitored_pair}\n📍 Direção: 🟢 CALL\n⏱️ Horário: {currentTime}\n💰 Preço atual: {current_price}"
                        time.sleep(0.1)
                        tradeEvent.clear()
                        trades.append(f"{monitored_pair} call")

                        aux_hour = int(currentTime.split(":")[0])
                        aux_minutes = int(currentTime.split(":")[1])
                        aux_minutes = aux_minutes - aux_minutes % 5
                        aux_minutes = aux_minutes+1 if aux_minutes==59 else aux_minutes

                        tradesToCheck.append(
                            (monitored_pair, f"{aux_hour}:{aux_minutes}:00", current_price, 'call', 'immediate'))
                        info_trade.value = {'type': '', 'pair': '', 'direction': ''}
                        pendingTrades.value += 1
                        

                    mensagemListaTransmissao(mensagem)


if __name__ == '__main__':
    set_start_method("spawn")
    linhas_taxas = []
    taxas = {}
    statusBot = False

    resultados = ''
    resultados_RT = ''
    aux_mensagemTransmissao = []
    mensagemTransmissao = []
    mensagensEnviadas = []
    contasStopadas = []

    trades = []

    stopThreadSignal = False
    stopListaTransmissao = False
    scheduledTrades = [[], [], []]
    scheduleSign = threading.Event()

    tradesToCheck = []

    with Manager() as manager:
        info_trade = manager.Value(typecode='dict', value={'type': '', 'pair': '', 'direction': ''})
        pendingTrades = manager.Value(typecode='int', value=0)
        aux_mensagemTransmissao = manager.Value(typecode='list', value=[])
        lock_msgTransmissao = Lock()

        thread_pares = threading.Thread(target=monitorPairs)
        thread_agendamentos = threading.Thread(target=__monitorScheduledTrades)
        thread_transmissao = threading.Thread(target=monitorarListaTransmissao, args=(aux_mensagemTransmissao, lock_msgTransmissao))
        
        contas = manager.dict()
        
        tradeEvent = Event()

        
        print("Starting... teste")
        num_cores = os.cpu_count()
        #print(f"Número de núcleos da CPU: {num_cores}")
        api = IQ_Option('winnerzonebot@gmail.com', 'WinnerzoneBOT1!')
        check, reason = api.connect()
        print('Bot connected!')
        print(api.get_balance())
        check, reason = None, None
        app = Application.builder().token(token).build()
        '''job_queue = app.job_queue

        job_10sec = job_queue.run_repeating(sendMessageForAll, interval=10, first=10)'''

        # Comands
        conv_handler_cadastro = ConversationHandler(
            entry_points=[
                MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, menu_options_handler)],
            states={
                CODIGO_BOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, codigo_bot_handler)],
                CADASTRO_SENHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, cadastro_senha_handler)],
                REAL_DEMO: [MessageHandler(filters.TEXT & ~filters.COMMAND, real_demo_handler)],
                FIXO_PERCENTUAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, fixo_percentual_handler)],
                TRADE_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, trade_mode_handler)],
                CONFIG_STAKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, stake_handler)],
                STOP_WIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, stop_win_handler)],
                STOP_LOSS: [MessageHandler(filters.TEXT & ~filters.COMMAND, stop_loss_handler)],
                CONFIRMACAO_CONFIG: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmacao_config_handler)],
                MENU_STOP: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_stop_handler)]
            },
            # REAL_DEMO, FIXO_PERCENTUAL, CONFIG_STAKE, STOP_WIN, STOP_LOSS
            fallbacks=[],
        )

        app.add_handler(CommandHandler('menu', main_menu_command))
        app.add_handler(CommandHandler('help', help_command))

        # Messages
        app.add_handler(conv_handler_cadastro)
        app.add_handler(MessageHandler(filters.ChatType.GROUP | filters.ChatType.CHANNEL & filters.TEXT, handle_message))

        # Errors
        app.add_error_handler(error)

        # Polls the bot
        print("Polling...")
        app.run_polling(poll_interval=3)