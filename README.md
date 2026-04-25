# Fefusa Menores

Web app de clasificaciones combinadas para las categorias C15, C17 y C20 de Fefusa Mendoza.

## Requisitos

- Python 3.11+
- pip

## Instalacion

```bash
pip install -r requirements.txt
```

## Variables de entorno

- `PORT`: Puerto para el servidor (default: 5000)
- `PROMOTION_SPOTS`: Numero de equipos que ascienden/descienden (default: 2)

## Ejecucion local

```bash
python app.py
```

O usando Flask CLI:

```bash
flask --app app run
```

La aplicacion estara disponible en `http://localhost:5000`.

## Endpoints

- `/`: Pagina principal con clasificaciones combinadas
- `/refresh`: Actualiza los datos raspando Scorefy
- `/api/standings`: Devuelve todos los datos en JSON

## Despliegue en Render

1. Crear cuenta en [Render](https://render.com)
2. Conectar repositorio Git
3. Render detectara el archivo `render.yaml` automaticamente
4. O crear un Web Service manualmente:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`

## Estructura del proyecto

```
Fefusa-Menores/
  app.py            — Aplicacion Flask
  scraper.py        — Raspado de Scorefy
  calculator.py    — Calculo de tablas combinadas
  templates/
    index.html     — Plantilla HTML
  requirements.txt
  render.yaml
  Procfile
  .gitignore
  README.md
```

## Funcionamiento

1. Al iniciar, la app raspada las 9 URLs de Scorefy
2. Los datos se almacenan en memoria
3. Se calculan las tablas combinadas por club
4. Las zones de ascenso/descenso se marcan visualmente
5. `/refresh` permite actualizar los datos sin reiniciar