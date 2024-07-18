from argparse import ArgumentParser
from pathlib import Path
from typing import Any, Tuple
from tqdm import tqdm

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngine, NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine, OperatorConfig
import warnings


def create_nlp_engine_with_transformers(
    model_path: str,
) -> Tuple[NlpEngine, RecognizerRegistry]:
    print(f"Loading Transformers model: {model_path} of type {type(model_path)}")

    nlp_configuration = {
        "nlp_engine_name": "transformers",
        "models": [
            {
                "lang_code": "de",
                "model_name": {"spacy": "de_core_news_lg", "transformers": model_path},
            },
            {
                "lang_code": "en",
                "model_name": {"spacy": "en_core_web_lg", "transformers": model_path},
            },
        ],
        "ner_model_configuration": {
            "model_to_presidio_entity_mapping": {
                "PER": "PERSON",
                "PERSON": "PERSON",
                "LOC": "LOCATION",
                "LOCATION": "LOCATION",
                "GPE": "LOCATION",
                "ORG": "ORGANIZATION",
                "ORGANIZATION": "ORGANIZATION",
                "NORP": "NRP",
                "AGE": "AGE",
                "ID": "ID",
                "EMAIL": "EMAIL",
                "PATIENT": "PERSON",
                "STAFF": "PERSON",
                "HOSP": "ORGANIZATION",
                "PATORG": "ORGANIZATION",
                "DATE": "DATE_TIME",
                "TIME": "DATE_TIME",
                "PHONE": "PHONE_NUMBER",
                "HCW": "PERSON",
                "HOSPITAL": "ORGANIZATION",
                "FACILITY": "LOCATION",
            },
            "low_confidence_score_multiplier": 0.4,
            "low_score_entity_names": ["ID"],
            "labels_to_ignore": [
                "CARDINAL",
                "EVENT",
                "LANGUAGE",
                "LAW",
                "MONEY",
                "ORDINAL",
                "PERCENT",
                "PRODUCT",
                "QUANTITY",
                "WORK_OF_ART",
            ],
        },
    }

    nlp_engine = NlpEngineProvider(nlp_configuration=nlp_configuration).create_engine()

    registry = RecognizerRegistry()
    registry.load_predefined_recognizers(nlp_engine=nlp_engine, languages=["en", "de"])

    return nlp_engine, registry


st_model = "obi/deid_roberta_i2b2"
st_threshold = 0.5

nlp_engine, registry = create_nlp_engine_with_transformers(st_model)
analyzer = AnalyzerEngine(
    nlp_engine=nlp_engine,
    registry=registry,
    supported_languages=["en"],
)
anonymizer = AnonymizerEngine()


def anonymize_text(text: Any):

    if not isinstance(text, str):
        return text

    result = analyzer.analyze(
        text,
        language="de",
        entities=list(analyzer.get_supported_entities() + ["GENERIC_PII"]),
        score_threshold=st_threshold,
        return_decision_process=False,
    )
    warnings.simplefilter("ignore")
    anonymized = anonymizer.anonymize(
        text,
        result,
        operators={"DEFAULT": OperatorConfig("custom", {"lambda": lambda x: "***"})},
    )
    return anonymized.text


# Create new `pandas` methods which use `tqdm` progress
# (can use tqdm_gui, optional kwargs, etc.)
tqdm.pandas()

def anonymize_csv(input: Path, output: Path):
    import pandas as pd

    df = pd.read_csv(input, sep=";")
    to_anonymize = [
        "Requester",
        "Affected End User",
        "summary",
        "description",
        "Assignee",
    ]
    for column in to_anonymize:
        df[column] = df[column].progress_map(anonymize_text)
    print(df.columns)
    print(df["description"].head())
    df.to_csv(output, sep=";")


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="anonymize_csv",
        description="Anonymize a CSV file",
    )
    parser.add_argument("input", type=Path, help="Input CSV file")
    parser.add_argument("output", type=Path, help="Output CSV file")
    args = parser.parse_args()
    anonymize_csv(args.input, args.output)
