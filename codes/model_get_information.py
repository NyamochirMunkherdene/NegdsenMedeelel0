from __future__ import annotations #to treat type hints more efficiently.


import argparse #make it run from the command line ,, python classify.py --input facebook.json --output news.json
import json 
import sys # used mainly for error handling and exit codes.
from pathlib import Path #to handle file paths in a platform-independent way.
from typing import Any # to specify that a variable can be of any type, useful for functions that can return different types of data.


DEFAULT_MODEL = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
DEFAULT_LOCAL_MODEL_DIR = Path("models") / "mdeberta-v3-base-mnli-xnli"
DEFAULT_INPUT = "datas/facebook_posts.json"
DEFAULT_OUTPUT = "datas/classified_posts.json"
TEXT_FIELD = "post_content"

DEFAULT_LABELS = [
    "ус дулаан, шугам сүлжээний мэдэгдэл",
    "спорт, тэмцээн",
    "баярын мэндчилгээ",
    "орон нутгийн мэдээ",
    "зар, сурталчилгаа",
    "бусад",
]
DEFAULT_HYPOTHESIS_TEMPLATE = "Энэ нийтлэлийн ангилал нь {}."
TOKENIZER_KWARGS = {"use_fast": False}

# helper function to provide a message when Hugging Face dependencies are missing.
def missing_dependency_message() -> str:
    return (
        "Missing Hugging Face dependencies. Install them with:\n"
        "  .venv/bin/python -m pip install -r requirements.txt\n"
        "or:\n"
        "  python3 -m pip install -r requirements.txt"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify Mongolian Facebook posts with a Hugging Face zero-shot model."
    )
    #add options for input and output files, model selection, labels, hypothesis template, multi-label classification, threshold, top-k results, limit on number of posts to classify, device selection, and local-only mode.
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"JSON file created by build_dataset.py. Default: {DEFAULT_INPUT}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Where classified posts will be written. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=(
            "Hugging Face model id or local model directory. "
            f"Default: {DEFAULT_LOCAL_MODEL_DIR} if present, otherwise {DEFAULT_MODEL}"
        ),
    )
    parser.add_argument(
        "--label",
        action="append",
        dest="labels",
        help=(
            "Candidate label. Repeat this option for custom labels, for example "
            "--label 'эрүүл мэнд' --label 'спорт' --label 'бусад'."
        ),
    )
    parser.add_argument(
        "--labels-file",
        type=Path,
        help="Optional UTF-8 text file with one candidate label per line.",
    )
    parser.add_argument(
        "--hypothesis-template",
        default=DEFAULT_HYPOTHESIS_TEMPLATE,
        help=f"Zero-shot hypothesis template. Default: {DEFAULT_HYPOTHESIS_TEMPLATE}",
    )
    parser.add_argument(
        "--multi-label",
        action="store_true",
        help="Allow more than one label to be true for a post.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.35,
        help="Score threshold for selected_labels when --multi-label is used. Default: 0.35",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of scored labels to keep in the output. Default: 3",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Classify only the first N posts, useful for a quick test.",
    )
    parser.add_argument(
        "--device",
        type=int,
        default=-1,
        help="Transformers pipeline device. Use -1 for CPU, 0 for first CUDA GPU. Default: -1",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Only load a model already present on disk or in the Hugging Face cache.",
    )
    return parser.parse_args()


def resolve_model_name(model_arg: str | None) -> str:
    # model exists use it, if not download it from hugging face
    if model_arg:
        return model_arg
    if DEFAULT_LOCAL_MODEL_DIR.exists():
        return str(DEFAULT_LOCAL_MODEL_DIR)
    return DEFAULT_MODEL



def load_labels(args: argparse.Namespace) -> list[str]:
    if args.labels_file:
        labels = [
            line.strip()
            for line in args.labels_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

    elif args.labels:
        labels = args.labels
    else:
        labels = DEFAULT_LABELS

    if len(labels) < 2:
        raise ValueError("Provide at least two labels for zero-shot classification.")
    return labels




# 
def load_posts(input_path: Path) -> list[dict[str, Any]]:
    with input_path.open("r", encoding="utf-8") as file:
        posts = json.load(file)

    if not isinstance(posts, list):
        raise ValueError(f"{input_path} must contain a JSON list of post objects.")

    bad_items = [index for index, item in enumerate(posts) if not isinstance(item, dict)]
    if bad_items:
        raise ValueError(f"{input_path} contains non-object items at indexes: {bad_items[:5]}")

    return posts


def build_classifier(model_name: str, device: int, local_only: bool):
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
    except ImportError as exc:
        raise RuntimeError(missing_dependency_message()) from exc

    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        local_files_only=local_only,
        **TOKENIZER_KWARGS,
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        local_files_only=local_only,
    )
    return pipeline(
        "zero-shot-classification",
        model=model,
        tokenizer=tokenizer,
        device=device,
    )


def summarize_result( result: dict[str, Any], top_k: int, multi_label: bool, threshold: float,) -> dict[str, Any]:
    labels = result["labels"]
    scores = result["scores"]
    scored_labels = [
        {"label": label, "score": round(float(score), 4)}
        for label, score in zip(labels[:top_k], scores[:top_k])
    ]

    # when every label score is high enoug
    if multi_label:
        selected_labels = [
            label for label, score in zip(labels, scores) if float(score) >= threshold
        ]
    else:
        selected_labels = [labels[0]]

    return {
        "primary_label": labels[0],
        "primary_score": round(float(scores[0]), 4),
        "selected_labels": selected_labels,
        "top_labels": scored_labels,
    }


def classify_posts( posts: list[dict[str, Any]], classifier, labels: list[str], hypothesis_template: str, multi_label: bool, threshold: float, top_k: int,) -> list[dict[str, Any]]:
    classified_posts = []
    total = len(posts)

    for index, post in enumerate(posts, start=1):
        text = str(post.get(TEXT_FIELD) or "").strip()
        post_with_classification = dict(post)

        if not text:
            post_with_classification["classification"] = {
                "error": f"Missing or empty {TEXT_FIELD!r}.",
                "primary_label": None,
                "primary_score": None,
                "selected_labels": [],
                "top_labels": [],
            }
        else:
            result = classifier(
                text,
                candidate_labels=labels,
                hypothesis_template=hypothesis_template,
                multi_label=multi_label,
            )
            post_with_classification["classification"] = summarize_result(
                result=result,
                top_k=top_k,
                multi_label=multi_label,
                threshold=threshold,
            )

        classified_posts.append(post_with_classification)

        if index == 1 or index == total or index % 10 == 0:
            print(f"Classified {index}/{total} posts", flush=True)

    return classified_posts


def main() -> int:
    args = parse_args()

    try:
        posts = load_posts(args.input)
        labels = load_labels(args)
        model_name = resolve_model_name(args.model)
        posts_to_classify = posts[: args.limit] if args.limit else posts

        print(f"Using model: {model_name}")
        print(f"Using labels: {', '.join(labels)}")
        classifier = build_classifier(
            model_name=model_name,
            device=args.device,
            local_only=args.local_only,
        )
        classified_posts = classify_posts(
            posts=posts_to_classify,
            classifier=classifier,
            labels=labels,
            hypothesis_template=args.hypothesis_template,
            multi_label=args.multi_label,
            threshold=args.threshold,
            top_k=max(1, min(args.top_k, len(labels))),
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as file:
        json.dump(classified_posts, file, ensure_ascii=False, indent=2)

    print(f"Saved {len(classified_posts)} classified posts to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
