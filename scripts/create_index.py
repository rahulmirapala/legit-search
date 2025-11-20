"""Create Elasticsearch index with explicit mappings and analyzers."""
import os
from elasticsearch import Elasticsearch
from app.config import get_settings

SETTINGS = {
    "settings": {
        "analysis": {
            "filter": {
                "legal_stop": {"type": "stop", "stopwords": "_english_"},
                "english_possessive_stemmer": {"type": "stemmer", "name": "possessive_english"},
                "kstem": {"type": "stemmer", "name": "kstem"},
                "edge_ngrams": {"type": "edge_ngram", "min_gram": 2, "max_gram": 20},
                "shingle_2_3": {"type": "shingle", "min_shingle_size": 2, "max_shingle_size": 3, "output_unigrams": True},
                "legal_synonyms": {
                    "type": "synonym_graph",
                    "lenient": True,
                    "synonyms": [
                        "alimony, maintenance",
                        "bail, release on bond",
                        "FIR, first information report",
                        "PIL, public interest litigation",
                        "habeas corpus, unlawful detention",
                        "precedent, stare decisis",
                        "fundamental rights, constitutionally guaranteed rights"
                    ]
                }
            },
            "analyzer": {
                "legal_text_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "asciifolding",
                        "english_possessive_stemmer",
                        "kstem",
                        "legal_stop"
                    ]
                },
                "legal_text_search": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "asciifolding",
                        "english_possessive_stemmer",
                        "kstem",
                        "legal_stop",
                        "legal_synonyms"
                    ]
                },
                "legal_shingle": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "asciifolding",
                        "english_possessive_stemmer",
                        "kstem",
                        "legal_stop",
                        "shingle_2_3"
                    ]
                },
                "case_name_autocomplete": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding", "edge_ngrams"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "case_name": {
                "type": "text",
                "analyzer": "legal_text_analyzer",
                "search_analyzer": "legal_text_search",
                "fields": {
                    "raw": {"type": "keyword", "ignore_above": 256},
                    "ngram": {"type": "text", "analyzer": "case_name_autocomplete", "search_analyzer": "legal_text_search"},
                    "shingle": {"type": "text", "analyzer": "legal_shingle"}
                }
            },
            "judgment_date": {"type": "date", "format": "yyyy-MM-dd"},
            "citation_id": {"type": "keyword"},
            "full_text": {
                "type": "text",
                "analyzer": "legal_text_analyzer",
                "search_analyzer": "legal_text_search",
                "fields": {
                    "shingle": {"type": "text", "analyzer": "legal_shingle"}
                }
            },
            "year": {"type": "integer"},
            "page_rank": {"type": "float"},
            "ocr_used": {"type": "boolean"},
            "embedding": {
                "type": "dense_vector",
                "dims": 384,
                "index": True,
                "similarity": "cosine"
            },
            "court": {"type": "keyword"}
        }
    }
}

def main():
    settings = get_settings()
    es = Elasticsearch(settings.es_host)
    index = settings.index_name
    if es.indices.exists(index=index):
        print(f"Index '{index}' already exists. Skipping creation.")
        return
    es.indices.create(index=index, body=SETTINGS)
    print(f"Index '{index}' created.")

if __name__ == "__main__":
    main()
