
from flask import Flask, render_template, request, redirect, url_for, session, send_file
import pandas as pd
import os
import bcrypt
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'ursao_produtividade_123'

# Usuários RH (armazenado em dicionário para este exemplo)
usuarios_rh = {"admin": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())}
dados_funcionarios = pd.DataFrame()

@app.route("/")
def index():
    return redirect(url_for("login_rh"))

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
    if dados_funcionarios.empty:
        return render_template("painel_rh.html", tabela=None)
    return render_template("painel_rh.html", tabela=dados_funcionarios.to_html(classes='table table-striped', index=False))

@app.route("/exportar/<tipo>")
def exportar(tipo):
    if tipo == "excel":
        return send_file("dados_funcionarios_atualizado.xlsx", as_attachment=True)
    elif tipo == "txt":
        return send_file("dados_funcionarios_atualizado.txt", as_attachment=True)
    return "Formato inválido", 400
