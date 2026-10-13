"""Leitura e padronização das tabelas do Anuário Estatístico do Mercado Farmacêutico (CMED 2024)."""
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import openpyxl

warnings.filterwarnings("ignore")
ARQUIVO = Path(__file__).parent / "anuario_cmed_2024.xlsx"

# palavra-chave do cabeçalho original -> nome padronizado
MAPA = [
    ("Apresentações cadastradas", "Apresentações"),
    ("Apresentações comercializadas", "Qtd comercializada"),
    ("Quantidade comercializada", "Qtd comercializada"),
    ("Princípios ativos", "Princípios ativos"),
    ("Subclasses", "Subclasses"),
    ("Faturamento", "Faturamento"),
    ("Empresas", "Empresas"),
    ("Produtos", "Produtos"),
    ("Preço Médio", "Preço médio"),
    ("Preço médio", "Preço médio"),
    ("Média de Preço", "Média preço"),
    ("Mediana", "Mediana preço"),
]


def _renomear(c):
    c = str(c).replace("\n", " ").strip()
    for chave, novo in MAPA:
        if c.lower().startswith(chave.lower()):
            return novo
    return c


@__import__("functools").lru_cache(maxsize=1)
def _wb():
    return openpyxl.load_workbook(ARQUIVO, data_only=True)


def tabela(nome: str, primeira_col: str) -> pd.DataFrame:
    """Lê a aba `nome`: localiza a linha de cabeçalho (primeira célula == primeira_col)
    e lê até a linha de rodapé ('Fonte')."""
    linhas = list(_wb()[nome].iter_rows(values_only=True))
    ini = next(i for i, r in enumerate(linhas)
               if r[1] is not None and str(r[1]).strip().startswith(primeira_col))
    cab = [_renomear(c) for c in linhas[ini][1:] if c is not None]
    dados = []
    for r in linhas[ini + 1:]:
        if r[1] is None or str(r[1]).startswith(("Fonte", "Nota", "(")):
            break
        dados.append(list(r[1:1 + len(cab)]))
    df = pd.DataFrame(dados, columns=cab)
    # "**" = dado omitido por sigilo estatístico
    df = df.replace("**", np.nan)
    for c in df.columns:
        if c in ("Empresas", "Produtos", "Apresentações", "Princípios ativos", "Subclasses",
                 "Faturamento", "Qtd comercializada", "Preço médio", "Média preço",
                 "Mediana preço", "Rank Faturamento", "Rank Quantidade",
                 "Rank Quantidade comercializada"):
            num = pd.to_numeric(df[c], errors="coerce")
            # colunas de faixa (texto) permanecem como texto
            if num.notna().sum() >= 0.5 * df[c].notna().sum():
                df[c] = num
    return df


def ordem_faixa(s: pd.Series) -> pd.Series:
    """Ordena rótulos do tipo '3. R$ 50,01 - ...' pelo número inicial."""
    return s.str.extract(r"^(\d+)\.")[0].astype(float)


CANAL_CURTO = {
    "DISTRIBUIDOR": "Distribuidor",
    "ESTABELECIMENTO PRIVADO DE SAÚDE": "Estab. privado de saúde",
    "FARMÁCIAS E DROGARIAS PRIVADAS": "Farmácias e drogarias",
    "GOVERNO": "Governo",
    "OUTROS DESTINATÁRIOS, NÃO PRIVADOS": "Outros (não privados)",
}


def _canal(x):
    for k, v in CANAL_CURTO.items():
        if str(x).upper().startswith(k.split(",")[0][:20]):
            return v
    return x


def carregar() -> dict:
    d = {}
    d["t11"] = tabela("1.1", "Tipo de Registro")
    d["t12"] = tabela("1.2", "Tipo de Registro")
    d["t13"] = tabela("1.3", "Tipo de Registro")
    d["t14"] = tabela("1.4", "Tipo de Registro")
    d["t15"] = tabela("1.5", "Grupo Anat")
    d["t16"] = tabela("1.6", "Subclasse")
    d["t17"] = tabela("1.7", "Rank Quantidade")
    d["t18"] = tabela("1.8", "Tipo de Registro")
    d["t19"] = tabela("1.9", "Tipo de Registro")
    d["t21"] = tabela("2.1", "Regime")
    d["t22"] = tabela("2.2", "Regime")
    d["t23"] = tabela("2.3", "Regime")
    d["t24"] = tabela("2.4", "Regime")
    d["t25"] = tabela("2.5", "Regime")
    d["t26"] = tabela("2.6", "Rank Faturamento")
    d["t27"] = tabela("2.7", "Regime")
    d["t28"] = tabela("2.8", "Regime")
    d["t31"] = tabela("3.1", "Nível")
    d["t32"] = tabela("3.2", "Rank Faturamento")
    d["t33"] = tabela("3.3", "Tempo de Mercado")
    d["t34"] = tabela("3.4", "Porte")
    d["t35"] = tabela("3.5", "Rank Faturamento")
    d["t36"] = tabela("3.6", "Unidade Federativa")
    for k in ("t12", "t22"):
        col = "Tipo de Canal" if "Tipo de Canal" in d[k].columns else "Canal"
        d[k][col] = d[k][col].map(_canal)
    return d
