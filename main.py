import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

load_dotenv()

app = FastAPI()

urlStartPoint = os.getenv("URL_START_POINT")

class Consulta(BaseModel):
    cpf: str
    valorSolicitado: float = 0
    parcelas: int = 0

# retorna as ofertas de crédito de acordo com o cpf caso valorSolicitado e parcelas não sejam informados 
# retorna as 3 melhores ofertas de crédito do cpf caso valorSolicitado e parcelas sejam informados
@app.post("/consulta/")
def consulta_cpf(consulta: Consulta):
    # Consulta quais instituições o cpf tem crédito
    jsonRequest = {"cpf": consulta.cpf}
    response = requests.post(urlStartPoint + "credito/", json=jsonRequest)
    
    # Variaveis para encontrar as 3 melhores ofertas
    melhoresOfertas = []
    valorSolicitado = consulta.valorSolicitado
    parcelas = consulta.parcelas
    
    if response.ok:
        result = response.json()
        resultsPerInstitution = {}
        # Para cada instituição, consulta as ofertas de acordo com a modalidade
        for instituicao in result["instituicoes"]:
            resultsPerInstitution[instituicao["nome"]] = {}
            for modalidade in instituicao["modalidades"]:
                jsonRequest = {
                    "cpf": consulta.cpf, "instituicao_id": instituicao["id"], "codModalidade": modalidade["cod"]
                    }
                response = requests.post(urlStartPoint + "oferta/", json=jsonRequest)
                
                if response.ok:
                    resultsPerInstitution[instituicao["nome"]][modalidade["nome"]] = response.json()

        if valorSolicitado != 0 and parcelas != 0:
            # Encontra as 3 melhores ofertas com base no valor a pagar(valorSolicitado + juros)
            for instituicao in resultsPerInstitution:
                for modalidade in resultsPerInstitution[instituicao]:
                    modalidadeValorMinimo = resultsPerInstitution[instituicao][modalidade]["valorMin"]
                    modalidadeValorMaximo = resultsPerInstitution[instituicao][modalidade]["valorMax"]
                    modalidadeParcelasMinimo = resultsPerInstitution[instituicao][modalidade]["QntParcelaMin"]
                    modalidadeParcelasMaximo = resultsPerInstitution[instituicao][modalidade]["QntParcelaMax"]
                    modalidadeJuros = resultsPerInstitution[instituicao][modalidade]["jurosMes"]
                    
                    if valorSolicitado < modalidadeValorMinimo or valorSolicitado > modalidadeValorMaximo:
                        continue
                    if parcelas < modalidadeParcelasMinimo or parcelas > modalidadeParcelasMaximo:
                        continue
                    if modalidadeValorMinimo <= valorSolicitado <= modalidadeValorMaximo and modalidadeParcelasMinimo <= parcelas <= modalidadeParcelasMaximo:
                        valorParcela = valorSolicitado * (modalidadeJuros * (1 + modalidadeJuros) ** parcelas) / ((1 + modalidadeJuros) ** parcelas - 1)
                        melhoresOfertas.append({
                            "instituicaoFinanceira": instituicao,
                            "modalidadeCredito": modalidade,
                            "valorAPagar": valorParcela * parcelas,
                            "valorSolicitado": valorSolicitado,
                            "valorParcela": valorParcela,
                            "taxaJuros": modalidadeJuros,
                            "qntParcelas": parcelas
                        })
            melhoresOfertas.sort(key=lambda x: x["valorAPagar"])
            melhoresOfertas = melhoresOfertas[:3]
            
            return melhoresOfertas
        else:
            return resultsPerInstitution
    else:
        raise HTTPException(status_code=400, detail="Erro ao consultar CPF")