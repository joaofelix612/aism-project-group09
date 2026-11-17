"""Uso: python main.py vendas.csv "Qual a região com maior receita total?" [--model llama3.1] [--no-cache]"""
import argparse

import pandas as pd

from llm import DEFAULT_MODEL, LLM
from pipeline import Logger, answer_question


def main():
    ap = argparse.ArgumentParser(description="Data Analyst with a Self-Correcting Loop")
    ap.add_argument("csv")
    ap.add_argument("question", nargs="?", help="Se omitida, entra em modo interativo")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    llm = LLM(args.model, use_cache=not args.no_cache)
    logger = Logger()

    questions = [args.question] if args.question else iter(lambda: input("\nPergunta (vazio para sair): ").strip(), "")
    for q in questions:
        r = answer_question(q, df, llm, logger)
        print(f"\n=== RESPOSTA [{r['status']}, tentativas: {r['attempts']}] ===\n{r['answer']}\n")


if __name__ == "__main__":
    main()
