import speech_recognition as sr
import pyttsx3
import datetime
import wikipedia
import pywhatkit
import os
import requests
import webbrowser # Nova: Para abrir sites
import random      # Nova: Para piadas/respostas variadas
from urllib.parse import quote

# Inicialização
audio = sr.Recognizer()
maquina = pyttsx3.init()

# Configuração de voz
voices = maquina.getProperty('voices')
for voice in voices:
    if "brazil" in voice.name.lower():
        maquina.setProperty('voice', voice.id)

# Ajuste de ruído GLOBAL (Apenas uma vez para ser mais rápido)
print("Ajustando microfone para o ruído da sala... aguarde.")
with sr.Microphone() as source:
    audio.adjust_for_ambient_noise(source, duration=1)

def falar(texto):
    print(f"Safira: {texto}")
    maquina.say(texto)
    maquina.runAndWait()

def ouvirComando():
    comando = ""
    try:
        with sr.Microphone() as source:
            # Sem o "Ouvindo..." fixo para não poluir o terminal
            voz = audio.listen(source, phrase_time_limit=5)
            comando = audio.recognize_google(voz, language='pt-BR')
            comando = comando.lower()
            
            if "safira" in comando:
                comando = comando.replace("safira", "").strip()
                # Feedback sonoro que ela ativou
                respostas_ativacao = ["Sim?", "Pois não?", "Estou ouvindo.", "Oi!"]
                falar(random.choice(respostas_ativacao))
                return comando
            
    except sr.UnknownValueError:
        pass # Ignora quando houver barulho que ela não entendeu
    except Exception as e:
        print(f"Erro: {e}")
        
    return ""

def buscar_clima(cidade):
    cidade_codificada = quote(cidade)
    api_key = "0cc5b6faa55d0681bc9827b57a39ebeb"
    link = f"https://api.openweathermap.org/data/2.5/weather?q={cidade_codificada}&appid={api_key}&lang=pt_br&units=metric"
    
    try:
        requisicao = requests.get(link)
        dados = requisicao.json()
        if dados['cod'] == 200:
            temp = dados['main']['temp']
            desc = dados['weather'][0]['description']
            return f"Em {cidade}, faz {temp:.1f} graus com {desc}."
    except:
        return "Não consegui checar o clima agora."
    return "Cidade não encontrada."

def executar_safira():
    comando = ouvirComando()
    
    if comando == "":
        return
    
    print(f"Comando recebido: {comando}")

    # --- LÓGICA DE COMANDOS ---
    
    # 1. HORAS
    if "horas" in comando:
        hora = datetime.datetime.now().strftime("%H:%M")
        falar(f"Agora são {hora}")

    # 2. WIKIPEDIA
    elif "pesquisar" in comando:
        procurar = comando.replace("pesquisar", "")
        falar(f"Buscando {procurar}")
        wikipedia.set_lang("pt")
        falar(wikipedia.summary(procurar, sentences=1))

    # 4. CLIMA
    elif 'tempo em' in comando:
        cidade = comando.replace('tempo em', '').strip()
        falar(buscar_clima(cidade))

    # 5. NOVIDADE: ABRIR SITES (Prático para o dia a dia)
    elif 'abrir github' in comando:
        falar("Abrindo seu GitHub, bons códigos!")
        webbrowser.open("https://github.com/")
        
    elif 'abrir youtube' in comando:
        falar("Abrindo YouTube, aproveite os vídeos!")
        webbrowser.open("https://www.youtube.com/")
        
    elif 'abrir noticias' in comando:
        falar("Abrindo as últimas notícias para você.")
        webbrowser.open("")

    # 7. NOVIDADE: CRIAR NOTA RÁPIDA (Manipulação de arquivos)
    elif 'anote' in comando or 'anotar' in comando:
        nota = comando.replace('anote', '').replace('anotar', '').strip()
        with open("notas.txt", "a") as f:
            f.write(f"- {nota}\n")
        falar("Anotei no seu bloco de notas.")

    # 8. SAIR
    elif "desligar" in comando or "sair" in comando:
        falar("Encerrando sistemas. Até logo!")
        exit()

# ------ INICIO ------
falar("Safira online e pronta.")
while True:
    executar_safira()