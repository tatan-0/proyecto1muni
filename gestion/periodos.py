from datetime import timedelta


def rango_trimestre(hoy):
    """Devuelve (primer día, último día) del trimestre al que pertenece 'hoy'."""
    mes_inicio = 3 * ((hoy.month - 1) // 3) + 1
    desde = hoy.replace(month=mes_inicio, day=1)
    primero_ultimo_mes = hoy.replace(month=mes_inicio + 2, day=1)
    hasta = (primero_ultimo_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    return desde, hasta