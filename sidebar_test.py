import streamlit as st
import inspect

# Sidebar yapısını oluştur
st.sidebar.title("Test Sidebar")
st.sidebar.write("Bu bir test.")

# HTML çıktısı için
st.title("Sidebar Yapı Testi")

# CSS seçicileri için JavaScript
js = """
<script>
function getAllElementsWithIds() {
    let elements = document.querySelectorAll('[id]');
    let result = [];
    
    elements.forEach(el => {
        result.push({
            id: el.id,
            tag: el.tagName,
            classes: Array.from(el.classList)
        });
    });
    
    return JSON.stringify(result);
}

function getAllElementsWithDataTestId() {
    let elements = document.querySelectorAll('[data-testid]');
    let result = [];
    
    elements.forEach(el => {
        result.push({
            'data-testid': el.getAttribute('data-testid'),
            tag: el.tagName,
            classes: Array.from(el.classList)
        });
    });
    
    return JSON.stringify(result);
}

setTimeout(() => {
    const elementsWithIds = getAllElementsWithIds();
    const elementsWithTestIds = getAllElementsWithDataTestId();
    
    const outputDiv = document.createElement('pre');
    outputDiv.style.backgroundColor = '#f0f0f0';
    outputDiv.style.padding = '10px';
    outputDiv.style.overflowX = 'auto';
    outputDiv.style.maxHeight = '300px';
    outputDiv.innerHTML = '<strong>Elements with IDs:</strong>\\n' + 
                         JSON.stringify(JSON.parse(elementsWithIds), null, 2) + 
                         '\\n\\n<strong>Elements with data-testid:</strong>\\n' + 
                         JSON.stringify(JSON.parse(elementsWithTestIds), null, 2);
    
    document.body.appendChild(outputDiv);
}, 1000);
</script>
"""

st.markdown(js, unsafe_allow_html=True)