"""Dashboard – Anuário Estatístico do Mercado Farmacêutico Brasileiro 2024 (CMED/ANVISA)."""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
import dados

st.set_page_config(page_title="Mercado Farmacêutico 2024", page_icon="💊", layout="wide")

# ---------- estilo ----------
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
AZUL = "#2a78d6"
# Cor segue a entidade (ordem fixa da paleta validada), nunca o ranking
COR = {
    "Biológico": "#2a78d6", "Novo": "#eb6834", "Genérico": "#1baf7a", "Similar": "#eda100",
    "Específico": "#e87ba4", "Fitoterápico": "#008300", "Outros": "#8a8984", "Total": "#52514e",
    "Liberado": "#2a78d6", "Regulado": "#eb6834",
    "Distribuidor": "#2a78d6", "Farmácias e drogarias": "#eb6834", "Governo": "#1baf7a",
    "Estab. privado de saúde": "#eda100", "Outros (não privados)": "#e87ba4",
}
SEQ = ["#d6e6f9", "#9cc4ee", "#5b9ae0", "#2a78d6", "#1a56a0"]

st.markdown(
    """
<style>
.block-container {padding-top: 2.2rem; max-width: 1280px;}
[data-testid="stMetric"] {background:#f6f5f2; border:1px solid #e4e3df; border-radius:10px; padding:14px 16px;}
[data-testid="stMetricLabel"] p {font-size:0.8rem; color:#52514e;}
[data-testid="stMetricValue"] {font-size:1.3rem;}
h1 {font-size:1.9rem !important;} h2, h3 {font-weight:600 !important;}
.nota {color:#52514e; font-size:0.85rem;}
</style>""",
    unsafe_allow_html=True,
)


def estilo(fig, h=380, legenda=True, titulo=None):
    fig.update_layout(
        template="plotly_white", height=h, margin=dict(l=8, r=8, t=(78 if legenda else 44) if titulo else (40 if legenda else 12), b=8),
        title=dict(text=titulo, font=dict(size=15, color=INK), x=0, y=0.98, yanchor="top") if titulo else None,
        font=dict(color=INK2, size=12), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=legenda, legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0, xanchor="left", title=None),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, title=None)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, title=None)
    return fig


def mostrar(fig, **kw):
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False}, **kw)


def brl(v, casas=1):
    if pd.isna(v):
        return "–"
    if abs(v) >= 1e9:
        return f"R$ {v/1e9:,.{casas}f} bi".replace(",", "X").replace(".", ",").replace("X", ".")
    if abs(v) >= 1e6:
        return f"R$ {v/1e6:,.{casas}f} mi".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def num(v, casas=0):
    if pd.isna(v):
        return "–"
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def qtd(v):
    if v >= 1e9:
        return num(v / 1e9, 2) + " bi"
    if v >= 1e6:
        return num(v / 1e6, 1) + " mi"
    return num(v)


def add_bi(df):
    df = df.copy()
    df["Faturamento (R$ bi)"] = df["Faturamento"] / 1e9
    df["Qtd (milhões)"] = df["Qtd comercializada"] / 1e6
    return df


def ordenar_faixa(df, col):
    df = df[df[col] != "Total"].copy()
    df["_o"] = dados.ordem_faixa(df[col])
    return df.sort_values("_o").drop(columns="_o")


def tabela_fmt(df, ocultar=()):
    df = df.drop(columns=[c for c in ocultar if c in df.columns]).copy()
    cfg = {}
    for c in df.columns:
        if c == "Faturamento":
            cfg[c] = st.column_config.NumberColumn("Faturamento (R$)", format="localized")
        elif pd.api.types.is_float_dtype(df[c]):
            cfg[c] = st.column_config.NumberColumn(c, format="%.2f")
    st.dataframe(df, width="stretch", hide_index=True, column_config=cfg)


@st.cache_data(show_spinner="Lendo planilha…")
def carregar():
    return dados.carregar()


D = carregar()

# ---------- navegação ----------
st.sidebar.title("💊 Mercado Farmacêutico")
st.sidebar.caption("Anuário Estatístico CMED/ANVISA · ano-base 2024")
PAGINAS = [
    "Visão geral", "Canais de distribuição", "Faixas de preço", "Classes terapêuticas",
    "Princípios ativos", "Idade e composição", "Regime de preço (MIP × regulado)", "Empresas e concentração",
]
pag = st.sidebar.radio("Seção", PAGINAS, label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.caption(
    "Fonte: CMED/ANVISA – Relatório de Comercialização enviado pelas empresas. "
    "Dados processados em julho/2025. Valores marcados com ** na planilha (sigilo estatístico) aparecem como vazios."
)

# =====================================================================
if pag == "Visão geral":
    st.title("Mercado farmacêutico brasileiro em 2024")
    t = D["t11"]
    tot = t[t["Tipo de Registro Sanitário"] == "Total"].iloc[0]
    c = st.columns(6)
    c[0].metric("Faturamento", brl(tot["Faturamento"]))
    c[1].metric("Unidades vendidas", qtd(tot["Qtd comercializada"]))
    c[2].metric("Empresas", num(tot["Empresas"]))
    c[3].metric("Produtos", num(tot["Produtos"]))
    c[4].metric("Apresentações", num(tot["Apresentações"]))
    c[5].metric("Princípios ativos", num(tot["Princípios ativos"]))
    st.caption(f"Preço médio praticado: **{brl(tot['Preço médio'], 2)}** por unidade · "
               f"mediana por apresentação: **{brl(tot['Mediana preço'], 2)}**".replace("$", "\\$"))

    tt = add_bi(t[~t["Tipo de Registro Sanitário"].isin(["Total"])])
    col1, col2 = st.columns(2)
    with col1:
        d = tt.sort_values("Faturamento (R$ bi)")
        fig = px.bar(d, x="Faturamento (R$ bi)", y="Tipo de Registro Sanitário", orientation="h",
                     color="Tipo de Registro Sanitário", color_discrete_map=COR,
                     text=d["Faturamento (R$ bi)"].map(lambda v: f"{v:,.1f}".replace(".", ",")))
        fig.update_traces(textposition="outside", cliponaxis=False)
        mostrar(estilo(fig, legenda=False, titulo="Faturamento por tipo de registro (R$ bilhões)"))
    with col2:
        base = tt[tt["Tipo de Registro Sanitário"] != "Outros"]
        share = pd.DataFrame({
            "Tipo de Registro Sanitário": base["Tipo de Registro Sanitário"].tolist() * 2,
            "Medida": ["Faturamento"] * len(base) + ["Unidades vendidas"] * len(base),
            "Participação (%)": list(base["Faturamento"] / base["Faturamento"].sum() * 100)
                                + list(base["Qtd comercializada"] / base["Qtd comercializada"].sum() * 100),
        })
        fig = px.bar(share, x="Participação (%)", y="Medida", color="Tipo de Registro Sanitário",
                     orientation="h", color_discrete_map=COR, text=share["Participação (%)"].map(
                         lambda v: f"{v:.0f}%" if v >= 5 else ""))
        fig.update_traces(marker_line_color="#fcfcfb", marker_line_width=2)
        fig.update_layout(barmode="stack")
        mostrar(estilo(fig, titulo="Quem fatura vs. quem vende volume (participação %)"))
        st.markdown('<p class="nota">Genéricos respondem por cerca de metade das unidades, mas por uma fatia '
                    'bem menor do faturamento; biológicos e novos fazem o inverso.</p>', unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        d = tt[tt["Tipo de Registro Sanitário"] != "Outros"].sort_values("Preço médio")
        fig = px.bar(d, x="Preço médio", y="Tipo de Registro Sanitário", orientation="h",
                     color="Tipo de Registro Sanitário", color_discrete_map=COR,
                     text=d["Preço médio"].map(lambda v: f"R$ {v:,.2f}".replace(".", ",")))
        fig.update_traces(textposition="outside", cliponaxis=False)
        mostrar(estilo(fig, legenda=False, titulo="Preço médio praticado por unidade (R$)"))
        st.markdown('<p class="nota">“Outros” (radiofármacos e terapia avançada) fica de fora por ter só '
                    '~1 mil unidades e preço unitário em milhares de reais.</p>', unsafe_allow_html=True)
    with col4:
        d = tt.melt(id_vars="Tipo de Registro Sanitário",
                    value_vars=["Empresas", "Produtos", "Apresentações", "Princípios ativos"],
                    var_name="Indicador", value_name="Quantidade")
        d = d[d["Tipo de Registro Sanitário"] != "Outros"]
        ind = st.selectbox("Indicador de oferta", ["Produtos", "Apresentações", "Princípios ativos", "Empresas"])
        d = d[d["Indicador"] == ind].sort_values("Quantidade")
        fig = px.bar(d, x="Quantidade", y="Tipo de Registro Sanitário", orientation="h",
                     color="Tipo de Registro Sanitário", color_discrete_map=COR, text="Quantidade")
        fig.update_traces(textposition="outside", cliponaxis=False)
        mostrar(estilo(fig, h=330, legenda=False, titulo=f"{ind} com comercialização, por tipo"))

    with st.expander("Ver tabela completa (Tabela 1.1)"):
        tabela_fmt(t)

# =====================================================================
elif pag == "Canais de distribuição":
    st.title("Canais de distribuição")
    t = D["t12"]
    t = t[t["Tipo de Canal"] != "Total"]
    tot = add_bi(t[t["Tipo de Registro Sanitário"] == "Total"])
    c = st.columns(len(tot))
    for i, (_, r) in enumerate(tot.iterrows()):
        c[i].metric(r["Tipo de Canal"], brl(r["Faturamento"]),
                    f"{r['Faturamento']/tot['Faturamento'].sum()*100:.1f}% do total", delta_color="off")
    col1, col2 = st.columns(2)
    with col1:
        d = tot.sort_values("Faturamento (R$ bi)")
        fig = px.bar(d, x="Faturamento (R$ bi)", y="Tipo de Canal", orientation="h", color="Tipo de Canal",
                     color_discrete_map=COR, text=d["Faturamento (R$ bi)"].map(lambda v: f"{v:,.1f}".replace(".", ",")))
        fig.update_traces(textposition="outside", cliponaxis=False)
        mostrar(estilo(fig, legenda=False, titulo="Faturamento por canal (R$ bilhões)"))
    with col2:
        d = tot.sort_values("Preço médio")
        fig = px.bar(d, x="Preço médio", y="Tipo de Canal", orientation="h", color="Tipo de Canal",
                     color_discrete_map=COR, text=d["Preço médio"].map(lambda v: f"R$ {v:,.2f}".replace(".", ",")))
        fig.update_traces(textposition="outside", cliponaxis=False)
        mostrar(estilo(fig, legenda=False, titulo="Preço médio praticado por unidade (R$)"))
    sub = add_bi(t[t["Tipo de Registro Sanitário"] != "Total"])
    medida = st.radio("Medida da composição", ["Faturamento", "Unidades vendidas"], horizontal=True)
    campo = "Faturamento" if medida == "Faturamento" else "Qtd comercializada"
    sub["pct"] = sub[campo] / sub.groupby("Tipo de Registro Sanitário")[campo].transform("sum") * 100
    sub = sub.dropna(subset=["pct"])
    fig = px.bar(sub, x="pct", y="Tipo de Registro Sanitário", color="Tipo de Canal", orientation="h",
                 color_discrete_map=COR, labels={"pct": "% do total do tipo"},
                 text=sub["pct"].map(lambda v: f"{v:.0f}%" if v >= 6 else ""))
    fig.update_traces(marker_line_color="#fcfcfb", marker_line_width=2)
    fig.update_layout(barmode="stack")
    mostrar(estilo(fig, h=420, titulo=f"Canal de venda dentro de cada tipo de registro ({medida.lower()}, %)"))
    with st.expander("Ver tabela completa (Tabela 1.2)"):
        tabela_fmt(t)

# =====================================================================
elif pag == "Faixas de preço":
    st.title("Faixas de preço")
    ref = st.radio("Critério", ["Preço teto (CMED)", "Preço praticado"], horizontal=True)
    t, col = (D["t13"], "Faixa de Preço Teto") if ref.startswith("Preço teto") else (D["t14"], "Faixa de Preço Praticado")
    tipos = [x for x in t["Tipo de Registro Sanitário"].unique()]
    tipo = st.selectbox("Tipo de registro", tipos, index=0)
    d = add_bi(ordenar_faixa(t[t["Tipo de Registro Sanitário"] == tipo], col))
    d["Faixa"] = d[col].str.replace(r"^\d+\.\s*", "", regex=True)
    if d["Faturamento"].isna().any():
        st.info("Algumas faixas não têm dados publicados (sigilo estatístico) e aparecem vazias.")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(d, x="Faixa", y="Faturamento (R$ bi)", color_discrete_sequence=[AZUL])
        mostrar(estilo(fig, legenda=False, titulo="Faturamento por faixa (R$ bilhões)"))
    with c2:
        fig = px.bar(d, x="Faixa", y="Qtd (milhões)", color_discrete_sequence=["#eb6834"])
        mostrar(estilo(fig, legenda=False, titulo="Unidades vendidas por faixa (milhões)"))
    c3, c4 = st.columns(2)
    with c3:
        fig = px.bar(d, x="Faixa", y="Produtos", color_discrete_sequence=[AZUL])
        mostrar(estilo(fig, legenda=False, titulo="Número de produtos por faixa"))
    with c4:
        fig = go.Figure()
        fig.add_scatter(x=d["Faixa"], y=d["Preço médio"], mode="lines+markers", name="Preço médio", line=dict(color=AZUL, width=2))
        fig.add_scatter(x=d["Faixa"], y=d["Mediana preço"], mode="lines+markers", name="Mediana", line=dict(color="#eb6834", width=2))
        fig.update_yaxes(type="log")
        mostrar(estilo(fig, titulo="Preço médio e mediana por faixa (R$, escala log)"))
    with st.expander("Ver tabela"):
        tabela_fmt(d.drop(columns=["Faixa", "Faturamento (R$ bi)", "Qtd (milhões)"]))

# =====================================================================
elif pag == "Classes terapêuticas":
    st.title("Classes terapêuticas")
    t = add_bi(D["t15"])
    t["Grupo"] = t["Grupo Anatômico (1)"].str.replace(r"\s+", " ", regex=True)
    metrica = st.selectbox("Métrica", ["Faturamento (R$ bi)", "Qtd (milhões)", "Preço médio", "Mediana preço", "Produtos",
                                       "Apresentações", "Princípios ativos", "Empresas"])
    d = t.sort_values(metrica)
    fig = px.bar(d, x=metrica, y="Grupo", orientation="h", color_discrete_sequence=[AZUL],
                 text=d[metrica].map(lambda v: f"{v:,.1f}".replace(".", ",")))
    fig.update_traces(textposition="outside", cliponaxis=False)
    mostrar(estilo(fig, h=560, legenda=False, titulo=f"{metrica} por grupo anatômico (ATC nível 1)"))
    st.markdown('<p class="nota">Preço médio de “M – músculo-esquelético” é distorcido por poucas apresentações '
                'de preço muito alto; prefira a mediana para comparar.</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        fig = px.scatter(t, x="Qtd (milhões)", y="Faturamento (R$ bi)", size="Produtos", text=t["Grupo"].str[0],
                         color_discrete_sequence=[AZUL], size_max=38, hover_name="Grupo")
        fig.update_traces(textposition="middle center", textfont=dict(color="white", size=11))
        mostrar(estilo(fig, legenda=False, titulo="Volume × faturamento (tamanho = nº de produtos)"))
    with c2:
        s = D["t16"].copy()
        s["Faixa"] = s["Faixa de Faturamento (R$)"]
        cont = ordenar_faixa(s.groupby("Faixa").size().reset_index(name="Subclasses"), "Faixa")
        cont["Faixa"] = cont["Faixa"].str.replace(r"^\d+\.\s*", "", regex=True)
        fig = px.bar(cont, x="Faixa", y="Subclasses", color_discrete_sequence=[AZUL])
        mostrar(estilo(fig, legenda=False, titulo="Subclasses terapêuticas por faixa de faturamento"))
    st.subheader("Subclasses terapêuticas (Tabela 1.6)")
    q = st.text_input("Buscar subclasse", placeholder="ex.: insulina, antibióticos…")
    s = D["t16"]
    if q:
        s = s[s["Subclasse Terapêutica"].str.contains(q, case=False, na=False)]
    st.dataframe(s, width="stretch", hide_index=True, height=360)

# =====================================================================
elif pag == "Princípios ativos":
    st.title("Princípios ativos")
    t = D["t17"].copy()
    st.caption("A planilha publica o ranking e faixas de valor (não o valor exato) por princípio ativo.")
    n = st.slider("Top N por ranking de faturamento", 10, 50, 20)
    top = t.sort_values("Rank Faturamento").head(n)
    c1, c2 = st.columns(2)
    with c1:
        d = top.sort_values("Rank Faturamento", ascending=False)
        d["Nome"] = d["Princípio Ativo"].str.upper().str.slice(0, 32)
        fig = px.bar(d, x="Produtos", y="Nome", orientation="h", color_discrete_sequence=[AZUL], text="Produtos")
        fig.update_traces(textposition="outside", cliponaxis=False)
        mostrar(estilo(fig, h=max(380, n * 24), legenda=False, titulo=f"Top {n} em faturamento – nº de produtos (de cima p/ baixo: ranking)"))
    with c2:
        top2 = top.copy()
        top2["Faixa"] = top2["Faturamento"].str.replace(r"^\d+\.\s*", "", regex=True)
        cont = top2.groupby("Faixa").size().reset_index(name="Princípios ativos")
        fig = px.bar(cont, x="Princípios ativos", y="Faixa", orientation="h", color_discrete_sequence=[AZUL])
        mostrar(estilo(fig, h=300, legenda=False, titulo=f"Top {n}: faixa de faturamento"))
        d = t.copy()
        d["Faixa"] = d["Faturamento"]
        cont = ordenar_faixa(d.groupby("Faixa").size().reset_index(name="Princípios ativos"), "Faixa")
        cont["Faixa"] = cont["Faixa"].str.replace(r"^\d+\.\s*", "", regex=True)
        fig = px.bar(cont, x="Faixa", y="Princípios ativos", color_discrete_sequence=[AZUL])
        mostrar(estilo(fig, h=300, legenda=False, titulo="Todos os princípios ativos por faixa de faturamento"))
    st.subheader("Consulta (Tabela 1.7)")
    q = st.text_input("Buscar princípio ativo", placeholder="ex.: dipirona, insulina…")
    s = t.sort_values("Rank Faturamento")
    if q:
        s = s[s["Princípio Ativo"].str.contains(q, case=False, na=False)]
    st.dataframe(s, width="stretch", hide_index=True, height=380)

# =====================================================================
elif pag == "Idade e composição":
    st.title("Tempo de comercialização e composição")
    t = D["t18"]
    t = add_bi(t[~t["Tipo de Registro Sanitário"].isin(["Total", "Outros"]) & t["Faturamento"].notna()])
    ordem_idade = ["Menor ou igual a 5 anos", "Maior que 5 e menor que 10 anos", "Maior ou igual a 10 anos"]
    ordem_idade = [x for x in ordem_idade if x in set(t["Idade da apresentação"])] or list(t["Idade da apresentação"].unique())
    medida = st.radio("Medida", ["Faturamento (R$ bi)", "Qtd (milhões)", "Produtos", "Apresentações"], horizontal=True)
    fig = px.bar(t, x="Idade da apresentação", y=medida, color="Tipo de Registro Sanitário",
                 color_discrete_map=COR, category_orders={"Idade da apresentação": ordem_idade})
    fig.update_traces(marker_line_color="#fcfcfb", marker_line_width=2)
    fig.update_layout(barmode="stack")
    mostrar(estilo(fig, h=420, titulo=f"{medida} por idade da apresentação e tipo de registro"))
    st.markdown('<p class="nota">Combinações com poucos produtos são omitidas pela CMED (sigilo estatístico).</p>',
                unsafe_allow_html=True)
    c = D["t19"]
    c = add_bi(c[~c["Tipo de Registro Sanitário"].isin(["Total", "Outros"]) & c["Faturamento"].notna()])
    c["Comp"] = c["Composição dos princípios ativos"].replace({"Associalções de dois princípios ativos": "Associação de dois princípios ativos"})
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(c, x="Faturamento (R$ bi)", y="Tipo de Registro Sanitário", color="Comp", orientation="h",
                     color_discrete_sequence=[AZUL, "#eb6834", "#1baf7a"])
        fig.update_traces(marker_line_color="#fcfcfb", marker_line_width=2)
        fig.update_layout(barmode="stack")
        mostrar(estilo(fig, titulo="Faturamento por composição (R$ bilhões)"))
    with c2:
        fig = px.bar(c, x="Produtos", y="Tipo de Registro Sanitário", color="Comp", orientation="h",
                     color_discrete_sequence=[AZUL, "#eb6834", "#1baf7a"])
        fig.update_traces(marker_line_color="#fcfcfb", marker_line_width=2)
        fig.update_layout(barmode="stack")
        mostrar(estilo(fig, titulo="Produtos por composição"))
    with st.expander("Tabelas 1.8 e 1.9"):
        tabela_fmt(D["t18"]); tabela_fmt(D["t19"])

# =====================================================================
elif pag == "Regime de preço (MIP × regulado)":
    st.title("Regime de preço: liberado (MIP) × regulado")
    st.caption("“Liberado” = preço livre (inclui os medicamentos isentos de prescrição – MIP); “Regulado” = sujeito ao teto da CMED.")
    t = add_bi(D["t21"])
    tot = t[t["Tipo de Registro Sanitário"] == "Total"]
    c = st.columns(4)
    for i, (_, r) in enumerate(tot.iterrows()):
        c[2 * i].metric(f"{r['Regime']} – faturamento", brl(r["Faturamento"]))
        c[2 * i + 1].metric(f"{r['Regime']} – preço médio", brl(r["Preço médio"], 2))
    sub = t[~t["Tipo de Registro Sanitário"].isin(["Total", "Outros"])]
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(sub, x="Tipo de Registro Sanitário", y="Faturamento (R$ bi)", color="Regime", barmode="group",
                     color_discrete_map=COR)
        mostrar(estilo(fig, titulo="Faturamento por tipo de registro e regime (R$ bilhões)"))
    with c2:
        d = add_bi(D["t22"])
        fig = px.bar(d, x="Canal", y="Faturamento (R$ bi)", color="Regime", barmode="group", color_discrete_map=COR)
        mostrar(estilo(fig, titulo="Faturamento por canal e regime (R$ bilhões)"))
    c3, c4 = st.columns(2)
    with c3:
        d = add_bi(ordenar_faixa(D["t24"], "Faixa de Preço Praticado"))
        d["Faixa"] = d["Faixa de Preço Praticado"].str.replace(r"^\d+\.\s*", "", regex=True)
        fig = px.bar(d, x="Faixa", y="Qtd (milhões)", color="Regime", barmode="group", color_discrete_map=COR)
        mostrar(estilo(fig, titulo="Unidades vendidas por faixa de preço praticado (milhões)"))
    with c4:
        d = D["t27"]
        d = d[(d["xx"] == "Total") & d["Faturamento"].notna()].copy()
        d = add_bi(d)
        fig = px.bar(d, x="Tempo de Mercado", y="Faturamento (R$ bi)", color="Regime", barmode="group", color_discrete_map=COR,
                     category_orders={"Tempo de Mercado": ["Menor ou igual a 5 anos", "Maior que 5 e menor que 10 anos", "Maior ou igual a 10 anos"]})
        mostrar(estilo(fig, titulo="Faturamento por tempo de mercado (R$ bilhões)"))
    d = D["t28"]
    d = add_bi(d[(d["XXX"] == "Total") & d["Faturamento"].notna()])
    d["Composição"] = d["Composição da substância"].replace({"Associalções de dois princípios ativos": "Associação de dois princípios ativos"})
    fig = px.bar(d, x="Composição", y="Faturamento (R$ bi)", color="Regime", barmode="group", color_discrete_map=COR)
    mostrar(estilo(fig, h=340, titulo="Faturamento por composição da apresentação (R$ bilhões)"))
    st.subheader("Principais princípios ativos por regime (Tabela 2.6)")
    reg = st.radio("Regime", ["Liberado", "Regulado"], horizontal=True)
    s = D["t26"]
    s = s[s["Regime"] == reg].sort_values("Rank Faturamento").head(30)
    st.dataframe(s, width="stretch", hide_index=True, height=380)

# =====================================================================
else:
    st.title("Empresas e concentração")
    p = add_bi(D["t34"])
    p["Participação (%)"] = p["Faturamento"] / p["Faturamento"].sum() * 100
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(p, x="Porte Empresa", y="Participação (%)", color_discrete_sequence=[AZUL],
                     text=p["Participação (%)"].map(lambda v: f"{v:.1f}%".replace(".", ",")),
                     category_orders={"Porte Empresa": p["Porte Empresa"].tolist()})
        fig.update_traces(textposition="outside", cliponaxis=False)
        mostrar(estilo(fig, legenda=False, titulo="Participação no faturamento por porte da empresa"))
    with c2:
        fig = px.bar(p, x="Porte Empresa", y="Empresas", color_discrete_sequence=["#eb6834"], text="Empresas",
                     category_orders={"Porte Empresa": p["Porte Empresa"].tolist()})
        fig.update_traces(textposition="outside", cliponaxis=False)
        mostrar(estilo(fig, legenda=False, titulo="Número de empresas por porte"))
    c3, c4 = st.columns(2)
    with c3:
        z = add_bi(D["t31"])
        fig = px.bar(z, x="Nível (Fator Z)", y="Faturamento (R$ bi)", color_discrete_sequence=[AZUL],
                     text=z["Faturamento (R$ bi)"].map(lambda v: f"{v:,.1f}".replace(".", ",")))
        fig.update_traces(textposition="outside", cliponaxis=False)
        mostrar(estilo(fig, legenda=False, titulo="Faturamento por nível de concentração (Fator Z, R$ bi)"))
    with c4:
        z = D["t31"]
        fig = px.bar(z, x="Nível (Fator Z)", y="Empresas", color_discrete_sequence=["#eb6834"], text="Empresas")
        fig.update_traces(textposition="outside", cliponaxis=False)
        mostrar(estilo(fig, legenda=False, titulo="Empresas por nível de concentração"))
    l = add_bi(D["t33"])
    fig = px.bar(l, x="Tempo de Mercado", y="Faturamento (R$ bi)", color_discrete_sequence=[AZUL],
                 text=l["Faturamento (R$ bi)"].map(lambda v: f"{v:,.1f}".replace(".", ",")))
    fig.update_traces(textposition="outside", cliponaxis=False)
    mostrar(estilo(fig, h=300, legenda=False, titulo="Faturamento por LCCT – classificação do ciclo do mercado (R$ bi)"))

    st.subheader("Grupos econômicos")
    g = D["t32"].sort_values("Rank Faturamento")
    n = st.slider("Quantos grupos mostrar", 10, 50, 20)
    top = g.head(n).sort_values("Rank Faturamento", ascending=False)
    fig = px.bar(top, x="Produtos", y="Grupo econômico", orientation="h", color_discrete_sequence=[AZUL], text="Produtos")
    fig.update_traces(textposition="outside", cliponaxis=False)
    mostrar(estilo(fig, h=max(380, n * 24), legenda=False, titulo=f"Top {n} grupos por faturamento – nº de produtos"))
    q = st.text_input("Buscar grupo econômico")
    s = g if not q else g[g["Grupo econômico"].str.contains(q, case=False, na=False)]
    st.dataframe(s, width="stretch", hide_index=True, height=340)

    st.subheader("Unidades Federativas (sede das empresas)")
    u = D["t36"]
    c5, c6 = st.columns(2)
    with c5:
        d = u.sort_values("Empresas")
        fig = px.bar(d, x="Empresas", y="Unidade Federativa", orientation="h", color_discrete_sequence=[AZUL], text="Empresas")
        fig.update_traces(textposition="outside", cliponaxis=False)
        mostrar(estilo(fig, h=420, legenda=False, titulo="Empresas por UF"))
    with c6:
        d = u.sort_values("Produtos")
        fig = px.bar(d, x="Produtos", y="Unidade Federativa", orientation="h", color_discrete_sequence=["#eb6834"], text="Produtos")
        fig.update_traces(textposition="outside", cliponaxis=False)
        mostrar(estilo(fig, h=420, legenda=False, titulo="Produtos por UF"))
    st.caption("O faturamento por UF é publicado apenas em faixas.")
    st.dataframe(u, width="stretch", hide_index=True)
    with st.expander("Tabela 3.5 – produtos por grupo econômico e tipo de registro"):
        st.dataframe(D["t35"], width="stretch", hide_index=True, height=360)
