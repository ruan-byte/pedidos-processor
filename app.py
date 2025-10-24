from fastapi import FastAPI, Request
from bs4 import BeautifulSoup
import json
import re

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "online", "version": "3.1"}

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
            return {"pedidos": [], "total": 0}
        
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
                # ✅ Extrai TODOS os dados necessários
                data_pedido = cells[0].get_text(strip=True)      # Coluna 0
                entrega_prod = cells[1].get_text(strip=True)     # Coluna 1 - ADICIONADO!
                nr_pedido = cells[2].get_text(strip=True)        # Coluna 2
                cliente = cells[4].get_text(strip=True)          # Coluna 4
                vendedor = cells[6].get_text(strip=True)         # Coluna 6
                total_str = cells[10].get_text(strip=True)       # Coluna 10
                
                # Converte total (remove pontos de milhar, troca vírgula por ponto)
                total = total_str.replace('.', '').replace(',', '.')
                
                # Validação básica
                if not nr_pedido or not cliente:
                    continue
                
                # ✅ Cria objeto com campos corretos
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
                # Log do erro mas continua processando
                print(f"Erro ao processar linha: {e}")
                continue
        
        # ✅ Retorna objeto com array e contagem
        return {
            "pedidos": pedidos,
            "total": len(pedidos)
        }
    
    except Exception as e:
        # ✅ Indentação correta!
        return {
            "error": str(e),
            "pedidos": [],
            "total": 0
        }
