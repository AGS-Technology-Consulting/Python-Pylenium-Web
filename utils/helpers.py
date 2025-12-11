from pylenium.element import Element

def safe_text(element: Element) -> str:
    return element.text or element.value or ""
