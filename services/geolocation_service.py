"""
Serviço de Geolocalização
========================
Gerencia operações de geolocalização usando Google Maps API.
"""

import math
import requests
import urllib.parse
import streamlit as st
from typing import Tuple, Optional, Dict


class GeolocationService:
    """Serviço para gerenciar operações de geolocalização"""
    
    ORIGENS_DISPONIVEIS = {
        "Matriz (SP)": "Rua Freire Bastos, 284, São Paulo - SP, 02261-020",
        "Filial (Atibaia)": "Estrada das Flores 450, Atibaia - SP, 12948-326"
    }
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def geocode(self, endereco: str) -> Tuple[Optional[float], Optional[float]]:
        """Converte endereço ou CEP em coordenadas (lat, lng)"""
        try:
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(endereco)}&key={self.api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data["status"] == "OK" and data["results"]:
                location = data["results"][0]["geometry"]["location"]
                return location["lat"], location["lng"]
            return None, None
        except Exception as e:
            st.error(f"Erro na geocodificação: {str(e)}")
            return None, None
    
    def calcular_distancia(self, origem_coords: Tuple[float, float], 
                          destino_coords: Tuple[float, float]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Consulta a Distance Matrix API e retorna distância e tempo"""
        try:
            lat_o, lng_o = origem_coords
            lat_d, lng_d = destino_coords
            
            url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={lat_o},{lng_o}&destinations={lat_d},{lng_d}&key={self.api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            elemento = data['rows'][0]['elements'][0]
            status = elemento.get("status", "ERRO")
            
            if status != "OK":
                return None, None, f"⚠️ API não conseguiu calcular: `{status}`"
            
            distancia = elemento['distance']['text']
            duracao = elemento['duration']['text']
            return distancia, duracao, None
            
        except Exception as e:
            return None, None, f"❌ Erro ao processar resposta: {str(e)}"
    
    def calcular_rota_completa(self, origem: str, destino: str) -> Dict:
        """Calcula rota completa incluindo geocodificação e distância"""
        resultado = {
            'sucesso': False,
            'origem_coords': None,
            'destino_coords': None,
            'distancia': None,
            'duracao': None,
            'distancia_km': None,
            'erro': None
        }
        
        # Geocodificar origem
        origem_coords = self.geocode(origem)
        if not origem_coords:
            resultado['erro'] = "❌ Não foi possível localizar o endereço de origem."
            return resultado
        
        # Geocodificar destino
        destino_coords = self.geocode(destino)
        if not destino_coords:
            resultado['erro'] = f"❌ Não foi possível localizar o endereço de destino: {destino}"
            return resultado
        
        # Calcular distância
        distancia, duracao, erro = self.calcular_distancia(origem_coords, destino_coords)
        if erro:
            resultado['erro'] = erro
            return resultado
        
        # Converter distância para km numérico
        try:
            distancia_km = self._extrair_km_da_string(distancia)
            resultado.update({
                'sucesso': True,
                'origem_coords': origem_coords,
                'destino_coords': destino_coords,
                'distancia': distancia,
                'duracao': duracao,
                'distancia_km': distancia_km
            })
        except Exception as e:
            resultado['erro'] = f"❌ Erro ao processar distância: {str(e)}"
        
        return resultado
    
    def _extrair_km_da_string(self, distancia_str: str) -> float:
        """Extrai valor numérico de quilômetros da string de distância"""
        distancia_texto = distancia_str.replace('km', '').strip()
        
        # Se tem vírgula, verificar se é separador de milhares ou decimal
        if ',' in distancia_texto:
            # Se tem ponto E vírgula (ex: "1,159.5"), vírgula é separador de milhares
            if '.' in distancia_texto:
                # Formato: "1,159.5 km" - vírgula = milhares, ponto = decimal
                distancia_km = float(distancia_texto.replace(',', ''))
            else:
                # Só tem vírgula - verificar posição
                partes = distancia_texto.split(',')
                if len(partes[1]) == 3:  # "1,159" - vírgula é separador de milhares
                    distancia_km = float(distancia_texto.replace(',', ''))
                else:  # "1,5" - vírgula é decimal
                    distancia_km = float(distancia_texto.replace(',', '.'))
        else:
            # Só números e possivelmente ponto decimal
            distancia_km = float(distancia_texto.replace('.', ''))
        
        return distancia_km
    
    @staticmethod
    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distância entre duas coordenadas usando a fórmula de Haversine"""
        R = 6371  # Raio da Terra em km
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def gerar_url_mapa_embed(self, origem_coords: Tuple[float, float], 
                           destino_coords: Tuple[float, float]) -> str:
        """Gera URL do mapa embed com rota"""
        return (
            f"https://www.google.com/maps/embed/v1/directions?key={self.api_key}"
            f"&origin={origem_coords[0]},{origem_coords[1]}"
            f"&destination={destino_coords[0]},{destino_coords[1]}"
            f"&mode=driving"
        )
    
    def gerar_url_street_view(self, coords: Tuple[float, float]) -> str:
        """Gera URL do Street View"""
        return (
            f"https://www.google.com/maps/embed/v1/streetview?key={self.api_key}"
            f"&location={coords[0]},{coords[1]}&heading=210&pitch=10&fov=80"
        )
    
    @classmethod
    def get_origens_disponiveis(cls) -> Dict[str, str]:
        """Retorna dicionário de origens disponíveis"""
        return cls.ORIGENS_DISPONIVEIS.copy()