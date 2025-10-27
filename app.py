from fastapi import FastAPI, Request
from bs4 import BeautifulSoup
import json
import re

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "online", "version": "4.0"}

def converter_valor_brasileiro(valor_str: str) -> str:
    """
    Converte valores do formato brasileiro para formato numérico.
    Exemplos:
    - "18.629,20" -> "18629.20"
    - "9.455,00" -> "9455.00"
    - "373,50" -> "373.50"
    - "1.620,00" -> "1620.00"
    """
    try:
        # Remove espaços
        valor_limpo = valor_str.strip()
        
        # Remove qualquer caractere que não seja número, ponto ou vírgula
        valor_limpo = re.sub(r'[^\d,.]', '', valor_limpo)
        
        if not valor_limpo:
            return "0"
        
        # Formato brasileiro: usa . para milhares e , para decimal
        # Estratégia: remove TODOS os pontos (milhares) e troca vírgula por ponto (decimal)
        
        # Se tem vírgula, é formato brasileiro
        if ',' in valor_limpo:
            # Remove pontos (separador de milhar)
            valor_sem_pontos = valor_limpo.replace('.', '')
            # Troca vírgula por ponto (decimal)
            valor_final = valor_sem_pontos.replace(',', '.')
        else:
            # Não tem vírgula, só ponto
            # Pode ser formato americano OU número inteiro com separador de milhar
            partes = valor_limpo.split('.')
            
            if len(partes) == 2 and len(partes[1]) == 2:
                # Provavelmente decimal: "373.50"
                valor_final = valor_limpo
            else:
                # Provavelmente milhar: "1.234" -> "1234"
                valor_final = valor_limpo.replace('.', '')
        
        # Valida se é um número válido
        float(valor_final)
        
        return valor_final
        
    except Exception as e:
        print(f"❌ Erro ao converter valor '{valor_str}': {e}")
        return "0"

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
        
        # Remove quebras de linha e tabs
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
            
            # Verifica se tem pelo menos 11 células
            if len(cells) < 11:
                continue
            
            try:
                # Extrai dados conforme estrutura HTML atual
                data_pedido = cells[0].get_text(strip=True)      # Data
                nr_pedido = cells[1].get_text(strip=True)        # Nr. Ped
                cod_cli = cells[2].get_text(strip=True)          # Cod. Cli
                cliente = cells[3].get_text(strip=True)          # Cliente
                cod_vend = cells[4].get_text(strip=True)         # Cod. Vend
                vendedor = cells[5].get_text(strip=True)         # Vendedor
                prazo = cells[6].get_text(strip=True)            # Prazo
                cfop = cells[7].get_text(strip=True)             # CFOP
                sit_fat = cells[8].get_text(strip=True)          # Sit. Fat
                total_str = cells[9].get_text(strip=True)        # Total
                empresa = cells[10].get_text(strip=True)         # Empresa
                
                # ✅ Converte o valor usando função robusta
                total = converter_valor_brasileiro(total_str)
                
                # Validação básica
                if not nr_pedido or not cliente:
                    continue
                
                # Cria objeto do pedido
                pedido = {
                    "Data": data_pedido,
                    "Entrega Prod.": data_pedido,  # Usa mesma data (não existe mais no HTML)
                    "Nr. Ped": nr_pedido,
                    "Cliente": cliente,
                    "Vendedor": vendedor,
                    "Total": total
                }
                pedidos.append(pedido)
                
                print(f"✅ Pedido {nr_pedido}: {cliente} - R$ {total} (original: {total_str})")
                
            except (IndexError, AttributeError, ValueError) as e:
                print(f"⚠️ Erro ao processar linha: {e}")
                continue
        
        print(f"\n🎉 Total de pedidos processados: {len(pedidos)}")
        return pedidos
    
    except Exception as e:
        print(f"❌ Erro geral no processamento: {e}")
        import traceback
        traceback.print_exc()
        return []
