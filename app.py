from fastapi import FastAPI, Request
from bs4 import BeautifulSoup
import re
import json

app = FastAPI()

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Servidor de processamento de pedidos",
        "version": "2.0"
    }

@app.post("/processar-pedidos")
async def processar_pedidos(request: Request):
    """
    Processa HTML e retorna JSON com pedidos
    (não envia para Supabase - Make faz isso!)
    """
    try:
        body = await request.body()
        body_str = body.decode('utf-8')
        body_str = body_str.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        
        payload = json.loads(body_str)
        html = payload.get("html_email", "")
        
        if not html:
            return {"error": "html_email não fornecido", "sucesso": False, "data": []}
        
        html = html.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        soup = BeautifulSoup(html, 'html.parser')
        
        pedidos = []
        for tr in soup.find_all('tr', class_=re.compile(r'x?_?destac[ab]')):
            cells = tr.find_all('td')
            
            if len(cells) >= 12:
                try:
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
                except (IndexError, AttributeError):
                    continue
        
        return {
            "sucesso": len(pedidos) > 0,
            "pedidos_processados": len(pedidos),
            "data": pedidos
        }
    
    except Exception as e:
        return {"error": str(e), "sucesso": False, "data": []}
