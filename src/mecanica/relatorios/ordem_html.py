"""HTML service order report generator."""

import os
import tempfile
import webbrowser


def gerar_html(dados: dict) -> str:
    veiculo = dados.get("veiculo", "")
    ano     = dados.get("ano", "")
    placa   = dados.get("placa", "")
    data    = dados.get("data", "")
    cliente = dados.get("cliente", "")
    fone    = dados.get("fone", "")
    total   = dados.get("total", "0.00")
    linhas  = dados.get("linhas", [])

    MIN_ROWS = 9
    linhas_validas = [
        (qtd, disc, unit, tot)
        for qtd, disc, unit, tot in linhas
        if any(str(v).strip() for v in (qtd, disc, unit, tot))
    ]
    # Pad with empty rows up to the minimum so the table always looks full
    while len(linhas_validas) < MIN_ROWS:
        linhas_validas.append(("", "", "", ""))

    linhas_html = "".join(
        f"""<tr>
            <td class="col-qtd">{qtd}</td>
            <td class="col-disc">{disc}</td>
            <td class="col-unit">{unit}</td>
            <td class="col-tot">{tot}</td>
        </tr>"""
        for qtd, disc, unit, tot in linhas_validas
    )

    def bloco_os() -> str:
        return f"""
        <div class="os-box">
            <div class="header">
                <div class="logo-area">
                    <div class="logo-icon">🔧</div>
                    <div class="logo-text">MECÂNICA SP</div>
                </div>
                <div class="header-info">
                    <div class="header-servicos">Motor, suspensão, freio, injeção eletrônica, mecânica em geral</div>
                    <div class="header-contato">📞 (45) 99915-4797</div>
                    <div class="header-contato">✉ mecanicasp7@gmail.com</div>
                    <div class="header-contato">📍 Rua Tereza Barbieri - 320, Alto Panorama - Toledo/PR</div>
                </div>
            </div>
            <div class="titulo">Ordem de Serviço</div>
            <div class="campos-topo">
                <div class="campo-linha">
                    <span class="campo-lbl">Veículo:</span>
                    <span class="campo-val flex2">{veiculo}</span>
                    <span class="campo-lbl ml">Ano:</span>
                    <span class="campo-val">{ano}</span>
                </div>
                <div class="campo-linha">
                    <span class="campo-lbl">Placa:</span>
                    <span class="campo-val flex2">{placa}</span>
                    <span class="campo-lbl ml">Data:</span>
                    <span class="campo-val">{data}</span>
                </div>
                <div class="campo-linha">
                    <span class="campo-lbl">Cliente:</span>
                    <span class="campo-val flex2">{cliente}</span>
                    <span class="campo-lbl ml">Fone:</span>
                    <span class="campo-val">{fone}</span>
                </div>
            </div>
            <div class="table-wrapper">
            <table class="tabela-itens">
                <thead>
                    <tr>
                        <th class="col-qtd">Quant.</th>
                        <th class="col-disc">Descrição</th>
                        <th class="col-unit">P. Unitário</th>
                        <th class="col-tot">TOTAL</th>
                    </tr>
                </thead>
                <tbody>{linhas_html}</tbody>
            </table>
            </div>
            <div class="rodape-total">
                <span>TOTAL</span>
                <span class="total-val">R$ {total}</span>
            </div>
            <div class="assinatura">
                <span>Assinatura: ___________________________________</span>
            </div>
            <div class="aviso">
                <strong>ORÇAMENTO SUJEITO À ALTERAÇÃO DE VALORES</strong><br>
                Pode haver acréscimo de peças ou mão de obra, se necessário ou em caso de defeito oculto no veículo.
            </div>
        </div>"""

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  @page{{size:A4 landscape;margin:6mm}}
  html,body{{height:100%;overflow:hidden}}
  body{{width:100%;display:flex;flex-direction:row;gap:6mm;
        font-family:Arial,sans-serif;font-size:9.5pt;background:white}}
  .os-box{{flex:1;height:100%;border:1.5px solid #333;display:flex;
           flex-direction:column;padding:3mm;overflow:hidden}}
  .header{{display:flex;align-items:center;border-bottom:1.5px solid #333;
           padding-bottom:2mm;margin-bottom:1.5mm;gap:3mm}}
  .logo-area{{display:flex;flex-direction:column;align-items:center;min-width:32mm}}
  .logo-icon{{font-size:22pt;line-height:1}}
  .logo-text{{font-size:13pt;font-weight:900;color:#1a6b3a}}
  .header-info{{flex:1}}
  .header-servicos{{font-size:0.72em;color:#444;margin-bottom:1mm;font-style:italic}}
  .header-contato{{font-size:0.78em;color:#222;line-height:1.5}}
  .titulo{{text-align:center;font-size:1.15em;font-weight:bold;border:1px solid #333;
           padding:1mm 0;margin-bottom:1.5mm;letter-spacing:1px}}
  .campos-topo{{margin-bottom:1.5mm}}
  .campo-linha{{display:flex;align-items:baseline;border-bottom:0.5px solid #bbb;
               padding:0.8mm 0;gap:1mm}}
  .campo-lbl{{font-weight:bold;white-space:nowrap;font-size:0.82em}}
  .campo-val{{border-bottom:0.8px solid #555;min-width:20mm;font-size:0.88em}}
  .flex2{{flex:2}}.ml{{margin-left:2mm}}
  .table-wrapper{{flex:1;overflow:hidden;min-height:0}}
  .tabela-itens{{width:100%;height:100%;border-collapse:collapse;table-layout:fixed;font-size:0.88em}}
  .tabela-itens thead tr{{background:#1E7A48;color:white}}
  .tabela-itens th,.tabela-itens td{{border:0.5px solid #999;padding:0 1mm;text-align:center;
                                      vertical-align:middle;overflow:hidden;white-space:nowrap}}
  .tabela-itens td.col-disc{{text-align:left;padding-left:1.5mm}}
  .tabela-itens tbody tr:nth-child(even){{background:#f7f9f7}}
  .col-qtd{{width:10mm}}.col-unit{{width:24mm}}.col-tot{{width:22mm}}
  .rodape-total{{display:flex;justify-content:flex-end;align-items:center;gap:3mm;
                border:1px solid #333;padding:1mm 2mm;margin-top:1mm;
                font-weight:bold;font-size:1em}}
  .total-val{{border-bottom:1px solid #333;min-width:25mm;text-align:right;font-size:1.1em}}
  .assinatura{{margin-top:1.5mm;padding-top:1mm;border-top:0.5px solid #aaa;font-size:0.82em}}
  .aviso{{margin-top:1.5mm;font-size:0.65em;color:#333;border-top:0.8px solid #aaa;
          padding-top:1mm;line-height:1.4}}
  .aviso strong{{text-decoration:underline}}
</style></head><body>
{bloco_os()}{bloco_os()}
<script>
  document.querySelectorAll('.os-box').forEach(function(box) {{
    // 1. Shrink font until box content fits (min 5.5pt)
    var MIN_PT = 5.5;
    var pxPerPt = 96 / 72;
    var fs = parseFloat(window.getComputedStyle(box).fontSize);
    while (box.scrollHeight > box.clientHeight + 1 && fs / pxPerPt > MIN_PT) {{
      fs -= 0.4;
      box.style.fontSize = fs + 'px';
    }}
    // 2. Distribute wrapper height equally across all rows
    var wrapper = box.querySelector('.table-wrapper');
    var table   = box.querySelector('.tabela-itens');
    if (wrapper && table) {{
      var rows  = table.querySelectorAll('tr');
      var rowH  = Math.floor(wrapper.clientHeight / rows.length);
      rows.forEach(function(r) {{ r.style.height = rowH + 'px'; }});
    }}
  }});
  setTimeout(function(){{ window.print(); }}, 120);
</script>
</body></html>"""


def abrir_impressao(dados: dict) -> None:
    html = gerar_html(dados)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8")
    tmp.write(html)
    tmp.close()
    webbrowser.open(f"file:///{tmp.name.replace(os.sep, '/')}")
