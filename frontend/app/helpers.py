def optional_int(value):
    """'3' -> 3 ; '' / None / 'abc' -> None.  Sirve para filtros de la URL:
    si alguien escribe ?status_id=hola, simplemente se ignora el filtro."""
    if isinstance(value, str) and value.isascii() and value.isdigit():
        return int(value)
    return None
