import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import decimal
import requests

description = """
API para consulta de ofertas de crédito de acordo com o cpf do cliente.
"""

tags_metadata = [
    {
        "name": "consulta",
        "description": "Consulta de ofertas de crédito de acordo com o cpf do cliente, confira os exemplos de retorno"
    },
    {
        "name": "mockup_data",
        "description": "Retorna mockup de dados, pode enviar qualquer cpf, já se valor solicitado ou parcelas sejam 0 o retorno serão as ofertas, caso contrário serão as melhores ofertas"
    }
]

app = FastAPI(title="CreditAPI",
              description=description,
              version="0.0.1",
              contact={
                  "name": "Guilherme Luis",
                  "url": "https://github.com/guibluis"
              },
              openapi_tags=tags_metadata)

load_dotenv()

urlStartPoint = os.getenv("URL_START_POINT")


class Consulta(BaseModel):
    cpf: str
    valorSolicitado: decimal.Decimal = 0
    parcelas: int = 0

# retorna as ofertas de crédito de acordo com o cpf caso valorSolicitado e parcelas não sejam informados
# retorna as 3 melhores ofertas de crédito do cpf caso valorSolicitado e parcelas sejam informados


@app.post("/consulta/", tags=["consulta"], responses={
    200: {
        "description": "Ofertas de crédito encontradas",
        "content": {
            "application/json": {
                "examples": {
                    "defaultResult": {
                        "value": {
                            "Banco do Brasil": {
                                "Crédito Consignado": {
                                    "valorMin": 1000,
                                    "valorMax": 10000,
                                    "QntParcelaMin": 1,
                                    "QntParcelaMax": 12,
                                    "jurosMes": 0.01
                                }
                            }
                        }
                    },
                    "withAllParams": {
                        "value": {
                            "instituicaoFinanceira": "Banco do Brasil",
                            "modalidadeCredito": "Crédito Consignado",
                            "valorAPagar": 1000,
                            "valorSolicitado": 1000,
                            "valorParcela": 100,
                            "taxaJuros": 0.01,
                            "qntParcelas": 12
                        }
                    }
                }
            }
        }
    }})
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
                response = requests.post(
                    urlStartPoint + "oferta/", json=jsonRequest)

                if response.ok:
                    resultsPerInstitution[instituicao["nome"]
                                          ][modalidade["nome"]] = response.json()

        if valorSolicitado != 0 and parcelas != 0:
            # Encontra as 3 melhores ofertas com base no valor a pagar(valorSolicitado + juros)
            for instituicao in resultsPerInstitution:
                for modalidade in resultsPerInstitution[instituicao]:
                    modalidadeValorMinimo = resultsPerInstitution[instituicao][modalidade]["valorMin"]
                    modalidadeValorMaximo = resultsPerInstitution[instituicao][modalidade]["valorMax"]
                    modalidadeParcelasMinimo = resultsPerInstitution[
                        instituicao][modalidade]["QntParcelaMin"]
                    modalidadeParcelasMaximo = resultsPerInstitution[
                        instituicao][modalidade]["QntParcelaMax"]
                    modalidadeJuros = resultsPerInstitution[instituicao][modalidade]["jurosMes"]
                    modalidadeJuros = decimal.Decimal(modalidadeJuros)

                    if valorSolicitado < modalidadeValorMinimo or valorSolicitado > modalidadeValorMaximo:
                        continue
                    if parcelas < modalidadeParcelasMinimo or parcelas > modalidadeParcelasMaximo:
                        continue
                    if modalidadeValorMinimo <= valorSolicitado <= modalidadeValorMaximo and modalidadeParcelasMinimo <= parcelas <= modalidadeParcelasMaximo:
                        valorParcela = (valorSolicitado *
                                        (modalidadeJuros * (1 + modalidadeJuros) **
                                         parcelas) / ((1 + modalidadeJuros) ** parcelas - 1))
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


@app.post("/mockup_data/", tags=["mockup_data"])
def mockup_data(consulta: Consulta):
    valorSolicitado = decimal.Decimal(consulta.valorSolicitado)
    if valorSolicitado == 0 or consulta.parcelas == 0:
        return {
            "Banco do Brasil": {
                "Crédito Consignado": {
                    "valorMin": 1000,
                    "valorMax": 10000,
                    "QntParcelaMin": 1,
                    "QntParcelaMax": 12,
                    "jurosMes": 0.01
                },
                "Crédito Pessoal": {
                    "valorMin": 1000,
                    "valorMax": 10000,
                    "QntParcelaMin": 1,
                    "QntParcelaMax": 12,
                    "jurosMes": 0.01
                }
            },
            "Banco do BB": {
                "Crédito Consignado": {
                    "valorMin": 1500,
                    "valorMax": 15000,
                    "QntParcelaMin": 5,
                    "QntParcelaMax": 16,
                    "jurosMes": 0.015
                }
            }
        }
    else:
        return [{
            "instituicaoFinanceira": "Banco do Brasil",
            "modalidadeCredito": "Crédito Consignado",
            "valorAPagar": 1000,
            "valorSolicitado": 1000,
            "valorParcela": 100,
            "taxaJuros": 0.01,
            "qntParcelas": 12
        },
            {
            "instituicaoFinanceira": "Banco do BB",
            "modalidadeCredito": "Crédito Consignado",
            "valorAPagar": 1500,
            "valorSolicitado": 1500,
            "valorParcela": 150,
            "taxaJuros": 0.015,
            "qntParcelas": 16
        }]
