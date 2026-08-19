"""
Day 5 demo UI placeholder.

Will wire together: query input -> retrieval (src/retrieval) -> generation
(src/generation) -> safety layer (src/safety) -> display of retrieved chunks
+ structured, cited answer (or refusal).
"""

import streamlit as st

st.title("Clinical RAG — Contraindication & Drug-Interaction Checker")
st.caption("Demo UI placeholder — wire up retrieval/generation/safety layers here.")

query = st.text_input("Ask a question about aspirin, statins, or atorvastatin:")
if query:
    st.info("Retrieval and generation pipeline not yet connected. See src/retrieval, "
            "src/generation, src/safety for Day 2-4 build targets.")
