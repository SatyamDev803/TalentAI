from transformers import pipeline
from typing import List, Dict


class BERTEntityExtractor:
    def __init__(self, model_name: str = "dslim/bert-base-NER"):
        self.ner_pipeline = pipeline(
            "ner", model=model_name, aggregation_strategy="simple"
        )

    def extract_entities(self, text: str) -> List[Dict]:
        try:
            entities = self.ner_pipeline(text)
            return [
                {
                    "entity_type": entity["entity_group"],
                    "text": entity["word"],
                    "score": float(entity["score"]),
                    "start": entity["start"],
                    "end": entity["end"],
                }
                for entity in entities
            ]
        except Exception:
            return []

    def extract_by_type(self, text: str, entity_type: str) -> List[str]:
        entities = self.extract_entities(text)
        return [
            entity["text"]
            for entity in entities
            if entity["entity_type"] == entity_type
        ]
