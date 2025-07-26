import os
import gradio as gr
import requests
import inspect
import pandas as pd
from agent import *
import random



class BasicAgent:

    def __init__(self):
        print("BasicAgent initialized.")
        self.agent = build_agent()

    def __call__(self, question: str) -> str:
        print(f"Agent received question (first 50 chars): {question[:50]}...")

        fixed_answer = self.agent.run(question)
        if not isinstance(fixed_answer, (str, int, float)):
            fixed_answer = str(fixed_answer)
        print(f"Agent returning fixed answer: {fixed_answer}")
        return fixed_answer

try:
    agent = BasicAgent()
except Exception as e:
    print(f"Error instantiating agent: {e}")
   




def basic_response(message: str, history: list) -> str:
    """Basit, genel sohbet sorularını cevaplar."""
    print("-> Basic Response modülü çalışıyor.")
    system_prompt = "You are a helpful and friendly assistant. Keep your answers concise and conversational."
    
    # Gradio'dan gelen history formatını API'nin istediği formata çevirelim.
    messages = [{"role": "system", "content": system_prompt}]
    for user_msg, assistant_msg in history:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": assistant_msg})
    messages.append({"role": "user", "content": message})
    
    return call_llm(messages)



def call_llm(message: str) -> str:
    url = "https://c71e5ed4aba7.ngrok-free.app/api/chat"
    headers = {"Content-Type": "application/json"}

    data = {
        "model": "gemma3:27b",
        "stream": False,
        "messages": message
    }
    response = requests.post(url, headers=headers, data=json.dumps(data), stream=True)
    full_response = ""
    for line in response.iter_lines():
        if line:
            json_data = json.loads(line.decode("utf-8"))
            content = json_data.get("message", {}).get("content", "")
            full_response += content
    #print(full_response)
    return full_response


def route_question(message: str) -> str:
    """
    Kullanıcının sorusunu analiz eder ve 'AGENT' veya 'BASIC' olarak sınıflandırır.
    Bu fonksiyon, sistemin beynidir.
    """
    print(f"Yönlendirme için soru analiz ediliyor: '{message[:50]}...'")
    
    # Router'a özel, çok net bir sistem talimatı veriyoruz.
    system_prompt = (
        "You are an expert routing assistant. Your task is to classify the user's query. "
        "If the query requires real-time information, access to external tools (like web search, calculations, file access), "
        "or is a complex question that a simple chat model cannot answer, respond with only the single word: AGENT. "
        "For all other general conversational queries, greetings, simple questions, or chit-chat, respond with only the single word: BASIC."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ]
    
    # Daha küçük ve hızlı bir model kullanmak burada maliyeti ve hızı artırabilir.
    decision = call_llm(messages) # Örnek olarak daha küçük bir model
    
    # Çıktının sadece "AGENT" veya "BASIC" olduğundan emin olalım.
    decision_clean = "AGENT" if "AGENT" in decision.upper() else "BASIC"
    print(f"Yönlendirme Kararı: {decision_clean}")
    return decision_clean


def agent_response(message, history):

    submitted_answer = agent(message)
    return submitted_answer

def hybrid_response_with_router(message: str, history: list):
    """
    Gradio arayüzünün ana giriş noktası.
    Önce soruyu yönlendirir, sonra ilgili fonksiyonu çağırır.
    'yield' kullanarak arayüzü aşamalı olarak günceller.
    """
    # 1. Adım: Sorunun nereye gideceğine karar ver.
    decision = route_question(message)
    
    # 2. Adım: Karara göre ilgili fonksiyonu çalıştır.
    if decision == "AGENT":
        # Kullanıcıya bekleyeceğini bildir.
        yield "Agent'ı devreye alıyorum, bu işlem biraz zaman alabilir... ⏳"
        # Agent'ı çalıştır ve sonucu al.
        response = agent_response(message, history)
        yield response
    else: # decision == "BASIC"
        response = basic_response(message, history)
        yield response


gr.ChatInterface(
    fn=hybrid_response_with_router,
    title="🤖 Hibrit Chatbot & Agent Sistemi",
    description="Soru sorun. Sistem, sorunun basit mi yoksa karmaşık mı olduğuna karar verip ilgili modülü çalıştıracaktır.",
    examples=[["Selam, naber?"], ["Türkiye'nin güncel nüfusu ne kadar?"], ["Bugün İstanbul'da hava nasıl?"]],
).launch()