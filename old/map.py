import streamlit as st
import requests
import urllib.parse
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

# Chave da API do Google
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

st.set_page_config(page_title="Google Maps - Distância e Rota", layout="wide")
st.title("📍 Cálculo de distância - Tabela de frete")

col1, col2 = st.columns(2)
with col1:
    origem = st.text_input("Endereço ou CEP de Origem", "Rua rua freire bastos, 284 - 02261-020")
with col2:
    destino = st.text_input("Endereço ou CEP de Destino", "07750-020")

def geocode(endereco):
    """Converte endereço ou CEP em coordenadas (lat, lng)."""
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(endereco)}&key={GOOGLE_API_KEY}"
    r = requests.get(url).json()
    if r["status"] == "OK" and r["results"]:
        loc = r["results"][0]["geometry"]["location"]
        return loc["lat"], loc["lng"]
    return None, None


def calcular_distancia(origem_coords, destino_coords):
    """Consulta a Distance Matrix API e retorna distância e tempo."""
    lat_o, lng_o = origem_coords
    lat_d, lng_d = destino_coords

    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={lat_o},{lng_o}&destinations={lat_d},{lng_d}&key={GOOGLE_API_KEY}"
    resposta = requests.get(url).json()

    try:
        elemento = resposta['rows'][0]['elements'][0]
        status = elemento.get("status", "ERRO")

        if status != "OK":
            return None, None, f"⚠️ A API não conseguiu calcular a distância: `{status}`."

        distancia = elemento['distance']['text']
        duracao = elemento['duration']['text']
        return distancia, duracao, None
    except Exception as e:
        return None, None, f"❌ Erro inesperado ao processar a resposta: {str(e)}"

if st.button("Calcular"):
    origem_coords = geocode(origem)
    destino_coords = geocode(destino)

    if not origem_coords or not destino_coords:
        st.error("Não foi possível localizar os endereços informados.")
    else:
        distancia, duracao, erro = calcular_distancia(origem_coords, destino_coords)

        if erro:
            st.warning(erro)
        else:
            st.subheader("📏 Resultado")
            st.markdown(f"- **Distância**: `{distancia}`\n- **Tempo estimado**: `{duracao}`")

            # Mapa com rota
            st.subheader("🗺️ Mapa com rota")
            map_embed_url = (
                f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}"
                f"&origin={origem_coords[0]},{origem_coords[1]}"
                f"&destination={destino_coords[0]},{destino_coords[1]}"
                f"&mode=driving"
            )
            st.markdown(f'<iframe width="100%" height="500" frameborder="0" style="border:0" '
                        f'src="{map_embed_url}" allowfullscreen></iframe>', unsafe_allow_html=True)

            # Street View da Destino
            st.subheader("🚗 Street View - Destino")
            street_embed_url = (
                f"https://www.google.com/maps/embed/v1/streetview?key={GOOGLE_API_KEY}"
                f"&location={destino_coords[0]},{destino_coords[1]}&heading=210&pitch=10&fov=80"
            )
            st.markdown(f'<iframe width="100%" height="400" frameborder="0" style="border:0" '
                        f'src="{street_embed_url}" allowfullscreen></iframe>', unsafe_allow_html=True)
