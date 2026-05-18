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
from urllib.parse import quote
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.clock import mainthread
from kivymd.uix.screen import MDScreen

# --- CONFIGURAÇÕES DE BACKEND ---

audio = sr.Recognizer()
maquina = pyttsx3.init()

# Configuração de voz
voices = maquina.getProperty('voices')
for voice in voices:
    if "brazil" in voice.name.lower():
        maquina.setProperty('voice', voice.id)

print("Ajustando microfone para o ruído da sala... aguarde.")
with sr.Microphone() as source:
    audio.adjust_for_ambient_noise(source, duration=1)

# --- FUNÇÕES DE LÓGICA ---

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

# --- INTERFACE E APP ---

class MainScreen(MDScreen):
    pass

class SafiraApp(MDApp):
    def build(self):
        # Carrega o KV e define o tema
        self.theme_cls.primary_palette = "Blue"
        return Builder.load_file("safira.kv")

    def on_start(self):
        # Inicia o loop da Safira em uma thread separada para não travar a tela
        threading.Thread(target=self.loop_principal, daemon=True).start()

    # --- ATUALIZADORES DE INTERFACE (Thread Safe) ---
    @mainthread
    def atualizar_status(self, texto):
        self.root.get_screen('main').ids.status_label.text = texto

    @mainthread
    def atualizar_comando_lido(self, texto):
        self.root.get_screen('main').ids.last_command.text = f"Você disse: {texto}"

    # --- LOOP PRINCIPAL ---
    def falar(self, texto):
        print(f"Safira: {texto}")
        # Atualiza a interface antes de falar
        self.atualizar_status(texto)
        maquina.say(texto)
        maquina.runAndWait()

    def ouvir_comando(self):
        try:
            with sr.Microphone() as source:
                voz = audio.listen(source, phrase_time_limit=5)
                comando = audio.recognize_google(voz, language='pt-BR').lower()
                
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
                print(f"Comando recebido: {comando}")

                # 1. HORAS
                if "horas" in comando:
                    hora = datetime.datetime.now().strftime("%H:%M")
                    self.falar(f"Agora são {hora}")

                # 2. WIKIPEDIA
                elif "pesquisar" in comando:
                    procurar = comando.replace("pesquisar", "").strip()
                    self.falar(f"Buscando {procurar}")
                    try:
                        wikipedia.set_lang("pt")
                        resumo = wikipedia.summary(procurar, sentences=1)
                        self.falar(resumo)
                    except:
                        self.falar("Não encontrei nada sobre isso.")

                # 3. CLIMA
                elif 'tempo em' in comando:
                    cidade = comando.replace('tempo em', '').strip()
                    self.falar(buscar_clima(cidade))

                # 4. ABRIR SITES
                elif 'abrir github' in comando:
                    self.falar("Abrindo seu GitHub, bons códigos!")
                    webbrowser.open("https://github.com")
                    
                elif 'abrir youtube' in comando:
                    self.falar("Abrindo YouTube.")
                    webbrowser.open("https://www.youtube.com/")
                    
                elif 'abrir noticias' in comando:
                    self.falar("Abrindo as últimas notícias.")
                    webbrowser.open("https://jovempan.com.br/")

                # 5. CRIAR NOTA
                elif 'anote' in comando or 'anotar' in comando:
                    nota = comando.replace('anote', '').replace('anotar', '').strip()
                    with open("notas.txt", "a", encoding="utf-8") as f:
                        f.write(f"- {nota} ({datetime.datetime.now().strftime('%d/%m')})\n")
                    self.falar("Anotei no seu bloco de notas.")

                # 6. SAIR
                elif "desligar" in comando or "sair" in comando:
                    self.falar("Encerrando sistemas. Até logo!")
                    os._exit(0) # Força o fechamento de todas as threads

if __name__ == "__main__":
    SafiraApp().run()