from __future__ import annotations #to treat type hints more efficiently.


import argparse #make it run from the command line ,, python classify.py --input facebook.json --output news.json
import json 
from pathlib import Path #to handle file paths in a platform-independent way.
from typing import Any
import sys # used mainly for error handling and exit codes.



DEFAULT_MODEL = "facebook/nllb-200-distilled-600M"
DEFAULT_LOCAL_MODEL_DIR = Path("models") / "nllb-200-distilled-600M"
DEFAULT_INPUT = "datas/classified_posts.json"
DEFAULT_OUTPUT = "datas/translated_posts.json"
TEXT_FIELD = "post_content"


LABEL_TRANSLATIONS = {
    "ус дулаан, шугам сүлжээний мэдэгдэл":"municipal utility announcements",
    "эрүүл мэнд":"health",
    "спорт, тэмцээн":"sport, competition",
    "баярын мэндчилгээ":"holiday greetings",
    "орон нутгийн мэдээ":"community news",
    "зар, сурталчилгаа":"advertisement, promotion",
    "бусад":"others",
}
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
        description="Translate Mongolian Facebook posts with a Hugging Face translation model."
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
        help=f"Where translated posts will be written. Default: {DEFAULT_OUTPUT}",
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
        "--labels-file",
        type=Path,
        help="Optional UTF-8 text file with one candidate label per line.",
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
    if model_arg:
        return model_arg
    if DEFAULT_LOCAL_MODEL_DIR.exists():
        return str(DEFAULT_LOCAL_MODEL_DIR)
    return DEFAULT_MODEL



def load_posts(input_path: Path) -> list[dict[str, Any]]:
    with input_path.open("r", encoding="utf-8") as file:
        posts = json.load(file)

    if not isinstance(posts, list):
        raise ValueError(f"{input_path} must contain a JSON list of post objects.")

    bad_items = [index for index, item in enumerate(posts) if not isinstance(item, dict)]
    if bad_items:
        raise ValueError(f"{input_path} contains non-object items at indexes: {bad_items[:5]}")

    return posts


def build_translator(model_name: str, local_only: bool):
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    except ImportError as exc:
        raise RuntimeError(missing_dependency_message()) from exc
    
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=local_only)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name, local_files_only=local_only)

    return tokenizer, model




def translate_posts( posts: list[dict[str, Any]], tokenizer, model ) -> list[dict[str, Any]]:
    translated_posts = []
    total = len(posts)

    for index, post in enumerate(posts, start=1):
        text = post["post_content"]
        post_with_translation = dict(post)
        labels=post["classification"]

        if not text:
            post_with_translation["post_content_en"] = None
        else:
            tokenizer.src_lang = "khk_Cyrl"
            inputs = tokenizer(text, return_tensors="pt" )

            translated = model.generate( **inputs, forced_bos_token_id=tokenizer.convert_tokens_to_ids("eng_Latn"))

            english = tokenizer.batch_decode(
                translated,
                skip_special_tokens=True
            )[0]

            post_with_translation["post_content_en"] = english
            post_with_translation["label_en"] = LABEL_TRANSLATIONS.get(labels["primary_label"])
            

        translated_posts.append(post_with_translation)

        if index == 1 or index == total or index % 10 == 0:
            print(f"Translated {index}/{total} posts", flush=True)

    return translated_posts




def main() -> int:
    args = parse_args()
    posts = load_posts(args.input)
    tokenizer, model = build_translator(
        model_name=resolve_model_name(args.model),
        local_only=args.local_only
    )

    translated_posts = translate_posts(
    posts=posts,
    tokenizer=tokenizer,
    model=model,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8") as f:
        json.dump(translated_posts, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(translated_posts)} translated posts to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
