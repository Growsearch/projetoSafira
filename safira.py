import speech_recognition as sr # para importar: pip install SpeechRecognition
import pyttsx3  # para instalar : pip install pyttsx3
import datetime
import wikipedia  # para instalar: pip install wikipedia
import pywhatkit
import os
import requests
import webbrowser
import random
import threading
from urllib.parse import quote
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.clock import mainthread
from kivymd.uix.screen import MDScreen
from kivy.properties import StringProperty

# --- CONFIGURAÇÕES DE BACKEND ---

audio = sr.Recognizer()
maquina = pyttsx3.init()

# Configuração de voz
try:
    voices = maquina.getProperty("voices")
    for voice in voices:
        if "brazil" in voice.name.lower():
            maquina.setProperty("voice", voice.id)
            break
except Exception as e:
    print(f"Erro ao configurar voz: {e}")

# --- FUNÇÕES DE LÓGICA ---

def buscar_clima(cidade):
    cidade_codificada = quote(cidade)
    api_key = "0cc5b6faa55d0681bc9827b57a39ebeb"
    link = f"https://api.openweathermap.org/data/2.5/weather?q={cidade_codificada}&appid={api_key}&lang=pt_br&units=metric"
    
    try:
        requisicao = requests.get(link)
        dados = requisicao.json()
        if dados.get("cod") == 200:
            temp = dados["main"]["temp"]
            desc = dados["weather"][0]["description"]
            return f"Em {cidade}, faz {temp:.1f} graus com {desc}."
    except:
        return "Não consegui checar o clima agora."
    return "Cidade não encontrada."

def buscar_cripto(moeda_id, moeda_name):
    # Api do coin market cap
    link = f"https://api.coingecko.com/api/v3/simple/price?ids={moeda_id}&vs_currencies=brl"
    
    try:
        headers = {'User-agent' : 'Mozilla/5.0'}
        requisicao = requests.get(link, headers=headers)
        dados = requisicao.json()
        
        if moeda_id in dados:
            preco = dados[moeda_id]["brl"]
            preco_formatado = f"R$ {preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return (f"O preço atual do {moeda_name} é {preco_formatado}")
    except Exception as e:
        print(f"Erro ao buscar preço da criptomoeda: {e}")
        return ("Não consegui checar o preço agora.")
        
    return ("Moeda não encontrada.")

# --- INTERFACE E APP ---

class MainScreen(MDScreen):
    status_text = StringProperty("Aguardando comando...")
    command_text = StringProperty("Diga 'Safira' para começar")

class SafiraApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Dark" # Estilo escuro para combinar com o canvas
        return Builder.load_file("safira.kv")

    def on_start(self):
        # Ajuste do microfone em uma thread para não travar a abertura do app
        threading.Thread(target=self.inicializar_audio, daemon=True).start()

    def inicializar_audio(self):
        self.atualizar_status("Ajustando microfone...")
        try:
            with sr.Microphone() as source:
                audio.adjust_for_ambient_noise(source, duration=1)
            self.atualizar_status("Safira pronta!")
            self.loop_principal()
        except Exception as e:
            self.atualizar_status(f"Erro de áudio: {e}")

    # --- ATUALIZADORES DE INTERFACE (Thread Safe) ---
    @mainthread
    def atualizar_status(self, texto):
        # Busca a tela de forma segura
        if self.root:
            screen = self.root.get_screen("main")
            if screen:
                screen.status_text = texto

    @mainthread
    def atualizar_comando_lido(self, texto):
        if self.root:
            screen = self.root.get_screen("main")
            if screen:
                screen.command_text = f"Você disse: {texto}"

    # --- LOOP PRINCIPAL ---
    def falar(self, texto):
        print(f"Safira: {texto}")
        self.atualizar_status(texto)
        maquina.say(texto)
        maquina.runAndWait()

    def ouvir_comando(self):
        try:
            with sr.Microphone() as source:
                voz = audio.listen(source, phrase_time_limit=5)
                comando = audio.recognize_google(voz, language="pt-BR").lower()
                
                if "safira" in comando:
                    comando = comando.replace("safira", "").strip()
                    respostas_ativacao = ["Sim?", "Pois não?", "Estou ouvindo.", "Oi!"]
                    ativacao = random.choice(respostas_ativacao)
                    self.falar(ativacao)
                    return comando
        except sr.UnknownValueError:
            pass
        except Exception as e:
            print(f"Erro no microfone: {e}")
        return ""

    def loop_principal(self):
        while True:
            comando = self.ouvir_comando()
            
            if comando != "":
                self.atualizar_comando_lido(comando)
                
                if "horas" in comando:
                    hora = datetime.datetime.now().strftime("%H:%M")
                    self.falar(f"Agora são {hora}")

                elif "pesquisar" in comando:
                    procurar = comando.replace("pesquisar", "").strip()
                    self.falar(f"Buscando {procurar}")
                    try:
                        wikipedia.set_lang("pt")
                        resumo = wikipedia.summary(procurar, sentences=1)
                        self.falar(resumo)
                    except:
                        self.falar("Não encontrei nada sobre isso.")

                elif "tempo em" in comando:
                    cidade = comando.replace("tempo em", "").strip()
                    self.falar(buscar_clima(cidade))

                elif "abrir github" in comando:
                    self.falar("Abrindo seu GitHub.")
                    webbrowser.open("https://github.com")
                    
                elif "abrir youtube" in comando:
                    self.falar("Abrindo YouTube.")
                    webbrowser.open("https://www.youtube.com/")
                    
                elif "anote" in comando or "anotar" in comando:
                    nota = comando.replace("anote", "").replace("anotar", "").strip()
                    with open("notas.txt", "a", encoding="utf-8") as f:
                        f.write(f"- {nota} ({datetime.datetime.now().strftime('%d/%m')})\n")
                    self.falar("Anotei no seu bloco de notas.")
                    
                elif "preço do bitcoin" in comando or "valor do Bitcoin" in comando:
                    self.falar("Checando preço do Bitcoin...")
                    resposta = buscar_cripto("bitcoin", "Bitcoin")
                    self.falar(resposta)
                    
                elif "preço do ethereum" in comando or "valor do ethereum" in comando:
                    self.falar("Checando preço do Ethereum...")
                    resposta = buscar_cripto("ethereum", "Ethereum")
                    self.falar(resposta)
                    
                elif "preço da Solana" in comando or "valor da Solana" in comando:
                    self.falar("Checando preço da Solana...")
                    resposta = buscar_cripto("solana", "Solana")
                    self.falar(resposta)

                elif "desligar" in comando or "sair" in comando:
                    self.falar("Até logo!")
                    os._exit(0)

if __name__ == "__main__":
    SafiraApp().run()
