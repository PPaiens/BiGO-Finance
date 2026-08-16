import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Smart Finance AI",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializando histórico de gastos
if "historico_gastos" not in st.session_state:
    st.session_state.historico_gastos = pd.DataFrame(
        columns=["Data", "Estabelecimento", "Categoria", "Detalhe/Sub", "Valor (R$)", "Fixo"]
    )

# Inicializando histórico de cartões
if "historico_cartoes" not in st.session_state:
    st.session_state.historico_cartoes = pd.DataFrame(
        columns=["Cartão", "Descrição", "Valor Total (R$)", "Parcelas", "Classe/Categoria"]
    )

if "lista_cartoes_cadastrados" not in st.session_state:
    st.session_state.lista_cartoes_cadastrados = {}

# Inicializando portfólio de investimentos
if "portfolio_investimentos" not in st.session_state:
    st.session_state.portfolio_investimentos = pd.DataFrame(
        columns=["Ativo", "Quantidade", "Preço Médio Compra"]
    )

# Inicializando o ganho/entrada mensal total editável (Padrão inicial: R$ 8.500,00)
if "renda_mensal" not in st.session_state:
    st.session_state.renda_mensal = 8500.00

# Metas mensais dinâmicas baseadas na renda atual (Proporções padrão)
GANHO_TOTAL = st.session_state.renda_mensal
METAS = {
    "Casa": GANHO_TOTAL * 0.30,          # 30%
    "Transporte": GANHO_TOTAL * 0.10,    # 10%
    "Investimentos": GANHO_TOTAL * 0.20, # 20%
    "Viagem": GANHO_TOTAL * 0.10,        # 10%
    "Lazer": GANHO_TOTAL * 0.10          # 10%
    # (Os 20% restantes formam a folga/saldo livre do mês)
}

# Estilo visual customizado e responsivo
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #161b22;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #30363d;
        min-height: 120px;
    }
    .stMetric label {
        font-size: 13px !important;
        white-space: normal !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        font-size: 22px !important;
        white-space: nowrap !important;
    }
    .card-box {
        background-color: #161b22;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #30363d;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Menu Lateral
with st.sidebar:
    st.image("https://img.icons8.com/color/96/stack-of-coins.png", width=60)
    st.title("Smart Finance")
    st.markdown("---")
    mes_selecionado = st.selectbox("Mês de Referência", ["Março/2026", "Fevereiro/2026", "Janeiro/2026"])
    st.markdown("---")
    
    # Campo para edição rápida da renda na barra lateral
    st.subheader("💵 Configurar Renda")
    nova_renda_sidebar = st.number_input("Entrada Mensal Total (R$):", min_value=0.0, value=st.session_state.renda_mensal, step=100.0)
    if nova_renda_sidebar != st.session_state.renda_mensal:
        st.session_state.renda_mensal = nova_renda_sidebar
        st.rerun()

    st.markdown("---")
    st.info("💡 *Dica:* Altere sua renda acima ou na aba de Visão Geral para recalcular todas as metas automaticamente.")

# Abas do Dashboard
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Visão Geral", "💸 Gastos", "💳 Cartões", "📈 Investimentos"])

with tab1:
    st.subheader(f"📊 Resumo Financeiro Completo - {mes_selecionado}")
    
    # Bloco para edição interativa da renda direto na Visão Geral
    with st.expander("⚙️ Editar Renda / Ganhos do Mês", expanded=False):
        col_ed_r1, col_ed_r2 = st.columns([2, 1])
        with col_ed_r1:
            renda_input_main = st.number_input("Valor Atualizado dos Ganhos Mensais (R$):", min_value=0.0, value=st.session_state.renda_mensal, step=100.0, key="input_renda_principal")
        with col_ed_r2:
            st.text("")
            st.text("")
            if st.button("Atualizar Renda 💰"):
                st.session_state.renda_mensal = renda_input_main
                st.success("Renda atualizada com sucesso!")
                st.rerun()

    # Consolidação de Gastos avulsos e Faturas de Cartão
    gastos_brutos = {}
    if not st.session_state.historico_gastos.empty:
        gastos_brutos = st.session_state.historico_gastos.groupby("Categoria")["Valor (R$)"].sum().to_dict()

    if not st.session_state.historico_cartoes.empty:
        for _, row_c in st.session_state.historico_cartoes.iterrows():
            cat_c = row_c["Classe/Categoria"]
            val_parcela = row_c["Valor Total (R$)"] / row_c["Parcelas"]
            gastos_brutos[cat_c] = gastos_brutos.get(cat_c, 0.0) + val_parcela

    gastos_avulsos_mes = st.session_state.historico_gastos["Valor (R$)"].sum() if not st.session_state.historico_gastos.empty else 0.0
    total_cartoes_mes = sum([row_c["Valor Total (R$)"] / row_c["Parcelas"] for _, row_c in st.session_state.historico_cartoes.iterrows()]) if not st.session_state.historico_cartoes.empty else 0.0

    total_saidas_mes = gastos_avulsos_mes + total_cartoes_mes
    saldo_mes = st.session_state.renda_mensal - total_saidas_mes

    # Cálculo do Crédito Global
    limite_total_geral = sum(st.session_state.lista_cartoes_cadastrados.values()) if st.session_state.lista_cartoes_cadastrados else 0.0
    total_comprometido_geral = 0.0
    if not st.session_state.historico_cartoes.empty:
        for _, row_c in st.session_state.historico_cartoes.iterrows():
            total_comprometido_geral += row_c["Valor Total (R$)"]
    limite_disponivel_geral = limite_total_geral - total_comprometido_geral

    # Métricas Principais
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Entradas (Ganhos)", f"R$ {st.session_state.renda_mensal:,.2f}", "Renda configurada")
    col2.metric("Saídas Totais", f"R$ {total_saidas_mes:,.2f}", "Gastos + Faturas")
    col3.metric("Saldo do Mês", f"R$ {saldo_mes:,.2f}", "Saudável 🟢" if saldo_mes >= 0 else "Atenção 🔴")
    col4.metric("Crédito Disponível", f"R$ {limite_disponivel_geral:,.2f}", f"Tot: R$ {limite_total_geral:,.2f}")
    
    st.markdown("---")
    
    # Seção Gráfica e Visual (Raio-X)
    st.subheader("📊 Raio-X Visual do Orçamento")
    graf_col1, graf_col2 = st.columns(2)
    
    dados_grafico = []
    for cat, meta in METAS.items():
        gasto_real = gastos_brutos.get(cat, 0.0)
        dados_grafico.append({"Categoria": cat, "Tipo": "Planejado (Meta)", "Valor (R$)": meta})
        dados_grafico.append({"Categoria": cat, "Tipo": "Gasto Real", "Valor (R$)": gasto_real})
    
    df_comparativo = pd.DataFrame(dados_grafico)
    
    with graf_col1:
        st.write("*Metas vs. Gastos Reais (Gráfico de Barras)*")
        if not df_comparativo.empty:
            fig_bar = px.bar(
                df_comparativo, 
                x="Categoria", 
                y="Valor (R$)", 
                color="Tipo", 
                barmode="group",
                color_discrete_map={"Planejado (Meta)": "#2b5c8f", "Gasto Real": "#ff4b4b"},
                template="plotly_dark"
            )
            fig_bar.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Sem dados suficientes para o gráfico.")

    with graf_col2:
        st.write("*Distribuição dos Gastos por Categoria (Gráfico de Pizza)*")
        dados_pizza = [{"Categoria": cat, "Valor (R$)": val} for cat, val in gastos_brutos.items() if val > 0]
        df_pizza = pd.DataFrame(dados_pizza)
        
        if not df_pizza.empty:
            fig_pie = px.pie(
                df_pizza, 
                names="Categoria", 
                values="Valor (R$)", 
                hole=0.4,
                template="plotly_dark"
            )
            fig_pie.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Nenhum gasto registrado neste mês para gerar o gráfico de pizza.")

    st.markdown("---")
    
    # --- RESUMO DINÂMICO DE INVESTIMENTOS ---
    st.subheader("📈 Resumo Dinâmico da Carteira")
    
    if not st.session_state.portfolio_investimentos.empty:
        df_temp = st.session_state.portfolio_investimentos.copy()
        df_temp["Valor Total"] = df_temp["Quantidade"] * df_temp["Preço Médio Compra"]
        total_resumo = df_temp["Valor Total"].sum()
        
        col_i1, col_i2, col_i3 = st.columns(3)
        col_i1.metric("Patrimônio Investido", f"R$ {total_resumo:,.2f}")
        col_i2.metric("Ativos Cadastrados", f"{len(df_temp)}")
        col_i3.success("Painel conectado aos seus ativos.")
    else:
        st.info("Nenhum investimento cadastrado. Vá até a aba **Investimentos** para adicionar seus ativos.")

    st.markdown("---")

    # --- INTELIGÊNCIA DE GESTÃO FINANCEIRA COM CONSELHOS DINÂMICOS ---
    st.subheader("🧠 Inteligência de Gestão Financeira & Análise de Gastos")
    
    dicas_ia = []
    if saldo_mes < 0:
        dicas_ia.append(("🔴 Alerta Vermelho", f"Suas saídas ultrapassaram suas entradas em R$ {abs(saldo_mes):,.2f}. O uso excessivo do cartão está comprometendo seu mês."))
    elif saldo_mes < (st.session_state.renda_mensal * 0.15):
        dicas_ia.append(("⚠️ Alerta de Margem Baixa", "Seu saldo livre está apertado em relação à sua renda total."))
    else:
        dicas_ia.append(("🟢 Comportamento Saudável", "Excelente controle! Seu fluxo de caixa está positivo."))

    for cat, meta in METAS.items():
        gasto_cat = gastos_brutos.get(cat, 0.0)
        if gasto_cat > meta:
            excedente = gasto_cat - meta
            dicas_ia.append(("💡 Conselho de Ajuste", f"Você gastou R$ {excedente:,.2f} a mais do que o planejado na categoria **{cat}**."))

    for titulo, mensagem in dicas_ia:
        if "🔴" in titulo or "⚠️" in titulo:
            st.warning(f"**{titulo}:** {mensagem}")
        elif "🟢" in titulo:
            st.success(f"**{titulo}:** {mensagem}")
        else:
            st.info(f"**{titulo}:** {mensagem}")

with tab2:
    st.subheader("💸 Lançamento de Gastos & Metas por Categoria")
    
    with st.form(key="form_gasto", clear_on_submit=True):
        col_n1, col_n2 = st.columns(2)
        
        with col_n1:
            categoria_gasto = st.selectbox(
                "Selecione a Categoria:",
                ["Casa", "Transporte", "Lazer", "Viagem", "Investimentos", "Outros"]
            )
            
            sub_viagem = "Normal"
            if categoria_gasto == "Viagem":
                sub_viagem = st.selectbox(
                    "Classificação da Viagem:",
                    ["Sem dinheiro para viajar (Imprevisto/Corte)", "Com imprevisto (Gasto extra)"]
                )
                
        with col_n2:
            valor_gasto = st.number_input("Valor da Compra (R$):", min_value=0.0, value=150.00, step=10.0)
            detalhe_gasto = st.text_input("Descrição / Estabelecimento:", value="")
            
            submitted = st.form_submit_button("Confirmar e Registrar Gasto 🚀", type="primary")
            if submitted:
                novo_dado = {
                    "Data": pd.Timestamp.today().strftime("%d/%m/%Y"),
                    "Estabelecimento": detalhe_gasto if detalhe_gasto.strip() else "Gasto Diversos",
                    "Categoria": categoria_gasto,
                    "Detalhe/Sub": sub_viagem if categoria_gasto == "Viagem" else "-",
                    "Valor (R$)": valor_gasto,
                    "Fixo": False
                }
                st.session_state.historico_gastos = pd.concat(
                    [st.session_state.historico_gastos, pd.DataFrame([novo_dado])], 
                    ignore_index=True
                )
                st.success("Gasto registrado com sucesso!")
                st.rerun()

    st.markdown("---")
    
    excedente_outras_g = 0.0
    for cat, meta in METAS.items():
        if cat != "Viagem":
            gasto_cat = gastos_brutos.get(cat, 0.0)
            if gasto_cat > meta:
                excedente_outras_g += (gasto_cat - meta)

    st.subheader("📊 Acompanhamento de Metas vs. Gastos Reais (Detalhado)")
    for cat, meta in METAS.items():
        gasto_atual = gastos_brutos.get(cat, 0.0)
        
        if cat == "Viagem":
            gasto_total_viagem = gasto_atual + excedente_outras_g
            progresso = min(gasto_total_viagem / meta, 1.0) if meta > 0 else 0
            
            col_m1, col_m2 = st.columns([3, 1])
            with col_m1:
                if excedente_outras_g > 0:
                    st.text(f"✈️ {cat} (Base: R$ {gasto_atual:.2f} + Imprevistos de outras áreas: R$ {excedente_outras_g:.2f}) / Meta R$ {meta:.2f}")
                else:
                    st.text(f"✈️ {cat}: Gasto Atual R$ {gasto_atual:.2f} / Meta R$ {meta:.2f}")
                st.progress(progresso)
            with col_m2:
                if gasto_total_viagem > meta:
                    st.error(f"Estourou R$ {gasto_total_viagem - meta:.2f}! ⚠️")
                else:
                    sobra_viagem = meta - gasto_total_viagem
                    st.success(f"Sobra p/ Fundo: R$ {sobra_viagem:.2f} 🟢")
        else:
            progresso = min(gasto_atual / meta, 1.0) if meta > 0 else 0
            excedente_destE = gasto_atual - meta if gasto_atual > meta else 0.0
            
            col_m1, col_m2 = st.columns([3, 1])
            with col_m1:
                st.text(f"{cat}: Gasto R$ {gasto_atual:.2f} / Meta R$ {meta:.2f}")
                st.progress(progresso)
            with col_m2:
                if excedente_destE > 0:
                    st.markdown(f"<span style='color: #ff4b4b; font-weight: bold;'>Excedente: +R$ {excedente_destE:.2f} ⚠️</span>", unsafe_allow_html=True)
                else:
                    st.warning(f"Resta R$ {meta - gasto_atual:.2f} 🟢")

    st.markdown("---")
    
    st.subheader("📜 Gerenciamento de Lançamentos Recentes")
    if not st.session_state.historico_gastos.empty:
        for idx, row in st.session_state.historico_gastos.iterrows():
            c1, c2, c3, c4, c5, c6, c7 = st.columns([1.1, 2.3, 1.6, 2.0, 1.1, 1.2, 0.6])
            
            is_fixo = row.get("Fixo", False)

            with c1:
                st.text(row["Data"])
            with c2:
                prefixo_fixo = "📌 " if is_fixo else ""
                st.text(prefixo_fixo + row["Estabelecimento"])
            with c3:
                st.text(f"R$ {row['Valor (R$)']:.2f}")
            with c4:
                opcoes_cat = ["Casa", "Transporte", "Lazer", "Viagem", "Investimentos", "Outros"]
                cat_atual_idx = opcoes_cat.index(row["Categoria"]) if row["Categoria"] in opcoes_cat else 0
                nova_categoria = st.selectbox("Categoria", opcoes_cat, index=cat_atual_idx, key=f"cat_{idx}", label_visibility="collapsed")
                if nova_categoria != row["Categoria"]:
                    st.session_state.historico_gastos.at[idx, "Categoria"] = nova_categoria
                    st.rerun()
            with c5:
                st.text(row["Detalhe/Sub"])
            with c6:
                novo_estado_fixo = st.checkbox("Fixar 📌", value=is_fixo, key=f"fix_{idx}")
                if novo_estado_fixo != is_fixo:
                    st.session_state.historico_gastos.at[idx, "Fixo"] = novo_estado_fixo
                    st.rerun()
            with c7:
                if st.button("🗑️", key=f"del_{idx}", help="Apagar este gasto"):
                    st.session_state.historico_gastos = st.session_state.historico_gastos.drop(idx).reset_index(drop=True)
                    st.rerun()
    else:
        st.info("Nenhum gasto registrado ainda. Use o formulário acima para adicionar.")

with tab3:
    st.subheader("💳 Gestão de Múltiplos Cartões & Limites de Crédito")
    
    with st.expander("⚙️ Gerenciar / Cadastrar Cartões (Definir Limites Individuais)", expanded=True):
        col_cad1, col_cad2, col_cad3 = st.columns([2, 2, 1])
        with col_cad1:
            novo_nome_cartao = st.text_input("Nome do Cartão (ex: Nubank, Itaú):", value="")
        with col_cad2:
            novo_limite_cartao = st.number_input("Limite Individual (R$):", min_value=0.0, value=1000.00, step=500.0)
        with col_cad3:
            st.text("")
            st.text("")
            if st.button("Adicionar Cartão 💳"):
                if novo_nome_cartao.strip():
                    st.session_state.lista_cartoes_cadastrados[novo_nome_cartao.strip()] = novo_limite_cartao
                    st.success(f"Cartão {novo_nome_cartao} adicionado com sucesso!")
                    st.rerun()

    # Métricas Globais de Crédito
    limite_total_global = sum(st.session_state.lista_cartoes_cadastrados.values()) if st.session_state.lista_cartoes_cadastrados else 0.0
    
    comprometido_por_cartao = {cartao: 0.0 for cartao in st.session_state.lista_cartoes_cadastrados.keys()}
    total_fatura_mensal_global = 0.0
    total_comprometido_global = 0.0

    if not st.session_state.historico_cartoes.empty:
        for _, row_c in st.session_state.historico_cartoes.iterrows():
            c_nome = row_c["Cartão"]
            v_tot = row_c["Valor Total (R$)"]
            v_parc = v_tot / row_c["Parcelas"]
            
            total_fatura_mensal_global += v_parc
            total_comprometido_global += v_tot
            if c_nome in comprometido_por_cartao:
                comprometido_por_cartao[c_nome] += v_tot

    limite_disponivel_global = limite_total_global - total_comprometido_global

    col_l1, col_l2, col_l3 = st.columns(3)
    col_l1.metric("Limite Total Consolidado", f"R$ {limite_total_global:,.2f}", f"{len(st.session_state.lista_cartoes_cadastrados)} cartões ativos")
    col_l2.metric("Fatura Atual Consolidada", f"R$ {total_fatura_mensal_global:,.2f}", "Soma das parcelas mensais")
    col_l3.metric("Limite Disponível Geral", f"R$ {limite_disponivel_global:,.2f}", "Livre para novas compras 🟢" if limite_disponivel_global >= 0 else "Estourado 🔴")
    
    porcentagem_uso_global = min(total_comprometido_global / limite_total_global, 1.0) if limite_total_global > 0 else 0
    st.progress(porcentagem_uso_global, text=f"Uso do Limite Global: {porcentagem_uso_global*100:.1f}%")

    st.markdown("#### 🔍 Situação Individual por Cartão:")
    
    if len(st.session_state.lista_cartoes_cadastrados) > 0:
        cartao_cols = st.columns(len(st.session_state.lista_cartoes_cadastrados))
        for idx_ct, (nome_c, lim_c) in enumerate(st.session_state.lista_cartoes_cadastrados.items()):
            comp_c = comprometido_por_cartao.get(nome_c, 0.0)
            disp_c = lim_c - comp_c
            porcentagem_c = min(comp_c / lim_c, 1.0) if lim_c > 0 else 0
            
            with cartao_cols[idx_ct]:
                with st.container():
                    st.markdown(f"*💳 {nome_c}*")
                    st.text(f"Limite: R$ {lim_c:,.2f}")
                    st.text(f"Comprometido: R$ {comp_c:,.2f}")
                    st.progress(porcentagem_c, text=f"Uso: {porcentagem_c*100:.1f}%")
                    if disp_c >= 0:
                        st.success(f"Disponível: R$ {disp_c:,.2f} 🟢")
                    else:
                        st.error(f"Estourado: R$ {abs(disp_c):,.2f} 🔴")
    else:
        st.info("Nenhum cartão cadastrado. Cadastre acima para visualizar os limites individuais.")

    st.markdown("---")
    
    st.subheader("➕ Adicionar Nova Compra Parcelada no Cartão")
    if len(st.session_state.lista_cartoes_cadastrados) > 0:
        with st.form(key="form_cartao", clear_on_submit=True):
            col_c1, col_c2 = st.columns(2)
            
            with col_c1:
                cartao_selecionado = st.selectbox("Selecione o Cartão:", list(st.session_state.lista_cartoes_cadastrados.keys()))
                desc_cartao = st.text_input("Descrição / Estabelecimento:", value="")
                
            with col_c2:
                valor_total_cartao = st.number_input("Valor Total da Compra (R$):", min_value=0.0, value=500.00, step=50.0)
                num_parcelas = st.number_input("Número de Parcelas:", min_value=1, max_value=24, value=5, step=1)
                classe_cartao = st.selectbox("Classe / Categoria do Gasto:", ["Casa", "Transporte", "Lazer", "Viagem", "Investimentos", "Outros"], key="cat_cartao_input")
                
            btn_add_cartao = st.form_submit_button("Cadastrar Compra Parcelada 💳", type="primary")
            if btn_add_cartao:
                novo_cartao = {
                    "Cartão": cartao_selecionado,
                    "Descrição": desc_cartao if desc_cartao.strip() else "Compra Parcelada",
                    "Valor Total (R$)": valor_total_cartao,
                    "Parcelas": int(num_parcelas),
                    "Classe/Categoria": classe_cartao
                }
                st.session_state.historico_cartoes = pd.concat(
                    [st.session_state.historico_cartoes, pd.DataFrame([novo_cartao])], 
                    ignore_index=True
                )
                st.success("Compra parcelada cadastrada com sucesso!")
                st.rerun()
    else:
        st.warning("Cadastre pelo menos um cartão acima antes de registrar compras parceladas.")

    st.markdown("---")
    
    st.subheader("📜 Histórico de Parcelamentos Registrados")
    if not st.session_state.historico_cartoes.empty:
        for idx_c, row_c in st.session_state.historico_cartoes.iterrows():
            valor_parcela_calc = row_c["Valor Total (R$)"] / row_c["Parcelas"]
            
            cc1, cc2, cc3, cc4, cc5, cc6, cc7 = st.columns([1.8, 2.2, 1.8, 1.2, 1.4, 1.8, 0.8])
            
            with cc1:
                st.text(row_c["Cartão"])
            with cc2:
                st.text(row_c["Descrição"])
            with cc3:
                st.text(f"Tot: R$ {row_c['Valor Total (R$)']:.2f}")
            with cc4:
                st.text(f"{row_c['Parcelas']}x")
            with cc5:
                st.text(f"R$ {valor_parcela_calc:.2f}/mês")
            with cc6:
                st.text(row_c["Classe/Categoria"])
            with cc7:
                if st.button("🗑️", key=f"del_cartao_{idx_c}", help="Apagar este parcelamento"):
                    st.session_state.historico_cartoes = st.session_state.historico_cartoes.drop(idx_c).reset_index(drop=True)
                    st.rerun()
    else:
        st.info("Nenhum parcelamento de cartão registrado.")

with tab4:
    st.subheader("📈 Gestão da Carteira de Investimentos")
    st.write("Adicione seus ativos (ex: PETR4.SA, VALE3.SA, IVVB11.SA) para acompanhar cotações reais da bolsa:")

    with st.form(key="form_ativo", clear_on_submit=True):
        col_inv_a, col_inv_b, col_inv_c, col_inv_d = st.columns([2, 1.5, 1.5, 1])
        with col_inv_a:
            ticker_input = st.text_input("Ticker do Ativo (ex: PETR4.SA):", value="")
        with col_inv_b:
            qtd_input = st.number_input("Quantidade:", min_value=1, value=10, step=1)
        with col_inv_c:
            preco_medio_input = st.number_input("Preço Médio de Compra (R$):", min_value=0.0, value=30.00, step=1.0)
        with col_inv_d:
            st.text("")
            st.text("")
            btn_add_ativo = st.form_submit_button("Adicionar Ativo 📈")
            
        if btn_add_ativo:
            if ticker_input.strip():
                novo_ativo_df = pd.DataFrame([{
                    "Ativo": ticker_input.strip().upper(),
                    "Quantidade": int(qtd_input),
                    "Preço Médio Compra": float(preco_medio_input)
                }])
                st.session_state.portfolio_investimentos = pd.concat(
                    [st.session_state.portfolio_investimentos, novo_ativo_df],
                    ignore_index=True
                )
                st.success("Ativo adicionado com sucesso!")
                st.rerun()

    st.markdown("---")

    if not st.session_state.portfolio_investimentos.empty:
        df_portfolio = st.session_state.portfolio_investimentos.copy()
        precos_atuais = []
        
        for ticker in df_portfolio["Ativo"]:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d")
                preco = hist['Close'].iloc[-1] if not hist.empty else df_portfolio.loc[df_portfolio["Ativo"] == ticker, "Preço Médio Compra"].values[0]
            except:
                preco = df_portfolio.loc[df_portfolio["Ativo"] == ticker, "Preço Médio Compra"].values[0]
            precos_atuais.append(preco)

        df_portfolio["Preço Atual"] = precos_atuais
        df_portfolio["Valor Total"] = df_portfolio["Quantidade"] * df_portfolio["Preço Atual"]
        df_portfolio["Lucro / Prejuízo (R$)"] = df_portfolio["Quantidade"] * (df_portfolio["Preço Atual"] - df_portfolio["Preço Médio Compra"])
        df_portfolio["Rentabilidade (%)"] = ((df_portfolio["Preço Atual"] / df_portfolio["Preço Médio Compra"]) - 1) * 100

        st.dataframe(
            df_portfolio.style.format({
                "Preço Médio Compra": "R$ {:.2f}",
                "Preço Atual": "R$ {:.2f}",
                "Valor Total": "R$ {:.2f}",
                "Lucro / Prejuízo (R$)": "R$ {:.2f}",
                "Rentabilidade (%)": "{:.2f}%"
            }),
            use_container_width=True
        )

        patrimonio_atual_carteira = df_portfolio["Valor Total"].sum()
        lucro_total_carteira = df_portfolio["Lucro / Prejuízo (R$)"].sum()
        
        col_inv1, col_inv2 = st.columns(2)
        col_inv1.metric("Patrimônio Atual na Bolsa", f"R$ {patrimonio_atual_carteira:,.2f}", f"R$ {lucro_total_carteira:+,.2f} total")
        
        if st.button("🗑️ Limpar Todos os Investimentos"):
            st.session_state.portfolio_investimentos = pd.DataFrame(columns=["Ativo", "Quantidade", "Preço Médio Compra"])
            st.rerun()
    else:
        st.info("Nenhum ativo cadastrado na carteira. Utilize o formulário acima para inserir suas ações ou ETFs.")