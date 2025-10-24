from fastapi import FastAPI, Request
from bs4 import BeautifulSoup
import json
import re

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "online", "version": "3.0"}

@app.post("/processar-pedidos")
async def processar_pedidos(request: Request):
    """
    Processa HTML e retorna array de pedidos
    """
    try:
        body = await request.body()
        body_str = body.decode('utf-8').strip()
        
        # Parse JSON
        try:
            payload = json.loads(body_str)
            html = payload.get("html_email", "")
        except:
            html = body_str
        
        if not html:
            return []
        
        # Remove quebras e tabs
        html = re.sub(r'[\r\n\t]+', ' ', html)
        
        soup = BeautifulSoup(html, 'html.parser')
        pedidos = []
        
        # Procura todas as linhas com classe "destaca" ou "destacb"
        for tr in soup.find_all('tr'):
            classes = tr.get('class', []) if tr.get('class') else []
            
            # Verifica se tem classe de pedido
            if not any('destac' in str(c) for c in classes):
                continue
            
            cells = tr.find_all('td')
            if len(cells) < 11:
                continue
            
            try:
                # Extrai dados
                data_pedido = cells[0].get_text(strip=True)
                nr_pedido = cells[2].get_text(strip=True)
                cliente = cells[4].get_text(strip=True)
                vendedor = cells[6].get_text(strip=True)
                total_str = cells[10].get_text(strip=True)
                
                # Converte total
                total = total_str.replace('.', '').replace(',', '.')
                
                # Validação
                if not nr_pedido or not cliente:
                    continue
                
                # Cria objeto
                pedido = {
                    "data_pedido": data_pedido,
                    "nr_pedido": nr_pedido,
                    "cliente": cliente,
                    "vendedor": vendedor,
                    "total": total
                }
                pedidos.append(pedido)
                
            except (IndexError, AttributeError, ValueError):
                continue
        
        # ✅ RETORNA ARRAY DIRETO (não wrapped)
        return pedidos
    
    except Exception as e:
        return []
