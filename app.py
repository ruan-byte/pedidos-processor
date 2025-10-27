from fastapi import FastAPI, Request
from bs4 import BeautifulSoup
import json
import re

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "online", "version": "3.3"}

@app.post("/processar-pedidos")
async def processar_pedidos(request: Request):
    """
    Processa HTML de email e retorna array de pedidos
    """
    try:
        body = await request.body()
        body_str = body.decode('utf-8').strip()
        
        try:
            payload = json.loads(body_str)
            html = payload.get("html_email", "")
        except:
            html = body_str
        
        if not html:
            return []
        
        html = re.sub(r'[\r\n\t]+', ' ', html)
        soup = BeautifulSoup(html, 'html.parser')
        pedidos = []
        
        for tr in soup.find_all('tr'):
            classes = tr.get('class', []) if tr.get('class') else []
            
            if not any('destac' in str(c) for c in classes):
                continue
            
            cells = tr.find_all('td')
            
            # ✅ Verifica se tem pelo menos 12 células (era 11 antes)
            if len(cells) < 12:
                continue
            
            try:
                # ✅ ÍNDICES CORRETOS
                data_pedido = cells[0].get_text(strip=True)      # Data
                entrega_prod = cells[1].get_text(strip=True)     # DtEntrPro
                nr_pedido = cells[2].get_text(strip=True)        # Nr. Ped
                cod_cli = cells[3].get_text(strip=True)          # Cod. Cli
                cliente = cells[4].get_text(strip=True)          # Cliente
                cod_vend = cells[5].get_text(strip=True)         # Cod. Vend
                vendedor = cells[6].get_text(strip=True)         # Vendedor
                prazo = cells[7].get_text(strip=True)            # Prazo
                cfop = cells[8].get_text(strip=True)             # CFOP
                sit_fat = cells[9].get_text(strip=True)          # Sit. Fat
                total_str = cells[10].get_text(strip=True)       # Total
                empresa = cells[11].get_text(strip=True)         # Empresa
                
                # Converte total
                total = total_str.replace('.', '').replace(',', '.')
                
                # Validação
                if not nr_pedido or not cliente:
                    continue
                
                # ✅ Objeto com campos corretos
                pedido = {
                    "Data": data_pedido,
                    "Entrega Prod.": entrega_prod,
                    "Nr. Ped": nr_pedido,
                    "Cliente": cliente,
                    "Vendedor": vendedor,
                    "Total": total,
                    "Cod. Cli.": cod_cli,
                    "Prazo": prazo,
                    "CFOP": cfop,
                    "Sit. Fat.": sit_fat,
                    "Empresa": empresa
                }
                pedidos.append(pedido)
                
                # 🐛 DEBUG: Log cada pedido processado
                print(f"✅ Pedido {nr_pedido}: {cliente} - R$ {total}")
                
            except (IndexError, AttributeError, ValueError) as e:
                print(f"⚠️ Erro ao processar linha: {e}")
                continue
        
        print(f"\n🎉 Total processado: {len(pedidos)} pedidos")
        return pedidos
    
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return []
