import speech_recognition as sr 
import pyttsx3  
import datetime
import wikipedia  
import pywhatkit
import os
import requests
import webbrowser
import random
import threading
import ctypes  # Requisito para estabilizar threads de áudio no Windows
from urllib.parse import quote
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.clock import mainthread
from kivymd.uix.screen import MDScreen
from kivy.properties import StringProperty

# --- CONFIGURAÇÕES DE BACKEND ---

audio = sr.Recognizer()

# Calibração para respostas e processamento quase instantâneos
audio.dynamic_energy_threshold = True  # Ajusta o ganho conforme o ambiente
audio.pause_threshold = 0.5  # Aguarda apenas 0.5s de silêncio para processar a fala

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
            desc = dados["weather"][0]['description']
            return f"Em {cidade}, está fazendo {temp:.1f} graus com {desc}."
    except:
        return "Não consegui checar o clima agora."
    return "Ih, não encontrei essa cidade."

def buscar_cripto(moeda_id, moeda_name):
    link = f"https://api.coingecko.com/api/v3/simple/price?ids={moeda_id}&vs_currencies=brl"
    try:
        headers = {'User-agent' : 'Mozilla/5.0'}
        requisicao = requests.get(link, headers=headers)
        dados = requisicao.json()
        
        if moeda_id in dados:
            preco = dados[moeda_id]["brl"]
            preco_formatado = f"R$ {preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"O preço atual do {moeda_name} é {preco_formatado}."
    except Exception as e:
        print(f"Erro ao buscar preço da criptomoeda: {e}")
        return "Não consegui olhar o mercado agora."
    return "Moeda não encontrada."

# --- INTERFACE E APP ---

class MainScreen(MDScreen):
    status_text = StringProperty("Aguardando comando...")
    command_text = StringProperty("Diga 'Safira' para começar")

class SafiraApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Dark" 
        return Builder.load_file("safira.kv")

    def on_start(self):
        # Dispara a inicialização em paralelo para manter a janela do Kivy responsiva
        threading.Thread(target=self.inicializar_audio, daemon=True).start()

    def inicializar_audio(self):
        # Inicializa o barramento COM dentro desta thread específica do Windows antes de ouvir ou falar
        ctypes.windll.ole32.CoInitialize(None)
        
        self.atualizar_status("Ajustando microfone...")
        try:
            with sr.Microphone() as source:
                audio.adjust_for_ambient_noise(source, duration=0.8)
            self.atualizar_status("Safira pronta!")
            self.loop_principal()
        except Exception as e:
            self.atualizar_status(f"Erro de áudio: {e}")

    # --- ATUALIZADORES DE INTERFACE (Thread Safe) ---
    @mainthread
    def atualizar_status(self, texto):
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

    def falar(self, texto):
        print(f"Safira: {texto}")
        self.atualizar_status(texto)
        maquina.say(texto)
        maquina.runAndWait()

    def ouvir_comando(self):
        try:
            with sr.Microphone() as source:
                voz = audio.listen(source, phrase_time_limit=4)
                comando = audio.recognize_google(voz, language="pt-BR").lower()
                
                if "safira" in comando:
                    comando = comando.replace("safira", "").strip()
                    respostas_ativacao = ["Sim?", "Pois não?", "Estou ouvindo.", "Oi! O que manda?", "Diga!"]
                    self.falar(random.choice(respostas_ativacao))
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
                
                # 1. HORAS
                if "horas" in comando or "que horas são" in comando:
                    hora = datetime.datetime.now().strftime("%H:%M")
                    respostas = [f"Agora são {hora}", f"Olha, são {hora}", f"No meu relógio são {hora}"]
                    self.falar(random.choice(respostas))

                # 2. WIKIPEDIA
                elif "pesquisar" in comando or "procure por" in comando:
                    procurar = comando.replace("pesquisar", "").replace("procure por", "").strip()
                    self.falar(f"Vou dar uma olhada sobre {procurar}...")
                    try:
                        wikipedia.set_lang("pt")
                        resumo = wikipedia.summary(procurar, sentences=1)
                        self.falar(resumo)
                    except:
                        self.falar("Ih, não achei nada relevante sobre isso na Wikipedia.")

                # 3. CLIMA
                elif "tempo em" in comando or "clima em" in comando:
                    cidade = comando.replace("tempo em", "").replace("clima em", "").strip()
                    self.falar(buscar_clima(cidade))

                # 4. SITES
                elif "github" in comando:
                    self.falar("Com certeza! Abrindo seu GitHub agora.")
                    webbrowser.open("https://github.com")
                    
                elif "youtube" in comando:
                    self.falar("Pode deixar, abrindo o YouTube.")
                    webbrowser.open("https://www.youtube.com/")
                    
                # 5. ANOTAÇÕES
                elif "anote" in comando or "anotar" in comando or "escreva" in comando:
                    nota = comando.replace("anote", "").replace("anotar", "").replace("escreva", "").strip()
                    with open("notas.txt", "a", encoding="utf-8") as f:
                        f.write(f"- {nota} ({datetime.datetime.now().strftime('%d/%m')})\n")
                    self.falar(random.choice(["Feito! Guardei no bloco de notas.", "Anotado!", "Prontinho, salvei."]))
                    
                # 6. MERCADO CRIPTO
                elif "bitcoin" in comando:
                    self.falar("Buscando a cotação do Bitcoin...")
                    self.falar(buscar_cripto("bitcoin", "Bitcoin"))
                    
                elif "ethereum" in comando:
                    self.falar("Deixa eu ver o preço do Ethereum...")
                    self.falar(buscar_cripto("ethereum", "Ethereum"))
                    
                elif "solana" in comando:
                    self.falar("Atualizando o valor da Solana...")
                    self.falar(buscar_cripto("solana", "Solana"))

                # 7. INTERAÇÃO HUMANA / SAUDAÇÕES
                elif "tudo bem" in comando or "como você está" in comando:
                    respostas_ia = [
                        "Comigo está tudo ótimo! E com você?",
                        "Tudo excelente, operando com cem por cento dos sistemas prontos.",
                        "Estou ótima! Pronta para te ajudar com as linhas de código hoje."
                    ]
                    self.falar(random.choice(respostas_ia))

                elif "obrigado" in comando or "valeu" in comando:
                    self.falar(random.choice(["Por nada!", "Disponha!", "Tamo junto!", "Sempre que precisar!"]))

                # 8. DESLIGAR (Encerramento Limpo)
                elif "desligar" in comando or "sair" in comando or "fechar" in comando:
                    self.falar(random.choice(["Fui! Até a próxima.", "Até logo!", "Encerrando os motores."]))
                    MDApp.get_running_app().stop()
                    break

if __name__ == "__main__":
    SafiraApp().run()