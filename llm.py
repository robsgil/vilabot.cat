"""
LLM Module - OpenAI integration for query understanding and response generation
"""

import os
import json
from openai import AsyncOpenAI
from datetime import datetime

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-5-nano"


async def extract_query_intent(query: str) -> dict:
    """
    Extract structured intent from a natural language query.
    
    Returns:
        dict with keys:
        - keywords: list of relevant search terms
        - location: specific location mentioned (or None)
        - date_range: dict with 'start' and 'end' dates (or None)
        - category: event category if identifiable
        - original_query: the original query text
    """
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    system_prompt = f"""Ets un assistent especialitzat en entendre consultes sobre esdeveniments a Catalunya.
    
La data d'avui és: {today}

Analitza la consulta de l'usuari i extreu la següent informació en format JSON:

{{
    "keywords": ["paraula1", "paraula2"],  // Paraules clau per buscar esdeveniments
    "location": "nom del lloc o null",      // Ciutat, poble, barri o comarca
    "date_range": {{                         // Rang de dates o null
        "start": "YYYY-MM-DD",
        "end": "YYYY-MM-DD"
    }},
    "category": "categoria o null"          // música, teatre, familiar, esports, cultura, gastronomia, etc.
}}

Interpreta expressions temporals com:
- "aquest cap de setmana" = dissabte i diumenge d'aquesta setmana
- "avui" = la data d'avui
- "demà" = la data de demà
- "la setmana que ve" = dilluns a diumenge de la setmana vinent
- "aquest mes" = des d'avui fins a final de mes

Respon NOMÉS amb el JSON, sense explicacions."""

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    
    try:
        intent = json.loads(response.choices[0].message.content)
        intent["original_query"] = query
        return intent
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return {
            "keywords": query.split(),
            "location": None,
            "date_range": None,
            "category": None,
            "original_query": query
        }


async def generate_response(
    original_query: str,
    intent: dict,
    scraped_content: list[dict]
) -> str:
    """
    Generate a natural language response based on scraped event content.
    
    Args:
        original_query: The user's original query
        intent: Extracted intent from the query
        scraped_content: List of scraped event data
        
    Returns:
        Formatted response in Catalan
    """
    
    # Format scraped content for the prompt
    if not scraped_content:
        content_text = "No s'han trobat esdeveniments que coincideixin amb la cerca."
    else:
        content_items = []
        for item in scraped_content[:20]:  # Limit to 20 items
            content_items.append(f"""
Títol: {item.get('title', 'Sense títol')}
Data: {item.get('date', 'Data no especificada')}
Lloc: {item.get('location', 'Lloc no especificat')}
Descripció: {item.get('description', 'Sense descripció')}
Font: {item.get('source_url', 'No disponible')}
---""")
        content_text = "\n".join(content_items)
    
    system_prompt = """Ets Vilabot, un assistent amigable especialitzat en esdeveniments locals a Catalunya.

La teva missió és ajudar els catalans a descobrir què passa al seu voltant.

Instruccions:
1. Respon sempre en català
2. Sigues concís però informatiu
3. Si hi ha esdeveniments, presenta'ls de forma clara i organitzada
4. Inclou dates, llocs i una breu descripció
5. Si no trobes esdeveniments, suggereix alternatives o demana més detalls
6. Mantingues un to proper i entusiasta sobre la cultura catalana

Format de resposta:
- Usa emojis amb moderació per fer-ho visual
- Agrupa per data si hi ha múltiples esdeveniments
- Inclou enllaços a les fonts quan siguin disponibles"""

    user_prompt = f"""Consulta de l'usuari: {original_query}

Intent extret:
- Paraules clau: {intent.get('keywords', [])}
- Ubicació: {intent.get('location', 'No especificada')}
- Dates: {intent.get('date_range', 'No especificades')}
- Categoria: {intent.get('category', 'No especificada')}

Contingut trobat:
{content_text}

Genera una resposta útil i ben formatada per a l'usuari."""

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=1500
    )
    
    return response.choices[0].message.content
