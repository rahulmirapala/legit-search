import nltk
from autocorrect import Speller  # Import Speller
from elasticsearch import Elasticsearch

# --- NLTK setup ---
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# --- Autocorrect Function (Updated) ---
speller = Speller(lang='en')  # Initialize the Speller once

def autospell(text):
    """Corrects spelling of words in a query."""
    spells = [speller(w) for w in (nltk.word_tokenize(text))] # Use speller()
    return " ".join(spells)

# --- Elasticsearch Query Builder (With Dynamic Boost) ---
def build_search_query(query_text: str, title_boost: float = 3.0):
    """
    Builds the Elasticsearch query with a dynamic boost for the title.
    """
    
    # Use an f-string to dynamically set the boost value for case_name
    case_name_field = f"case_name^{title_boost}"

    query_body = {
        "query": {
            "query_string": {
                "query": query_text,
                "fields": [
                    "full_text",
                    case_name_field  # e.g., "case_name^5.0"
                ],
                "default_operator": "OR"
            }
        },
        "highlight": {
            "fields": {
                "full_text": {
                    "fragment_size": 150,
                    "number_of_fragments": 3
                }
            }
        },
        "size": 10
    }

    return query_body