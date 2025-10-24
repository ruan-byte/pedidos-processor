from fastapi import FastAPI, Request
from bs4 import BeautifulSoup
import json
import re

app = FastAPI()

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Servidor de processamento de pedidos",
        "version": "2.1"
    }

@app.post("/processar-pedidos")
async def processar_pedidos(request: Request):
    """
    Processa HTML e retorna JSON com pedidos
    """
    try:
        # Lê o payload
        body = await request.body()
        body_str = body.decode('utf-8')
        
        # Tira espaços e quebras
        body_str = body_str.strip()
        
        # Parse JSON - trata erros de aspas
        try:
            payload = json.loads(body_str)
        except json.JSONDecodeError as e:
            return {"error": f"JSON Error: {str(e)}", "sucesso": False, "data": []}
        
        html = payload.get("html_email", "")
        
        if not html or not isinstance(html, str):
            return {"error": "html_email inválido", "sucesso": False, "data": []}
        
        # Remove quebras e tabs do HTML
        html = re.sub(r'[\r\n\t]+', ' ', html)
        
        soup = BeautifulSoup(html, 'html.parser')
        pedidos = []
        
        # Procura por todas as linhas (tr) com dados
        for tr in soup.find_all('tr'):
            classes = tr.get('class', []) if tr.get('class') else []
            
            # Verifica se tem classes de pedido
            if not any('destaca' in str(c) for c in classes):
                continue
            
            cells = tr.find_all('td')
            if len(cells) < 11:
                continue
            
            try:
                # Extrai dados
                data = cells[0].get_text(strip=True)
                nr_ped = cells[2].get_text(strip=True)
                cliente = cells[4].get_text(strip=True)
                vendedor = cells[6].get_text(strip=True)
                total_str = cells[10].get_text(strip=True)
                
                # Converte total (remove pontos e troca vírgula)
                total = total_str.replace('.', '').replace(',', '.')
                
                # Validação básica
                if not nr_ped or not cliente:
                    continue
                
                pedido = {
                    "Nr. Ped": nr_ped,
                    "Cliente": cliente,
                    "Vendedor": vendedor,
                    "Data": data,
                    "Total": total
                }
                pedidos.append(pedido)
                
            except (IndexError, AttributeError, ValueError):
                continue
        
        return {
            "sucesso": len(pedidos) > 0,
            "pedidos_processados": len(pedidos),
            "data": pedidos
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "sucesso": False,
            "data": []
        }
