from fastapi import FastAPI, Request
from bs4 import BeautifulSoup
import json
import re

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "online", "version": "3.4"}

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
            
            if len(cells) < 11:
                continue
            
            try:
                # ✅ MAPEAMENTO CORRETO BASEADO NOS SEUS DADOS
                data_pedido = cells[0].get_text(strip=True)      # Data: "27/10/2025"
                nr_pedido = cells[1].get_text(strip=True)        # Nr. Ped: "297049"
                cod_cli = cells[2].get_text(strip=True)          # Cod. Cli: "15756"
                cod_vend = cells[3].get_text(strip=True)         # Cod. Vend: "259"
                prazo = cells[4].get_text(strip=True)            # Prazo: "28 DDL"
                empresa = cells[5].get_text(strip=True)          # Empresa: "ASITECH"
                cliente = cells[6].get_text(strip=True)          # Cliente: "JANLEAF..."
                cfop = cells[7].get_text(strip=True)             # CFOP: "5.102"
                sit_fat = cells[8].get_text(strip=True)          # Sit. Fat: "Faturado"
                total_str = cells[9].get_text(strip=True)        # Total: "373,50"
                entrega_prod = cells[10].get_text(strip=True)    # Entrega Prod: "27/10/2025"
                
                # Pega o vendedor completo (se houver cells[11], senão usa cod_vend)
                vendedor = cells[11].get_text(strip=True) if len(cells) > 11 else f"{cod_vend} - (Nome não encontrado)"
                
                # Converte total
                total = total_str.replace('.', '').replace(',', '.')
                
                # Validação
                if not nr_pedido or not cliente:
                    continue
                
                # ✅ Objeto com ordem correta
                pedido = {
                    "Data": data_pedido,
                    "Entrega Prod.": entrega_prod,
                    "Nr. Ped": nr_pedido,
                    "Cliente": cliente,
                    "Vendedor": vendedor,
                    "Total": total
                }
                pedidos.append(pedido)
                
                print(f"✅ Pedido {nr_pedido}: {cliente} - R$ {total}")
                
            except (IndexError, AttributeError, ValueError) as e:
                print(f"⚠️ Erro ao processar linha: {e}")
                # Imprime células para debug
                print(f"   Células disponíveis: {len(cells)}")
                for i, cell in enumerate(cells[:12]):  # Mostra até 12
                    print(f"   cells[{i}] = {cell.get_text(strip=True)[:30]}")
                continue
        
        print(f"\n🎉 Total processado: {len(pedidos)} pedidos")
        return pedidos
    
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return []
