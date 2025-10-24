@app.post("/processar-pedidos")
async def processar_pedidos(request: Request):
    """
    APENAS PROCESSA E RETORNA PEDIDOS (não envia para Supabase)
    O Make faz isso depois no HTTP 2
    """
    try:
        # Lê o payload como texto
        body = await request.body()
        body_str = body.decode('utf-8')
        
        # Remove caracteres de controle
        body_str = body_str.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        
        # Parse JSON
        try:
            payload = json.loads(body_str)
        except json.JSONDecodeError as e:
            return {"error": f"JSON inválido: {str(e)}", "sucesso": False}
        
        html = payload.get("html_email", "")
        
        if not html:
            return {"error": "html_email não fornecido", "sucesso": False}
        
        # Remove caracteres de controle do HTML
        html = html.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        
        # Parse HTML com BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Encontra todas as linhas de pedido
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
        
        if not pedidos:
            return {
                "error": "Nenhum pedido encontrado",
                "sucesso": False,
                "data": []
            }
        
        # ✅ APENAS RETORNA OS PEDIDOS (não envia para Supabase aqui!)
        return {
            "sucesso": True,
            "pedidos_processados": len(pedidos),
            "data": pedidos
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "tipo": "exception",
            "sucesso": False
        }
