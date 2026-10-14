import requests
import streamlit as st
from geopy.geocoders import Nominatim

# Configuración inicial de la página
st.set_page_config(page_title="Calculadora de Viajes - Kangoo", page_icon="🚐", layout="centered")

st.title("🚐 Calculadora de Costos de Viaje")
st.write("Herramienta profesional para calcular costos de combustible, distancias y ganancias.")

# Inicializamos el geolocalizador
geolocalizador = Nominatim(user_agent="presupuesto_viaje_app")

def obtener_coordenadas(ciudad):
    try:
        locacion = geolocalizador.geocode(ciudad + ", Argentina")
        if locacion:
            return locacion.longitude, locacion.latitude
    except Exception as e:
        st.error(f"Error al buscar la ciudad: {e}")
    return None, None

def calcular_ruta_osrm(ciudad_origen, ciudad_destino):
    longitud1, latitud1 = obtener_coordenadas(ciudad_origen)
    longitud2, latitud2 = obtener_coordenadas(ciudad_destino)

    if not longitud1 or not longitud2:
        return None, None

    url = f"http://router.project-osrm.org/route/v1/driving/{longitud1},{latitud1};{longitud2},{latitud2}?overview=false"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data["code"] == "Ok":
            distancia_km = data["routes"][0]["distance"] / 1000
            duracion_segundos = data["routes"][0]["duration"]
            
            horas = int(duracion_segundos // 3600)
            minutos = int((duracion_segundos % 3600) // 60)
            tiempo_formato = f"{horas} horas {minutos} minutos"
            
            return round(distancia_km, 2), tiempo_formato
        else:
            return None, None
    except Exception:
        return None, None

def gasto_nafta(gas_vehiculo, precio_combus, distancia):
    resultado = distancia / 100 * gas_vehiculo
    total = resultado * precio_combus
    return total

def tiempo(vel, dis):
    tiem = dis / vel
    horas = int(tiem)
    minutos = int((tiem - horas) * 60)
    return horas, minutos

# --- INTERFAZ VISUAL EN STREAMLIT ---

st.subheader("1. Datos del Viaje y Vehículo")

# Contenedor para los inputs principales
col1, col2 = st.columns(2)
with col1:
    salida = st.text_input("Ciudad de salida", "Victoria, Entre Rios")
    gasto_vehiculo = st.number_input("Litros cada 100km", value=8.5)
with col2:
    destino = st.text_input("Ciudad de destino", "Rosario")
    precio_combus = st.number_input("Precio del combustible ($)", value=2150.0)

sabe_precio = st.selectbox("¿Sabe cuánto dinero va a ganar en total?", ("Sí", "No"))
precio = None
if sabe_precio == "Sí":
    precio = st.number_input("¿Cuánto ganará en total? ($)", value=0.0)

# Botón principal para calcular con OSRM
if st.button("Calcular Ruta Automática"):
    with st.spinner("Calculando ruta y consultando mapas..."):
        distancia, tiempo_est = calcular_ruta_osrm(salida, destino)
        
        if distancia is not None:
            st.session_state['distancia'] = distancia
            st.session_state['tiempo'] = tiempo_est
            st.session_state['modo_manual'] = False
            st.success("¡Ruta calculada con éxito!")
        else:
            st.warning("No se pudo calcular la ruta automáticamente. Podés usar el modo manual abajo.")
            st.session_state['distancia'] = None

# Si ya tenemos una distancia calculada o queremos forzar el modo manual
if 'distancia' in st.session_state and st.session_state['distancia'] is not None:
    distancia = st.session_state['distancia']
    tiempo_est = st.session_state['tiempo']
    
    st.markdown("---")
    st.subheader("📊 Resultados Automáticos")
    st.write(f"**Origen:** {salida} ➔ **Destino:** {destino}")
    st.write(f"**Distancia aproximada:** {distancia} km")
    st.write(f"**Tiempo aproximado:** {tiempo_est}")
    
    dinero_nafta = gasto_nafta(gasto_vehiculo, precio_combus, distancia)
    st.metric(label="Gasto en Combustible", value=f"${round(dinero_nafta, 2)}")
    
    if precio is not None and precio > 0:
        ganancia_neta = precio - dinero_nafta
        st.metric(label="Ganancia Neta (Descontando Nafta)", value=f"${round(ganancia_neta, 2)}")

st.markdown("---")
st.subheader("🛠️ Opción Manual (Si no te convence la ruta o querés ajustar)")

with st.form("form_manual"):
    distancia_manual = st.number_input("Ingresa los km de distancia a mano", value=0.0)
    velocidad_manual = st.number_input("Velocidad promedio estimada (km/h)", value=80.0)
    tipo_viaje = st.radio("¿El viaje es solo de ida?", ("Sí", "No (Ida y vuelta)"))
    
    enviar_manual = st.form_submit_button("Calcular con Datos Manuales")
    
    if enviar_manual:
        dist_final = distancia_manual if tipo_viaje == "Sí" else distancia_manual * 2
        h, m = tiempo(velocidad_manual, dist_final)
        gasto_m = gasto_nafta(gasto_vehiculo, precio_combus, dist_final)
        
        st.success("¡Cálculo manual realizado!")
        st.write(f"**Distancia total calculada:** {dist_final} km")
        st.write(f"**Tiempo estimado:** {h} horas y {m} minutos")
        st.metric(label="Gasto en Combustible (Manual)", value=f"${round(gasto_m, 2)}")
        
        if precio is not None and precio > 0:
            ganancia_m = precio - gasto_m
            st.metric(label="Ganancia Neta (Manual)", value=f"${round(ganancia_m, 2)}")