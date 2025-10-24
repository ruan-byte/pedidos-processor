from fastapi import FastAPI, Request
from bs4 import BeautifulSoup
import json
import re

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "online", "version": "2.2"}

@app.post("/processar-pedidos")
async def processar_pedidos(request: Request):
    try:
        body = await request.body()
        body_str = body.decode('utf-8').strip()
        
        # Tenta parsear como JSON normal
        try:
            payload = json.loads(body_str)
            html = payload.get("html_email", "")
        except:
            # Se falhar, trata como body direto
            html = body_str
        
        if not html:
            return {"data": []}
        
        # Remove quebras e tabs
        html = re.sub(r'[\r\n\t]+', ' ', html)
        
        soup = BeautifulSoup(html, 'html.parser')
        pedidos = []
        
        # Procura TODAS as linhas com classe "destaca" ou "destacb"
        for tr in soup.find_all('tr', class_=re.compile(r'destac')):
            cells = tr.find_all('td')
            
            if len(cells) < 11:
                continue
            
            try:
                pedido = {
                    "data": cells[0].get_text(strip=True),
                    "nr_pedido": cells[2].get_text(strip=True),
                    "cliente": cells[4].get_text(strip=True),
                    "vendedor": cells[6].get_text(strip=True),
                    "total": cells[10].get_text(strip=True).replace('.', '').replace(',', '.')
                }
                pedidos.append(pedido)
            except:
                continue
        
        return {"data": pedidos}
    
    except Exception as e:
        return {"data": []}
