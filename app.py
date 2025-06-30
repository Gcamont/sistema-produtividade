
from flask import Flask, render_template, request, redirect, url_for, session, send_file
import pandas as pd
import os
import bcrypt
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'ursao_produtividade_123'

usuarios_rh = {"admin": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())}
usuarios_func = {"123": {"senha": bcrypt.hashpw("senha123".encode(), bcrypt.gensalt()), "nome": "Funcionario Exemplo"}}
dados_funcionarios = pd.DataFrame()
solicitacoes = []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login_funcionario", methods=["GET", "POST"])
def login_funcionario():
    if request.method == "POST":
        matricula = request.form["matricula"]
        senha = request.form["senha"]
        if matricula in usuarios_func and bcrypt.checkpw(senha.encode(), usuarios_func[matricula]["senha"]):
            session["matricula"] = matricula
            return redirect(url_for("painel_funcionario"))
        return render_template("login_funcionario.html", erro="Matrícula ou senha incorreta")
    return render_template("login_funcionario.html")

@app.route("/painel_funcionario", methods=["GET", "POST"])
def painel_funcionario():
    if "matricula" not in session:
        return redirect(url_for("login_funcionario"))
    matricula = session["matricula"]
    dados = dados_funcionarios[dados_funcionarios["Matrícula"] == int(matricula)]
    if dados.empty:
        return "<p>Sem dados para este funcionário</p>"
    estoque = int(dados["Estoque"].values[0])
    if request.method == "POST":
        pontos_solicitados = int(request.form["pontos"])
        solicitacoes.append({
            "id": str(uuid.uuid4()),
            "matricula": matricula,
            "nome": usuarios_func[matricula]["nome"],
            "pontos": pontos_solicitados,
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Pendente"
        })
    return render_template("painel_funcionario.html", nome=usuarios_func[matricula]["nome"], estoque=estoque, solicitacoes=[s for s in solicitacoes if s["matricula"] == matricula])

@app.route("/login_rh", methods=["GET", "POST"])
def login_rh():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]
        if usuario in usuarios_rh and bcrypt.checkpw(senha.encode(), usuarios_rh[usuario]):
            session["usuario_rh"] = usuario
            return redirect(url_for("painel_rh"))
        return render_template("login_rh.html", erro="Usuário ou senha inválido.")
    return render_template("login_rh.html")

@app.route("/cadastrar_rh", methods=["GET", "POST"])
def cadastrar_rh():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]
        if usuario in usuarios_rh:
            return render_template("cadastrar_rh.html", erro="Usuário já existe.")
        usuarios_rh[usuario] = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())
        return redirect(url_for("login_rh"))
    return render_template("cadastrar_rh.html")

@app.route("/upload", methods=["POST"])
def upload():
    global dados_funcionarios
    if "arquivo" not in request.files:
        return "Arquivo não enviado", 400
    arquivo = request.files["arquivo"]
    try:
        df = pd.read_excel(arquivo)
    except:
        return "Erro ao ler arquivo", 400

    required_columns = ["Nome", "Matrícula", "Cargo", "Setor", "Valor Base", "Meta", "Pontos"]
    if not all(col in df.columns for col in required_columns):
        return "Colunas esperadas não encontradas no arquivo", 400

    df["Bônus"] = df.apply(lambda row: row["Valor Base"] * 0.25 if row["Pontos"] >= row["Meta"] and row["Pontos"] >= 1100 else 0, axis=1)
    df["Estoque"] = df.apply(lambda row: max(row["Pontos"] - row["Meta"], 0), axis=1)
    df["Data Atualização"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dados_funcionarios = df
    df.to_excel("dados_funcionarios_atualizado.xlsx", index=False)
    df.to_csv("dados_funcionarios_atualizado.txt", sep=";", index=False)
    return redirect(url_for("painel_rh"))

@app.route("/painel_rh")
def painel_rh():
    if "usuario_rh" not in session:
        return redirect(url_for("login_rh"))
    return render_template("painel_rh.html", tabela=dados_funcionarios.to_html(index=False) if not dados_funcionarios.empty else None, solicitacoes=solicitacoes)

@app.route("/aprovar/<id>")
def aprovar(id):
    for s in solicitacoes:
        if s["id"] == id:
            s["status"] = "Aprovado"
    return redirect(url_for("painel_rh"))

@app.route("/negar/<id>")
def negar(id):
    for s in solicitacoes:
        if s["id"] == id:
            s["status"] = "Negado"
    return redirect(url_for("painel_rh"))

@app.route("/exportar/<tipo>")
def exportar(tipo):
    if tipo == "excel":
        return send_file("dados_funcionarios_atualizado.xlsx", as_attachment=True)
    elif tipo == "txt":
        return send_file("dados_funcionarios_atualizado.txt", as_attachment=True)
    return "Formato inválido", 400
