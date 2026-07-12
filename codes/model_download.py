from __future__ import annotations

import argparse
import sys
from pathlib import Path

from model_get_information import (
    DEFAULT_LOCAL_MODEL_DIR as DEFAULT_CLASSIFICATION_LOCAL_MODEL_DIR,
    DEFAULT_MODEL as DEFAULT_CLASSIFICATION_MODEL,
    TOKENIZER_KWARGS,
)
from model_to_tranlate import (
    DEFAULT_LOCAL_TRANSLATION_MODEL_DIR,
    DEFAULT_TRANSLATION_MODEL,
    TRANSLATION_TOKENIZER_KWARGS,
)


def missing_dependency_message() -> str:
    return (
        "Missing Hugging Face dependencies. Install them with:\n"
        "  .venv/bin/python -m pip install -r requirements.txt\n"
        "or:\n"
        "  python3 -m pip install -r requirements.txt"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Hugging Face models for classification and translation."
    )
    parser.add_argument(
        "--task",
        choices=["classification", "translation", "both"],
        default="classification",
        help="Which model to download. Default: classification",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model id for a single selected task. Use task-specific options with --task both.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for a single selected task. Use task-specific options with --task both.",
    )
    parser.add_argument(
        "--classification-model",
        default=DEFAULT_CLASSIFICATION_MODEL,
        help=f"Classification model id. Default: {DEFAULT_CLASSIFICATION_MODEL}",
    )
    parser.add_argument(
        "--classification-output-dir",
        type=Path,
        default=DEFAULT_CLASSIFICATION_LOCAL_MODEL_DIR,
        help=(
            "Local directory for the classification model. "
            f"Default: {DEFAULT_CLASSIFICATION_LOCAL_MODEL_DIR}"
        ),
    )
    parser.add_argument(
        "--translation-model",
        default=DEFAULT_TRANSLATION_MODEL,
        help=f"Translation model id. Default: {DEFAULT_TRANSLATION_MODEL}",
    )
    parser.add_argument(
        "--translation-output-dir",
        type=Path,
        default=DEFAULT_LOCAL_TRANSLATION_MODEL_DIR,
        help=(
            "Local directory for the translation model. "
            f"Default: {DEFAULT_LOCAL_TRANSLATION_MODEL_DIR}"
        ),
    )
    return parser.parse_args()


def download_model(model_name: str, output_dir: Path, task: str) -> None:
    try:
        from transformers import (
            AutoModelForSeq2SeqLM,
            AutoModelForSequenceClassification,
            AutoTokenizer,
        )
    except ImportError as exc:
        raise RuntimeError(missing_dependency_message()) from exc

    output_dir.mkdir(parents=True, exist_ok=True)

    if task == "classification":
        tokenizer = AutoTokenizer.from_pretrained(model_name, **TOKENIZER_KWARGS)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
    elif task == "translation":
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            **TRANSLATION_TOKENIZER_KWARGS,
        )
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    else:
        raise ValueError(f"Unsupported task: {task}")

    tokenizer.save_pretrained(output_dir)
    model.save_pretrained(output_dir)


def build_download_jobs(args: argparse.Namespace) -> list[tuple[str, str, Path]]:
    if args.task == "classification":
        return [
            (
                "classification",
                args.model or args.classification_model,
                args.output_dir or args.classification_output_dir,
            )
        ]

    if args.task == "translation":
        return [
            (
                "translation",
                args.model or args.translation_model,
                args.output_dir or args.translation_output_dir,
            )
        ]

    if args.model or args.output_dir:
        raise ValueError(
            "--model and --output-dir are only valid for one task. "
            "Use --classification-model, --classification-output-dir, "
            "--translation-model, and --translation-output-dir with --task both."
        )

    return [
        (
            "classification",
            args.classification_model,
            args.classification_output_dir,
        ),
        (
            "translation",
            args.translation_model,
            args.translation_output_dir,
        ),
    ]


def main() -> int:
    args = parse_args()

    try:
        jobs = build_download_jobs(args)
        for task, model_name, output_dir in jobs:
            print(f"Downloading {task} model: {model_name}")
            download_model(model_name, output_dir, task)
            print(f"Saved {model_name} to {output_dir}")
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if any(task == "classification" for task, _, _ in jobs):
        classification_dir = next(
            output_dir for task, _, output_dir in jobs if task == "classification"
        )
        print("Run classification with:")
        print(f"  .venv/bin/python model_get_information.py --model {classification_dir}")

    if any(task == "translation" for task, _, _ in jobs):
        translation_dir = next(
            output_dir for task, _, output_dir in jobs if task == "translation"
        )
        print("Run translation with:")
        print(f"  .venv/bin/python model_to_tranlate.py --model {translation_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
