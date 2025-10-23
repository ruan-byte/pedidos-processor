from fastapi import FastAPI, Request
from bs4 import BeautifulSoup
import requests
import re
import json

app = FastAPI()

SUPABASE_URL = "https://gnpgiraaoscuvmfwcgxu.supabase.co/functions/v1/import-pedidos-dia"
SUPABASE_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImducGdpcmFhb3NjdXZtZndjZ3h1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA0NTcxODQsImV4cCI6MjA3NjAzMzE4NH0.rfPZEgi1aYyc0ebm8bIBat7zG1BgrinjL4uk34wk7lk"

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Servidor de processamento de pedidos",
        "version": "1.0"
    }

@app.post("/processar-pedidos")
async def processar_pedidos(request: Request):
    """
    Recebe HTML do email, extrai pedidos e envia para Supabase
    """
    try:
        # Lê o payload como texto primeiro
        body = await request.body()
        body_str = body.decode('utf-8')
        
        # Remove caracteres de controle problemáticos
        body_str = body_str.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        
        # Parse JSON
        payload = json.loads(body_str)
        html = payload.get("html_email", "")
        
        if not html:
            return {"error": "html_email não fornecido", "sucesso": False}
        
        # Remove caracteres de controle do HTML também
        html = html.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        
        # Parse HTML com BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Encontra todas as linhas de pedido (destaca ou destacb)
        # Aceita também x_destaca e x_destacb (formatação do Outlook)
        pedidos = []
        for tr in soup.find_all('tr', class_=re.compile('x?_?destac[ab]')):
            cells = tr.find_all('td')
            
            if len(cells) >= 12:
                # Remove pontos de milhar e troca vírgula por ponto
                total = cells[10].text.strip()
                total = total.replace('.', '').replace(',', '.')
                
                pedido = {
                    "Nr. Ped": cells[2].text.strip(),
                    "Cliente": cells[4].text.strip(),
                    "Total": total,
                    "Vendedor": cells[6].text.strip(),
                    "Data": cells[0].text.strip(),
                    "Entrega Prod.": cells[1].text.strip()
                }
                pedidos.append(pedido)
        
        if not pedidos:
            return {
                "error": "Nenhum pedido encontrado no HTML",
                "pedidos_encontrados": 0,
                "sucesso": False
            }
        
        # Envia para Supabase
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SUPABASE_TOKEN}"
        }
        
        # Serializa JSON garantindo ASCII
        payload_json = json.dumps({"data": pedidos}, ensure_ascii=True)
        
        response = requests.post(
            SUPABASE_URL,
            data=payload_json,
            headers=headers,
            timeout=30
        )
        
        return {
            "sucesso": response.status_code == 200,
            "pedidos_processados": len(pedidos),
            "supabase_response": response.json() if response.status_code == 200 else response.text,
            "status_code": response.status_code
        }
    
    except json.JSONDecodeError as e:
        return {
            "error": f"JSON Decode Error: {str(e)}",
            "tipo": "json_error",
            "sucesso": False
        }
    except Exception as e:
        return {
            "error": str(e),
            "tipo": "exception",
            "sucesso": False
        }
