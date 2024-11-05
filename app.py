from flask import Flask, request, send_file, render_template_string
import pandas as pd
import re
import unicodedata
from io import BytesIO

app = Flask(__name__)

# Função para normalizar o texto (remover acentos e pontuação)
def normalizar_texto(texto):
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    texto = re.sub(r'[^\w\s]', '', texto)
    return texto

@app.route('/')
def index():
    return render_template_string(open("index.html").read())

@app.route('/processar', methods=['POST'])
def processar():
    # Receber o texto do formulário
    texto = request.form['texto']

    # Lista de marcas e palavras para excluir
    marcas_desejadas = ['Infinix', 'Realme', 'Samsung', 'Motorola', 'Honor', 'iPhone']
    produtos_excluir = [
        'PENDRIVE', 'CARTAO DE MEMORIA', 'CARTÃO DE MEMÓRIA',
        'CABO', 'FONTE', 'SSD', 'CAIXA DE SOM', 'RECEPTOR'
    ]

    # Processar o texto
    produtos = []
    marca_atual = None
    linhas = texto.strip().split('\n')

    for idx, linha in enumerate(linhas):
        linha = linha.strip()
        if not linha:
            continue
        is_marca = False
        for marca in marcas_desejadas:
            if marca.upper() in linha.upper():
                marca_atual = marca.capitalize()
                is_marca = True
                break
        if '💰' in linha and marca_atual:
            preco_match = re.search(r'💰\*?([\d\.,]+)', linha)
            preco = preco_match.group(1).replace(',', '.') if preco_match else ''
            descricao = linha.split('💰')[0].strip()
            modelo = descricao
            modelo_normalizado = normalizar_texto(modelo).upper()
            if any(palavra in modelo_normalizado for palavra in produtos_excluir):
                continue
            cores = []
            j = idx + 1
            while j < len(linhas):
                prox_linha = linhas[j].strip()
                if not prox_linha or '💰' in prox_linha or any(m.upper() in prox_linha.upper() for m in marcas_desejadas):
                    break
                else:
                    cores.append(prox_linha)
                j += 1
            cor = ', '.join(cores)
            produtos.append({
                'Marca': marca_atual,
                'Modelo': modelo,
                'Cor': cor,
                'Preço': preco
            })

    # Criar DataFrame e salvar em um buffer em CSV
    df = pd.DataFrame(produtos, columns=['Marca', 'Modelo', 'Cor', 'Preço'])
    buffer = BytesIO()
    df.to_csv(buffer, index=False, encoding='utf-8')
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="produtos_filtrados.csv", mimetype='text/csv')

if __name__ == '__main__':
    app.run(debug=True)
