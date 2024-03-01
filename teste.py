from iqoptionapi.stable_api import IQ_Option
from multiprocessing import Process, Event, Manager, set_start_method, Queue
import threading
import os
import time

"""def contar_decrescente(nome, limite, parar, contador):
    print(f"THREAD {nome}, limite: {limite}")
    while True:
        contador_atualizado = contador.value
        if contador_atualizado <= limite:
            #faz o processo main parar também
            print(f"Thread de {nome}, Limite atingido")
            parar.set()
            break
        time.sleep(1)

def processo(nome, func1, limite, contador):
    parar = Event()
    print(f"Iniciando contagens em {nome}...")
    time.sleep(1)
    t1 = threading.Thread(target=func1, args=(nome,limite,parar,contador,))
    t1.start()
    
    while True:
        if parar.is_set():
            print("Limite atingido na thread")
            break
        time.sleep(1)
    
    

if __name__ == "__main__":
    with Manager() as manager:
        info_trade = manager.Value(typecode='dict', value={'type': '', 'pair': '', 'direction': ''})
        pendingTrades = manager.Value(typecode='int', value=100)
        p1 = Process(target=processo, args=("Roberto", contar_decrescente, 80, pendingTrades,))
        p2 = Process(target=processo, args=("Milena", contar_decrescente, 90, pendingTrades,))

        p1.start()
        p2.start()
        x = 300
        while True:
            pendingTrades.value -= 1
            print(f'Contagem principal: {pendingTrades.value}')
            time.sleep(0.5)
            if x == 0:
                print("FIM")
                break
        p1.join()
        p2.join()"""

"""def fazer_login(email, senha):
    global pending_login_accs
    acc = IQ_Option(email, senha)
    acc_check, acc_reason = acc.connect()
    
    pending_login_accs[email] = (acc_check, acc_reason)
    print("INSIDE PROCESS: {} {} {}".format(email,acc_check, acc_reason))

if __name__ == '__main__':
    result_queue = Queue()
    with Manager() as manager:
        pending_login_accs = {}

        api = IQ_Option('winnerzonebot@gmail.com', 'WinnerzoneBOT1!')
        check, reason = api.connect()
        print('Bot connected!')
        print(api.get_balance())
        email_pass1 = ('bejr2002@gmail.com', 'Bejr2002!')
        email_pass2 = ('rey.iqop@gmail.com', '123123!')

        accs = [email_pass1, email_pass2]

    for acc in accs:
        x = Process(target=fazer_login, args=(acc[0], acc[1],))
        x.start()
        result = False
        while not(result):
            time.sleep(1)
            print("Trying")
            print(pending_login_accs)
            try:
                print(pending_login_accs[acc[0]])
                result = True
            except:
                pass
        x.terminate()
    #    except:
    #        pass"""

x = """🎯 RESULTADO DA TRADE 🎯

📊 Ativo: EURJPY 
📍 Direção: 🔴 PUT
📝 Resultado: ❌ 11:10 HIT RT

-------------------------------------------
🎯 RESULTADO DA TRADE 🎯

📊 Ativo: EURJPY 
📍 Direção: 🔴 PUT
📝 Resultado: ❌ 11:10 HIT RT

-------------------------------------------

📝 RESULTADOS 08/02/2024 📝

M5 EURUSD PUT 1.07624 ✅ 11:45 HIT RT* ❌ 11:50 HIT RV
M5 EURJPY PUT 160.669 ✅ 10:35 WIN RT
M5 EURJPY CALL 160.443 ✅ 10:20 WIN RT* ✅ 10:25 WIN RV
M5 GBPJPY PUT 188.207 ❌ 11:45 HIT RT
M5 GBPJPY CALL 187.946 ✅ 10:15 WIN RT 
M5 USDCAD CALL 1.34693 ✅ 11:30 HIT RT* ✅ 11:35 WIN RV 
M5 GBPUSD PUT 1.26114 cancelada* ✅ 11:50 WIN RV
M5 AUDJPY PUT 97.0227 ⏱️
M5 AUDJPY CALL 96.8511 ✅ 10:20 WIN RT
M5 EURGBP PUT 0.85420 ✅ 10:35 WIN RT
M5 EURGBP CALL 0.85366 ✅ 10:5 WIN RT
M5 USDJPY CALL 149.005 ⏱️
M5 AUDCAD PUT 0.87586 ⏱️

✅ 12 | ❌ 2 | ⚪️ 0"""

aux_finalMessage = x.split("\n")
trade_rv = False

# M5 USDCAD CALL 1.34693 ✅ 11:30 HIT RT* ✅ 11:35 WIN RV
# M5 GBPUSD PUT 1.26114 cancelada ✅ 11:50 WIN RV
for i, line in enumerate(aux_finalMessage):
    if line.startswith("M5"):
        spaces = len(line.split(" "))
        if trade_rv:
            if "*" in line:
                spaces = len(line.split(" "))
                line = line.replace("*", "")
                if spaces == 9:
                    aux_finalMessage[i] = " ".join(
                        line.split(" ")[0:4] + line.split(" ")[5:]
                    )
                else:
                    aux_finalMessage[i] = " ".join(
                        line.split(" ")[0:4] + line.split(" ")[8:]
                    )
        else:
            if "*" in line:
                # print(line)
                spaces = len(line.split(" "))
                line = line.replace("*", "")
                if spaces == 9:
                    aux_finalMessage[i] = " ".join(line.split(" ")[0:5])
                else:
                    aux_finalMessage[i] = " ".join(line.split(" ")[0:8])

aux_finalMessage.pop(-1)

try:
    for message in str(aux_finalMessage).split("-" * 43):
        if "📝 RESULTADOS" in message:
            results_aux_finalMessage = message
except:
    results_aux_finalMessage = str(aux_finalMessage)

aux_finalMessage.append(
    f"✅ {results_aux_finalMessage.count('✅')} | ❌ {results_aux_finalMessage.count('❌')} | ⚪ {results_aux_finalMessage.count('⚪')}"
)

mensagemParaEnviar = "\n".join(aux_finalMessage)

#print(mensagemParaEnviar)


"""for i,line in enumerate(aux_finalMessage):
    if '*' in line:
        if trade_rv == True:
        #M5 EURUSD PUT 1.07624 ❌ 11:50 HIT RV
            aux_finalMessage[i] = " ".join(line.split(" ")[0:4]+line.split(" ")[8:])
        else:
            line = line.replace("*", "")
            #M5 EURUSD PUT 1.07624 ✅ 11:45 HIT RT
            aux_finalMessage[i] = " ".join(line.split(" ")[0:8])
aux_finalMessage.pop(-1)
    

try:
    for message in str(aux_finalMessage).split('-'*43):
        if '📝 RESULTADOS' in message:
            results_aux_finalMessage = message
except:
    results_aux_finalMessage = str(aux_finalMessage)

aux_finalMessage.append(f"✅ {results_aux_finalMessage.count('✅')} | ❌ {results_aux_finalMessage.count('❌')} | ⚪ {results_aux_finalMessage.count('⚪')}")

mensagemParaEnviar = '\n'.join(aux_finalMessage)

print(mensagemParaEnviar)"""


mensagemParaEnviar = ''
a = """🚨 TRADE CANCELADA 🚨

📊 Ativo: USDCHF-OTC
📍 Direção: 🔴 PUT
❓ Motivo: Taxa atingida no fechamento da vela
⏱️ Horário: 21:49:44
💰 Preço atual: 0.867705
"""
b = """🎯 TRADE REALIZADA - RETRAÇÃO M5 🎯

📊 Ativo: USDCHF-OTC
📍 Direção: 🔴 PUT
⏱️ Horário: 21:49:44
💰 Preço atual: 0.867705
"""
c = """🎯 RESULTADO DA TRADE 🎯

📊 Ativo: GBPUSD-OTC 
📍 Direção: 🔴 PUT
📝 Resultado: ✅ 21:45 WIN RT
"""

y = [a, b, c]
trades_canceladas = ''

for i, info in enumerate(y):
    if "🚨 TRADE CANCELADA 🚨" in info:    
        trades_canceladas += " ".join(info.split("\n")[1:4])
    elif " ".join(info.split('\n')[1:4]) in trades_canceladas:        
        continue
    mensagemParaEnviar +=f"\n\n{'-' * 43}\n\n{info}" if i > 0 else f"{info}"

print(mensagemParaEnviar)
z = 10>4
print(z)