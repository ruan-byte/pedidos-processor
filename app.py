import { createClient } from 'npm:@supabase/supabase-js@2.57.4';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Client-Info, Apikey'
};

const convertDateToISO = (dateStr)=>{
  try {
    if (!dateStr) return null;
    
    // Se já está em formato DD/MM/YYYY
    if (dateStr.includes('/')) {
      const [day, month, year] = dateStr.split('/');
      const fullYear = parseInt(year) < 100 ? parseInt(year) + 2000 : parseInt(year);
      const paddedMonth = month.padStart(2, '0');
      const paddedDay = day.padStart(2, '0');
      return `${fullYear}-${paddedMonth}-${paddedDay}`;
    }
    
    // Se já está em formato ISO (YYYY-MM-DD)
    if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
      return dateStr;
    }
    
    return null;
  } catch {
    return null;
  }
};

Deno.serve(async (req)=>{
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      status: 200,
      headers: corsHeaders
    });
  }
  
  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '', 
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    );
    
    const requestData = await req.json();
    
    if (!requestData || !Array.isArray(requestData)) {
      return new Response(JSON.stringify({
        error: 'Dados inválidos. Esperado um array de objetos.'
      }), {
        status: 400,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    
    // ✅ Validação mais tolerante - apenas campos essenciais
    // Entrega Prod. pode estar vazio (como no primeiro pedido do exemplo)
    const isValid = requestData.every((item)=>
      item['Nr. Ped'] && 
      item['Cliente'] && 
      item['Total'] && 
      item['Vendedor'] && 
      item['Data']
    );
    
    if (!isValid) {
      // 🐛 Log para debug - mostra quais itens estão inválidos
      const invalidItems = requestData.filter(item => 
        !item['Nr. Ped'] || !item['Cliente'] || !item['Total'] || !item['Vendedor'] || !item['Data']
      );
      
      console.error('❌ Itens inválidos encontrados:', JSON.stringify(invalidItems, null, 2));
      
      return new Response(JSON.stringify({
        error: 'Dados inválidos. Cada item deve conter: Nr. Ped, Cliente, Total, Vendedor, Data',
        invalid_items: invalidItems.map(item => ({
          nr_ped: item['Nr. Ped'] || 'FALTANDO',
          cliente: item['Cliente'] || 'FALTANDO'
        }))
      }), {
        status: 400,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    
    const fileName = `Make.com_${new Date().toISOString()}.json`;
    const now = new Date().toISOString();
    
    // Remove uploads antigos
    const { data: oldUploads } = await supabase
      .from('dashboard_uploads')
      .select('id')
      .eq('upload_type', 'pedidos_dia');
    
    if (oldUploads && oldUploads.length > 0) {
      await supabase
        .from('dashboard_uploads')
        .delete()
        .eq('upload_type', 'pedidos_dia');
    }
    
    // Cria novo registro de upload
    const { data: upload, error: uploadError } = await supabase
      .from('dashboard_uploads')
      .insert({
        upload_type: 'pedidos_dia',
        file_name: fileName,
        row_count: requestData.length,
        uploaded_at: now
      })
      .select()
      .single();
    
    if (uploadError) throw uploadError;
    
    // ✅ Converte AMBAS as datas para ISO e trata valores vazios
    const dataToInsert = requestData.map((item)=>{
      const dataISO = convertDateToISO(item['Data']);
      const entregaProdISO = convertDateToISO(item['Entrega Prod.']); // ✅ Pode retornar null se vazio
      
      let totalValue = item['Total'];
      if (typeof totalValue === 'string') {
        if (/^\d+\.\d{1,2}$/.test(totalValue)) {
          totalValue = totalValue;
        } else {
          totalValue = totalValue.replace(/\./g, '').replace(',', '.');
        }
      }
      const parsedTotal = parseFloat(totalValue) || 0;
      
      return {
        upload_id: upload.id,
        nr_ped: item['Nr. Ped'],
        cliente: item['Cliente'],
        total: parsedTotal,
        vendedor: item['Vendedor'],
        data: dataISO,
        entrega_prod: entregaProdISO, // ✅ Pode ser null
        cod_cli: item['Cod. Cli.'] || null,
        descricao: item['Descrição'] || null,
        qtde: item['Qtde'] || null,
        preco_unit: item['Preco Unit'] || null
      };
    });
    
    console.log(`📦 Inserindo ${dataToInsert.length} registros...`);
    
    // Insere os dados
    const { error: insertError } = await supabase
      .from('pedidos_dia_data')
      .insert(dataToInsert);
    
    if (insertError) {
      console.error('❌ Erro ao inserir dados:', insertError);
      throw insertError;
    }
    
    console.log(`✅ ${requestData.length} pedidos importados com sucesso!`);
    
    return new Response(JSON.stringify({
      success: true,
      message: `${requestData.length} registros de pedidos do dia importados com sucesso!`,
      timestamp: now
    }), {
      status: 200,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
    
  } catch (error) {
    console.error('❌ Erro ao importar pedidos do dia:', error);
    return new Response(JSON.stringify({
      error: 'Erro ao processar dados',
      details: error.message
    }), {
      status: 500,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  }
});
