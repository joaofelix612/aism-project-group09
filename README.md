# The Data Analyst with a Self-Correcting Loop

Repositório destinado ao projeto desenvolvido no âmbito da disciplina de Agentes Inteligentes e Sistemas Multiagentes.

O projeto consiste num sistema multiagente capaz de responder a perguntas em linguagem natural sobre conjuntos de dados CSV. O sistema planeia a análise, gera e executa código Python, corrige automaticamente possíveis erros e apresenta uma explicação dos resultados.

## 📚 Conteúdos:

### Projeto:

- **Data Analyst with a Self-Correcting Loop:** sistema multiagente que permite analisar dados através de perguntas em linguagem natural.
- **Planner:** interpreta a pergunta do utilizador e define um plano de análise.
- **Code Writer:** gera código Python com pandas para realizar os cálculos necessários.
- **Executor:** executa o código gerado e permite até três tentativas de autocorreção em caso de erro.
- **Explainer:** interpreta os resultados e apresenta uma resposta ao utilizador.
- **Interface gráfica:** permite interagir com o sistema através de uma aplicação web desenvolvida com Streamlit.
- **Avaliação:** inclui testes e um script para avaliar as respostas produzidas pelo sistema.

## 💻 Tecnologias Utilizadas:

- Python
- Pandas
- NumPy
- Streamlit
- Ollama
- Llama 3.1
- Git

## ▶️ Como instalar e correr:

É necessário ter Python e Ollama instalados.

**1. Instalar as dependências:**

```bash
pip install -r requirements.txt
```

**2. Instalar o modelo utilizado:**

```bash
ollama pull llama3.1
```

Certificar-se de que o Ollama está em execução antes de utilizar o modelo.

**3. Executar o projeto:**

Para iniciar a interface gráfica:

```bash
streamlit run app.py
```

A aplicação ficará disponível em:

`http://localhost:8501`

Também é possível executar o projeto através do terminal:

```bash
python main.py vendas.csv
```

Para fazer uma pergunta diretamente:

```bash
python main.py vendas.csv "Qual a região com maior receita total?"
```

**4. Executar os testes:**

```bash
python test_offline.py
python test_app.py
```

Para executar a avaliação:

```bash
python evaluate.py
```

## 📁 Estrutura do repositório:

```text
data_analyst_group9/
│
├── agents.py          Agentes Planner, Code Writer e Explainer
├── app.py             Interface gráfica com Streamlit
├── demo_llm.py        Modelo simulado para demonstração
├── evaluate.py        Script de avaliação do sistema
├── executor.py        Execução segura do código Python
├── llm.py             Comunicação com o Ollama
├── main.py            Execução através do terminal
├── make_data.py       Geração do conjunto de dados
├── pipeline.py        Orquestração dos agentes e autocorreção
├── requirements.txt   Dependências do projeto
├── vendas.csv         Conjunto de dados utilizado
├── avaliacao.json     Resultados da avaliação
├── test_app.py        Testes da interface gráfica
├── test_offline.py    Testes da pipeline sem modelo externo
└── README.md          Documentação do projeto
```

## 👨‍💻 Elementos do Grupo:

- João Félix - 230001131
- João Nogueira - 230000299
- João Gouveia - 230000962
