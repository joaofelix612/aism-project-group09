"""Avaliação: 5 perguntas verificadas à mão com pandas + 1 caso de falha (deve recusar).
Regista tentativas por pergunta e se a resposta coincide. Saída: avaliacao.json"""
import json
import re

import pandas as pd

from llm import LLM
from pipeline import Logger, answer_question

df = pd.read_csv("vendas.csv")
df["_r"] = df["quantidade"] * df["preco"]
df["_ano"] = pd.to_datetime(df["data"]).dt.year

TESTS = [  # (pergunta, esperado calculado com pandas)
    ("Qual a região com maior receita total? (receita = quantidade * preco)", df.groupby("regiao")["_r"].sum().idxmax()),
    ("Quantas vendas (linhas) existem no total?", len(df)),
    ("Qual a quantidade total vendida do produto Rato?", int(df.loc[df["produto"] == "Rato", "quantidade"].sum())),
    ("Qual o produto com maior quantidade total vendida?", df.groupby("produto")["quantidade"].sum().idxmax()),
    ("Qual a receita total (quantidade * preco) em vendas do ano 2024?", round(float(df.loc[df["_ano"] == 2024, "_r"].sum()), 2)),
]
FAIL_TEST = "Qual a idade média dos clientes?"


def matches(expected, result: str) -> bool:
    if isinstance(expected, str):
        return expected.lower() in (result or "").lower()
    nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", (result or "").replace(",", ""))]
    return any(abs(n - expected) <= max(0.01, abs(expected) * 1e-6) for n in nums)


if __name__ == "__main__":
    llm, logger = LLM(), Logger("logs/avaliacao.jsonl", verbose=False)
    rows = []
    for q, exp in TESTS:
        print(f"... a processar: {q}", flush=True)
        r = answer_question(q, df.drop(columns=["_r", "_ano"]), llm, logger)
        ok = r["status"] == "ok" and matches(exp, r["result"])
        rows.append({"pergunta": q, "esperado": exp, "obtido": r["result"], "tentativas": r["attempts"], "correto": ok})
        print(f"{'OK ' if ok else 'ERRO'} | tentativas={r['attempts']} | {q}")
    print(f"... a processar: {FAIL_TEST}", flush=True)
    r = answer_question(FAIL_TEST, df.drop(columns=["_r", "_ano"]), llm, logger)
    refused = r["status"] != "ok"
    rows.append({"pergunta": FAIL_TEST, "esperado": "recusa", "obtido": r["answer"], "tentativas": r["attempts"], "correto": refused})
    print(f"{'OK ' if refused else 'ERRO (inventou resposta!)'} | tentativas={r['attempts']} | {FAIL_TEST}")
    json.dump(rows, open("avaliacao.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=str)
    print(f"\n{sum(x['correto'] for x in rows)}/{len(rows)} corretas -> avaliacao.json")
