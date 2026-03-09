import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Gazoil - Audit Énergétique",
    page_icon="⛽",
    layout="wide"
)

# CSS personnalisé
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #f39c12;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Titre principal
st.markdown('<h1 class="main-title">⛽ Gestion des Factures de Gazoil</h1>', unsafe_allow_html=True)

st.info("🚧 Cette section sera disponible prochainement. La gestion des factures de gazoil est en cours de développement.")













