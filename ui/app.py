import json
import requests
import streamlit as st


st.set_page_config(page_title="Cited Notes Q&A", layout="wide")

st.title("Cited Notes Q&A")
st.caption("Ask questions over your local docs. Answers must include citations or abstain.")

with st.sidebar:
    st.header("Settings")
    api_base = st.text_input("API base URL", value="http://localhost:8000")
    top_k = st.slider("top_k (retrieve)", min_value=1, max_value=30, value=10, step=1)
    cite_k = st.slider("cite_k (attach citations)", min_value=1, max_value=6, value=2, step=1)
    include_evidence = st.checkbox("Include evidence (top chunks)", value=True)
    timeout_sec = st.slider("Request timeout (sec)", min_value=5, max_value=120, value=60, step=5)

    st.divider()
    if st.button("Ping /health"):
        try:
            r = requests.get(api_base + "/health", timeout=timeout_sec)
            st.write(r.status_code)
            st.json(r.json())
        except Exception as e:
            st.error(f"Health check failed: {e}")

query = st.text_input("Question", value="What is ISCM?")
col_a, col_b = st.columns([1, 3])

with col_a:
    ask_btn = st.button("Ask", type="primary")

with col_b:
    st.write("Tip: keep your FastAPI server running on port 8000 while using this UI.")

if ask_btn:
    payload = {
        "query": query,
        "top_k": int(top_k),
        "cite_k": int(cite_k),
        "include_evidence": bool(include_evidence),
    }

    st.subheader("Result")

    try:
        r = requests.post(api_base + "/ask", json=payload, timeout=timeout_sec)
        if r.status_code >= 400:
            st.error(f"HTTP {r.status_code}")
            st.text(r.text)
        else:
            out = r.json()

            abstained = bool(out.get("abstained", False))
            answer = out.get("answer", "")
            citations = out.get("citations", [])
            top_chunks = out.get("top_chunks", [])

            if abstained:
                st.warning("ABSTAINED (not enough evidence to answer safely).")
            else:
                st.success("Answered")

            st.markdown("### Answer")
            st.write(answer)

            st.markdown("### Citations")
            if isinstance(citations, list) and len(citations) > 0:
                st.write(", ".join([f"`{c}`" for c in citations]))
            else:
                st.write("_None_")

            if include_evidence:
                st.markdown("### Top retrieved chunks (evidence)")
                if isinstance(top_chunks, list) and len(top_chunks) > 0:
                    for i, ch in enumerate(top_chunks, start=1):
                        score = ch.get("score", 0.0)
                        doc_id = ch.get("doc_id", "")
                        chunk_id = ch.get("chunk_id", "")
                        page = ch.get("page", "")
                        preview = ch.get("text_preview", "")

                        with st.expander(f"{i}) score={score:.4f}  [{doc_id}:{chunk_id}]  page={page}"):
                            st.write(preview)
                else:
                    st.info("No top_chunks returned. (Try include_evidence=true or check your API response.)")

            st.markdown("### Raw JSON")
            st.json(out)

    except Exception as e:
        st.error(f"Request failed: {e}")
        st.info("Make sure the FastAPI server is running and API base URL is correct.")
