# 🏴 Vilabot.cat

**Descobreix què passa al teu voltant** — El teu assistent intel·ligent per trobar esdeveniments locals a Catalunya.

![Phase](https://img.shields.io/badge/Phase-1%20MVP-yellow)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## 🎯 Què és Vilabot?

Vilabot és una plataforma de descobriment d'esdeveniments hiperlocals per a Catalunya. Pregunta en llenguatge natural, rep resultats personalitzats.

**Exemple de consulta:**
> "Què puc fer aquest cap de setmana a Terrassa amb nens?"

**Vilabot entén:**
- 📍 Ubicació: Terrassa
- 📅 Data: Aquest cap de setmana
- 🏷️ Categoria: Familiar/infantil

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│                 (HTML/CSS/JS + Senyera UI)                  │
└─────────────────────┬───────────────────────────────────────┘
                      │ POST /api/query
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                          │
├─────────────────────────────────────────────────────────────┤
│  1. Query → LLM (gpt-5-nano) → Extract Intent               │
│  2. Intent → Scraper → Fetch Events                         │
│  3. Events → LLM (gpt-5-nano) → Generate Response          │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Desplegament a Railway

### 1. Fork o clona el repositori

```bash
git clone https://github.com/your-username/vilabot.git
cd vilabot
```

### 2. Configura les variables d'entorn

A Railway, afegeix:
- `OPENAI_API_KEY`: La teva clau d'API d'OpenAI

### 3. Desplega

Railway detectarà automàticament el projecte Python. Només cal fer push.

## 💻 Desenvolupament Local

### Requisits
- Python 3.11+
- Compte OpenAI amb accés a l'API

### Instal·lació

```bash
# Clona el repositori
git clone https://github.com/your-username/vilabot.git
cd vilabot

# Crea un entorn virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o: venv\Scripts\activate  # Windows

# Instal·la dependències
pip install -r requirements.txt

# Configura l'entorn
cp .env.example .env
# Edita .env amb la teva OPENAI_API_KEY

# Executa el servidor
python main.py
```

Obre http://localhost:8000 al navegador.

## 🔧 Configuració de Fonts de Dades

El fitxer `scraper.py` conté la configuració de les fonts web a escanejar.

### Afegir una nova font

1. Obre `scraper.py`
2. Afegeix una entrada al diccionari `SOURCES`:

```python
{
    "name": "Nom de la Font",
    "url": "https://exemple.cat",
    "type": "html",
    "search_url": "https://exemple.cat/cerca?q={keywords}",
    "selectors": {
        "event_container": ".event-item",    # Selector CSS del contenidor
        "title": ".event-title",              # Selector del títol
        "date": ".event-date",                # Selector de la data
        "location": ".event-location",        # Selector de la ubicació
        "description": ".event-description",  # Selector de la descripció
        "link": "a"                           # Selector de l'enllaç
    },
    "enabled": True  # Activa la font
}
```

3. Per trobar els selectors correctes:
   - Obre la web al navegador
   - Fes clic dret → "Inspecciona"
   - Identifica els elements HTML dels esdeveniments
   - Copia els selectors CSS

### Fonts preconfigurades (desactivades per defecte)

- Agenda Cultural Gencat
- Surt de Casa
- Barcelona Cultura
- Festa Catalunya

## 📁 Estructura del Projecte

```
vilabot/
├── main.py              # FastAPI app principal
├── llm.py               # Integració OpenAI
├── scraper.py           # Web scraping (CONFIGURA AQUÍ LES FONTS)
├── static/
│   └── index.html       # Frontend
├── requirements.txt     # Dependències Python
├── .env.example         # Template de configuració
└── README.md            # Documentació
```

## 🔮 Roadmap

### Fase 1 (Actual): MVP d'Esdeveniments
- [x] Interfície de cerca en llenguatge natural
- [x] Extracció d'intent amb LLM
- [x] Framework de scraping configurable
- [ ] Configurar fonts reals de dades
- [ ] Bot de Telegram

### Fase 2: Infraestructura [More to come]

## 🛡️ Consideracions Legals

- Només s'escaneja informació pública d'esdeveniments
- No es recopilen dades personals
- Respectar sempre robots.txt
- Limitar freqüència de peticions

## 📄 Llicència

Apache License — Fet amb ❤️ per Catalunya
