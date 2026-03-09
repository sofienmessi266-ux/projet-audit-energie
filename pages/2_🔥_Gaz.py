import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Gaz - Audit Énergétique",
    page_icon="🔥",
    layout="wide"
)

# CSS personnalisé
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #e74c3c;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Titre principal
st.markdown('<h1 class="main-title">🔥 Gestion des Factures de Gaz</h1>', unsafe_allow_html=True)

st.info("🚧 Cette section sera disponible prochainement. La gestion des factures de gaz est en cours de développement.")













