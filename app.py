from fastapi import FastAPI, Request
from bs4 import BeautifulSoup
import json
import re

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "online", "version": "3.2"}

@app.post("/processar-pedidos")
async def processar_pedidos(request: Request):
    try:
        body = await request.body()
        body_str = body.decode('utf-8').strip()
        
        try:
            payload = json.loads(body_str)
            html = payload.get("html_email", "")
        except:
            html = body_str
        
        if not html:
            return []  # ✅ Retorna array vazio
        
        html = re.sub(r'[\r\n\t]+', ' ', html)
        soup = BeautifulSoup(html, 'html.parser')
        pedidos = []
        
        for tr in soup.find_all('tr'):
            classes = tr.get('class', []) if tr.get('class') else []
            
            if not any('destac' in str(c) for c in classes):
                continue
            
            cells = tr.find_all('td')
            if len(cells) < 11:
                continue
            
            try:
                data_pedido = cells[0].get_text(strip=True)
                entrega_prod = cells[1].get_text(strip=True)
                nr_pedido = cells[2].get_text(strip=True)
                cliente = cells[4].get_text(strip=True)
                vendedor = cells[6].get_text(strip=True)
                total_str = cells[10].get_text(strip=True)
                
                total = total_str.replace('.', '').replace(',', '.')
                
                if not nr_pedido or not cliente:
                    continue
                
                pedido = {
                    "Data": data_pedido,
                    "Entrega Prod.": entrega_prod,
                    "Nr. Ped": nr_pedido,
                    "Cliente": cliente,
                    "Vendedor": vendedor,
                    "Total": total
                }
                pedidos.append(pedido)
                
            except (IndexError, AttributeError, ValueError) as e:
                print(f"Erro ao processar linha: {e}")
                continue
        
        return pedidos  # ✅ SEM WRAPPER!
    
    except Exception as e:
        print(f"Erro geral: {e}")
        return []  # ✅ Array vazio em caso de erro
