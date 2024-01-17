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
from multiprocessing import Process, Event, Manager, set_start_method
import os
import asyncio

token = "6485467359:AAFZZuUeP846mDcyhKs887Hs-LqjGoKJHrw"
botUsername = "@wzTaxa_bot"

# TEM QUE TER THREAD PARA VERIFICAR EM TODAS AS CONTAS SE TEM STOP WIN OU STOP LOSS

MENU_OPTIONS, CODIGO_BOT, CADASTRO_SENHA, REAL_DEMO, FIXO_PERCENTUAL, CONFIG_STAKE, STOP_WIN, STOP_LOSS, CONFIRMACAO_CONFIG = range(
    9)


# Comandos
def showConfigs(context):
    context.user_data['ultima_modificacao'] = datetime.now().strftime("%H:%M:%S")
    print(context.user_data['modo_config'])
    linhas = [
        f"📩 Conta: {context.user_data['email']}",
        # f"💰 Banca inicial: {context.user_data['banca_inicial']}",
        f"⚙️ Tipo de conta: {context.user_data['tipo_conta']} 🟢" if context.user_data[
                                                                        'tipo_conta'] == 'REAL' else f"⚙️ Tipo de conta: {context.user_data['tipo_conta']} 🟠",

        f"\n📍 Stake: R${context.user_data['stake']}" if context.user_data[
                                                            'modo_config'] == 'Valor' else f"📍 Stake: {context.user_data['stake']}%",

        f"📍 Stop Win: R${context.user_data['stop_win']}" if context.user_data[
                                                                'modo_config'] == 'Valor' else f"📍 Stop Win: {context.user_data['stop_win']}%",
        f"📍 Stop Loss: R${context.user_data['stop_loss']}" if context.user_data[
                                                                  'modo_config'] == 'Valor' else f"📍 Stop Loss: {context.user_data['stop_loss']}%",
        f"\n⏱️ Última modificação: {context.user_data['ultima_modificacao']}"
    ]

    return "\n".join(linhas)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(context.user_data)
    keyboard = [
        [KeyboardButton("Iniciar Bot")],
        [KeyboardButton("Suporte")]
    ]
    mainMenu = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    # Enviando a mensagem com o menu
    await update.message.reply_text("Selecione uma opção:", reply_markup=mainMenu, parse_mode='Markdown')

    # Definindo o estado para a etapa do menu
    return MENU_OPTIONS


async def listaDeTransmissao(context: ContextTypes.DEFAULT_TYPE):
    # Beep the person who called this alarm:
    global mensagemTransmissao, mensagensEnviadas
    if not (f"{context.job.chat_id}: {mensagemTransmissao}" in mensagensEnviadas) and mensagemTransmissao != '':
        await context.bot.send_message(chat_id=context.job.chat_id, text=f'{mensagemTransmissao}')
        mensagensEnviadas.append(f"{context.job.chat_id}: {mensagemTransmissao}")
    # context.user_data['messagesReceived'] += f' {mensagemTransmissao}'


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_chat.full_name
    chat_id = update.message.chat_id

    context.job_queue.run_repeating(listaDeTransmissao, data=name, chat_id=chat_id, interval=0.1, first=5)
    await update.message.reply_text("Inscrito na sequência", reply_markup=ReplyKeyboardRemove())


# Função para lidar com a escolha no menu
async def menu_options_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Obtendo a escolha do usuário
    user_choice = update.message.text.lower()

    if user_choice == 'iniciar bot':
        # Pedindo que o usuário forneça o email
        reply_markup = ReplyKeyboardRemove()
        await update.message.reply_text(
            "Ok! Antes disso, forneça o seu código do bot da WZ. (Esse código foi passado para você no momento da compra da licença)",
            reply_markup=reply_markup)
        # Definindo o estado para a etapa do email no cadastro
        return CODIGO_BOT
    elif user_choice == 'suporte':
        await update.message.reply_text(
            "Link ytb como usar\nCaso tenha algum outro problema que não esteja presente no vídeo, entre em contato com @Winnerzone_83")
    else:
        # Opção inválida, reinicie a conversa
        #await update.message.reply_text("Opção inválida. Por favor, selecione uma opção válida.")
        pass
    # Reiniciando a conversa
    return ConversationHandler.END


async def codigo_bot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Obtendo o email do usuário
    codigo = update.message.text

    lista_codigos = ['1', '2', '3']
    if codigo in lista_codigos:

        if codigo == '1':
            context.user_data['email'] = 'bejr2002@gmail.com'
        elif codigo == '2':
            context.user_data['email'] = 'rey.iqop@gmail.com'
        elif codigo == '3':
            context.user_data['email'] = 'belmorvictor@gmail.com'

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



# Função para lidar com o fornecimento da senha
async def cadastro_senha_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Obtendo a senha do usuário
    senha = update.message.text

    # Salvando a senha no contexto para uso posterior, se necessário
    context.user_data['senha'] = senha

    # Realizando qualquer ação necessária com as informações coletadas
    # ...
    context.user_data['api'] = IQ_Option(context.user_data['email'], context.user_data['senha'])
    bot_check, bot_reason = context.user_data['api'].connect()
    if bot_check:
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
            await update.message.reply_text(f"E-mail ou senha incorretos.")
        else:
            await update.message.reply_text(f"Erro ao realizar login. {bot_reason}")
        # Reiniciando a conversa
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Digite novamente a senha associada ao e-mail X para tentar efetuar o login novamente")
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
        '''context.user_data['api'].change_balance('PRACTICE')
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Você escolheu operar na conta DEMO.\nSaldo atual: R${context.user_data['api'].get_balance()}", reply_markup = ReplyKeyboardRemove())'''
    elif 'real' in tipo_conta:
        context.user_data['tipo_conta'] = 'REAL'
        '''context.user_data['api'].change_balance('REAL')
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Você escolheu operar na conta REAL.\nSaldo atual: R${context.user_data['api'].get_balance()}", reply_markup = ReplyKeyboardRemove())'''
    else:
        context.user_data['tipo_conta'] = 'DEMO'
        '''context.user_data['api'].change_balance('PRACTICE')
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Como não entendi sua resposta, o login foi feito na conta DEMO.\nSaldo atual: R${context.user_data['api'].get_balance()}", reply_markup = ReplyKeyboardRemove())'''

    # context.user_data['banca_inicial'] = context.user_data['api'].get_balance()

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
        print('here')
        context.user_data['trades'] = []
        informacoes_conta = {
            'email': context.user_data['email'],
            'senha': context.user_data['senha'],
            'tipo_conta': context.user_data['tipo_conta'],
            'modo_config': context.user_data['modo_config'],
            'stake': context.user_data['stake'],
            'stop_win': context.user_data['stop_win'],
            'stop_loss': context.user_data['stop_loss'],
        }
        x = Process(target=aguardar_compra, args=(informacoes_conta, tradeEvent, info_trade, contas, buy, buy_multi))
        x.start()
        contas[informacoes_conta['email']] = True

        name = update.effective_chat.full_name
        chat_id = update.message.chat_id

        context.job_queue.run_repeating(listaDeTransmissao, data=name, chat_id=chat_id, interval=1, first=1)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Configurações salvas com sucesso!",
                                       reply_markup=ReplyKeyboardRemove())

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


def connect_and_buy(email, password, buy_event, tradeInfo):
    api = IQ_Option(email, password)
    check, reason = api.connect()
    if api.check_connect():
        api.change_balance('PRACTICE')
        print(f"Conectado com sucesso: {email}")
        saldo = api.get_balance()
        print("Saldo: ", saldo)
        stake = round(saldo / 50, 2)

        while True:
            print('waiting...')
            buy_event.wait()
            x = tradeInfo.value
            print(email, x)
            buy(api, x['pair'], stake, x['direction'])
            time.sleep(1)
    else:
        print(f"Falha ao conectar: {email} \nmotivo:{reason}")


def aguardar_compra(informacoes_conta, sinal_compra, info_compra, contas, func_compra, func_compra_multi):
    acc_api = IQ_Option(informacoes_conta['email'], informacoes_conta['senha'])
    check, reason = acc_api.connect()
    acc_trades = []
    if check:
        acc_api.change_balance('REAL') if informacoes_conta['tipo_conta'] == 'REAL' else acc_api.change_balance(
            'PRACTICE')
        acc_banca_inicial = acc_api.get_balance()
        acc_stake = informacoes_conta['stake'] if informacoes_conta['modo_config'] == 'Valor' else round(
            acc_banca_inicial * informacoes_conta['stake'] / 100, 2)
        print(f'Stake definida: {informacoes_conta["email"]} - {acc_stake}')
        while True:
            if not (acc_api.check_connect()):
                acc_api.connect()
            print('Waiting')
            print(acc_banca_inicial)
            if not (contas[informacoes_conta['email']]):
                break
            sinal_compra.wait()
            infos_compra_atualizadas = info_compra.value

            if infos_compra_atualizadas['type'] == 'immediate':
                if not (f"{infos_compra_atualizadas['pair']} {infos_compra_atualizadas['direction']}" in acc_trades):
                    func_compra(acc_api, acc_stake, infos_compra_atualizadas['pair'],
                                infos_compra_atualizadas['direction'])
                    acc_trades.append(f"{infos_compra_atualizadas['pair']} {infos_compra_atualizadas['direction']}")

            else:
                for i, trade_pair in enumerate(infos_compra_atualizadas['pair']):
                    if f"{trade_pair} {infos_compra_atualizadas['direction']}" in acc_trades:
                        infos_compra_atualizadas['type'].pop(i)
                        infos_compra_atualizadas['pair'].pop(i)
                        infos_compra_atualizadas['direction'].pop(i)

                func_compra_multi(acc_api, acc_stake, infos_compra_atualizadas['pair'],
                                  infos_compra_atualizadas['direction'])

                acc_trades.append(' '.join([f'{pair} {infos_compra_atualizadas["direction"][i]}' for i, pair in
                                            enumerate(infos_compra_atualizadas['pair'])]))

            print(acc_trades)

            time.sleep(0.1)


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
    api = conta
    print(pair, stake, direction, 5)
    check, id = api.buy_digital_spot(pair, stake, direction, 5)
    if check:
        # __updateLog(f"TRADE -  {pair} {direction} at {currentPrice}")
        # tradesToCheck.append((id, pair, direction, tradeTime, "immediate"))
        # pendingTrades += 1
        print(f"DIGITAL TRADE -  {pair} {direction}")
        # trades.append(f'{pair} {direction}')
    else:
        # if not (f"ERROR on digital trade {pair} {direction}" in logText):
        # __updateLog(f"ERROR on digital trade {pair} {direction} at {currentPrice} - {id}, trying binary")
        print(f"ERROR on digital trade {pair} {direction} - {id}, trying binary")
        completeHour = __getCurrentTime()
        minutes = int(completeHour.split(":")[1][-1]) % 5
        seconds = math.ceil(float(completeHour.split(":")[2]))

        time_to_buy = 5 - minutes if seconds <= 30 else 5 - minutes - 1
        time_to_buy = 5 if time_to_buy == 0 else time_to_buy  # reset to the last option if the option is 0 (0min<30sec -> can't trade)

        check, id = api.buy(stake, pair, direction, time_to_buy)
        if check:
            '''__updateLog(f"TRADE -  {pair} {direction} at {currentPrice}")
            tradesToCheck.append((id, pair, direction, tradeTime, "immediate"))
            pendingTrades += 1'''

            print(f"BINARY TRADE -  {pair} {direction}")
        #    trades.append(f'{pair} {direction}')
        else:
            # if not (f"ERROR on binary trade {pair} {direction}" in logText):
            # __updateLog(f"ERROR on binary trade {pair} {direction} at {currentPrice} - {id}")
            print(f"ERROR on binary trade {pair} {direction} - {id}")
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
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

    if message_type == 'group':
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

                print(taxas)

                response: str = handle_response(text)
                global thread_pares, thread_agendamentos, thread_transmissao
                thread_pares.start()
                thread_agendamentos.start()
                thread_transmissao.start()

            else:
                return

            #await update.message.reply_text(response)


async def error(update: Update, context=ContextTypes.DEFAULT_TYPE):
    print(f'Update: {update} caused error {context.error}')


def mensagemListaTransmissao(mensagem):
    global aux_mensagemTransmissao
    aux_mensagemTransmissao += f"\n\n{'-' * 43}\n\n{mensagem}" if aux_mensagemTransmissao != "" else f"{mensagem}"


def monitorarListaTransmissao():
    while True:
        time.sleep(10)
        global aux_mensagemTransmissao, mensagemTransmissao
        if aux_mensagemTransmissao != mensagemTransmissao and aux_mensagemTransmissao != "":
            mensagemTransmissao = aux_mensagemTransmissao
            aux_mensagemTransmissao = ""
            print(f"Overview das trades:\nAgendadas: {scheduledTrades}\nPara checar: {tradesToCheck}")
        else:
            print("Sem mudanças na mensagem")


def __getCurrentTime():
    """Gets the current time of IQ Option server to prevent misunderstandings while logging
    bots action
Returns:
    str: IQ Option server time on this format H:M:S"""
    return datetime.now().strftime(
        "%H:%M:%S"
    )


def __monitorScheduledTrades():
    """Does multitrade (BINARY) with every trade scheduled on the next 5min candle, that are stored on the scheduledTrades.

    By Default, is inactive, just waiting for a signal to start pooling. This signal is sent by monitorPairs when it has any trade scheduled, otherwise, it stays waiting for a signal.
    """
    while True:
        global scheduledTrades
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
            if (minute + 1) % 5 == 0 and seconds == 59:
                minute = minute + 1 if minute != 59 else 0
                scheduleTradeTime = f"{hour}:{str(minute).zfill(2)}:00"
                print(scheduledTrades)
                info_trade.value = {'type': 'scheduled', 'pair': scheduledTrades[0], 'direction': scheduledTrades[1]}
                tradeEvent.set()

                scheduledTradesLog = "\n".join(
                    [f'   - {pair} {scheduledTrades[1][i].upper()}' for i, pair in enumerate(scheduledTrades[0])])

                mensagem = f"🎯 TRADE(S) REALIZADA(S) - REVERSÃO M5 🎯\n📊 Transações: \n{scheduledTradesLog}\n⏱️ Horário: {scheduleTradeTime}"
                mensagemListaTransmissao(mensagem)
                time.sleep(1)
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
                time.sleep(3)
                scheduledTrades = [[], [], []]
                scheduleSign.clear()


def monitorPairs():
    global api
    print("Monitoring pairs...")
    while True:
        '''if stopThreadSignal:
                break'''
        time.sleep(0.5)
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

                        if deltaTCurrentTime >= 301:

                            lastCandle = api.get_candles(checkedPair, 300, 1, time.time())
                            lastCandleCloseValue = lastCandle[0]['close']

                            print(f"Checando {checkedPair}...")
                            print(lastCandle)
                            print("Trade em: {}\nValor atual: {}".format(tradePrice, lastCandleCloseValue))
                            if lastCandleCloseValue < tradePrice:
                                # down
                                print("Abaixou")
                                if tradeType == "immediate":
                                    result = "✅ WIN RT" if tradeDirection == 'put' else "❌ HIT RT"
                                else:
                                    result = "✅ WIN RV" if tradeDirection == 'put' else "❌ HIT RV"

                            elif lastCandleCloseValue > tradePrice:
                                # up
                                print("Aumentou")
                                if tradeType == "immediate":
                                    result = "✅ WIN RT" if tradeDirection == 'call' else "❌ HIT RT"
                                else:
                                    result = "✅ WIN RV" if tradeDirection == 'call' else "❌ HIT RV"

                                # print("Win") if tradeDirection == 'call' else print("Lose")
                            else:
                                # draw
                                print("Igual")
                                if tradeType == "immediate":
                                    result = "⚪ DOJI"
                                else:
                                    result = "⚪ DOJI"

                            print(f"Resultado: {result}")
                            tradesToCheck.pop(tradeIndex)
                            tradeDirectionMessage = "🔴 PUT" if tradeDirection == 'put' else "🟢 CALL"
                            menssagemResultado = f"🎯 RESULTADO DA TRADE 🎯\n\n📊 Ativo: {monitored_pair} \nDireção: {tradeDirectionMessage}\n⏱️ Horário: {':'.join(tradeTime.split(':')[0:2])}\n📝 Resultado: {result}"
                            mensagemListaTransmissao(menssagemResultado)

            if not (api.check_connect()):
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

            print(f"Monitoring... {monitored_pair} {current_price}")
            currentTime = __getCurrentTime()
            minute = int(currentTime[-4])
            seconds = int(currentTime[-2:])
            if ((upper_limit != None and current_price < upper_limit) and (
                    bottom_limit != None and current_price > bottom_limit)):
                continue

            elif upper_limit != None and current_price >= upper_limit:

                if (f"{monitored_pair} put") not in trades:
                    print(f"{currentTime}: {monitored_pair} at {current_price} touched the upper limit ({upper_limit})")
                    if (minute % 5 == 0) and (seconds <= 5) or ((datetime.strptime(currentTime,
                                                                                   "%H:%M:%S") - datetime.strptime(
                            startTime, '%H:%M:%S')).total_seconds() < 10):
                        taxas[monitored_pair]["PUT"] = None
                        if (minute % 5 == 0) and (seconds <= 10):
                            mensagem = f"🚨 TRADE CANCELADA 🚨\n\n📊 Ativo: {monitored_pair}\n📍 Direção: 🔴 PUT\n❓ Motivo: Taxa atingida na abertura da vela\n⏱️ Horário: {currentTime}\n💰 Preço atual: {current_price}"
                        else:
                            mensagem = f"🚨 TRADE CANCELADA 🚨\n\n📊 Ativo: {monitored_pair}\n📍 Direção: 🔴 PUT\n❓ Motivo: Taxa atingida no momento de início do bot\n⏱️ Horário: {currentTime}\n💰 Preço atual: {current_price}"
                        mensagemListaTransmissao(mensagem)
                        continue

                    elif (minute == 9 or minute == 4) or (
                            (minute == 8 and seconds >= 35) or (minute == 3 and seconds >= 35)):
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
                        time.sleep(0.3)
                        tradeEvent.clear()
                        info_trade.value = {'type': '', 'pair': '', 'direction': ''}
                        trades.append(f"{monitored_pair} put")

                        aux_hour = int(currentTime.split(":")[0])
                        aux_minutes = int(currentTime.split(":")[1])
                        aux_minutes = aux_minutes - aux_minutes % 5

                        tradesToCheck.append(
                            (monitored_pair, f"{aux_hour}:{aux_minutes}:00", current_price, 'put', 'immediate'))
                        mensagem = f"🎯 TRADE REALIZADA - RETRAÇÃO M5 🎯\n\n📊 Ativo: {monitored_pair}\n📍 Direção: 🔴 PUT\n⏱️ Horário: {currentTime}\n💰 Preço atual: {current_price}"

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
                        continue

                    elif (minute == 9 or minute == 4) or (
                            (minute == 8 and seconds >= 35) or (minute == 3 and seconds >= 35)):
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
                        time.sleep(0.3)
                        tradeEvent.clear()
                        trades.append(f"{monitored_pair} call")

                        aux_hour = int(currentTime.split(":")[0])
                        aux_minutes = int(currentTime.split(":")[1])
                        aux_minutes = aux_minutes - aux_minutes % 5

                        tradesToCheck.append(
                            (monitored_pair, f"{aux_hour}:{aux_minutes}:00", current_price, 'call', 'immediate'))
                        info_trade.value = {'type': '', 'pair': '', 'direction': ''}

                    mensagemListaTransmissao(mensagem)


if __name__ == '__main__':
    set_start_method("spawn")
    taxas = {}

    aux_mensagemTransmissao = ''
    mensagemTransmissao = ''
    mensagensEnviadas = []

    trades = []
    stopThreadSignal = False
    scheduledTrades = [[], [], []]
    scheduleSign = threading.Event()

    tradesToCheck = []

    with Manager() as manager:
        thread_pares = threading.Thread(target=monitorPairs)
        thread_agendamentos = threading.Thread(target=__monitorScheduledTrades)
        thread_transmissao = threading.Thread(target=monitorarListaTransmissao)
        info_trade = manager.Value(typecode='dict', value={'type': '', 'pair': '', 'direction': ''})
        contas = manager.dict()
        tradeEvent = Event()

        startTime = __getCurrentTime()
        print("Starting... with Victor now 2")
        num_cores = os.cpu_count()
        #print(f"Número de núcleos da CPU: {num_cores}")
        api = IQ_Option('winnerzonebot@gmail.com', 'WinnerzoneBOT1!')
        check, reason = api.connect()
        print('Bot connected!')
        print(api.get_balance())

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
                CONFIG_STAKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, stake_handler)],
                STOP_WIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, stop_win_handler)],
                STOP_LOSS: [MessageHandler(filters.TEXT & ~filters.COMMAND, stop_loss_handler)],
                CONFIRMACAO_CONFIG: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmacao_config_handler)]
            },
            # REAL_DEMO, FIXO_PERCENTUAL, CONFIG_STAKE, STOP_WIN, STOP_LOSS
            fallbacks=[],
        )

        app.add_handler(CommandHandler('start', start_command))
        app.add_handler(CommandHandler('help', help_command))

        # Messages
        app.add_handler(conv_handler_cadastro)
        app.add_handler(MessageHandler(filters.ChatType.GROUP & filters.TEXT, handle_message))
        # Errors
        app.add_error_handler(error)

        # Polls the bot
        print("Polling...")
        app.run_polling(poll_interval=3)