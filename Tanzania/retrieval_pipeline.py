"""Repaired retrieval pipeline for the Tanzania agents task.

What was broken in the starter, and how each problem is fixed:

1. Two different embedding models. Documents were embedded with MiniLM and
   queries with e5-small-v2, so the vectors live in unrelated spaces and the
   dot product between them is meaningless. Now ONE model embeds both sides.
2. Missing e5 prefixes. e5 models expect "query: " / "passage: " prefixes.
   The starter only added "query: ". Now both sides get the right prefix.
3. 180-character chunks. A notice's title (exhibit + city), its "Access
   details" paragraph and its filler text were cut into separate fragments, so
   the best fragment was often a filler/background snippet. Every document is
   now embedded whole (they are all well under the 512-token limit).
4. The question asks for the *current access notice*, but every exhibit also
   has an "ARCHIVED BACKGROUND" twin with near-identical wording. The question
   intent (current vs. archived), the city and the exhibit name are now used to
   narrow the candidate documents before the dense ranking decides.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from flag_utils import derive_flag, load_verification_codes

ENCODER_MODEL = "intfloat/e5-small-v2"
QUERY_PREFIX = "query: "
PASSAGE_PREFIX = "passage: "
CURRENT_KIND = "CURRENT ACCESS NOTICE"

NOTICE_TITLE = re.compile(
    r"^(?P<kind>CURRENT ACCESS NOTICE|ARCHIVED BACKGROUND): "
    r"(?P<exhibit>.+), (?P<city>[^,]+)$"
)


@dataclass(frozen=True)
class Document:
    """One searchable source document."""

    document_id: str
    title: str
    text: str

    @property
    def searchable_text(self) -> str:
        """Whole-document text used for embedding."""
        return f"{self.title}\n{self.text}"


def load_corpus(corpus_path: Path) -> list[Document]:
    """Read source documents from a JSON Lines corpus.

    :param corpus_path: Corpus file supplied with the task.
    :return: Searchable documents in file order.
    """
    documents: list[Document] = []
    with corpus_path.open(encoding="utf-8") as corpus_file:
        for line in corpus_file:
            row = json.loads(line)
            documents.append(Document(row["document_id"], row["title"], row["text"]))
    return documents


def load_questions(questions_path: Path) -> list[dict[str, str]]:
    """Read the ordered retrieval questions.

    :param questions_path: JSON question file supplied with the task.
    :return: Question objects in official order.
    """
    with questions_path.open(encoding="utf-8") as questions_file:
        questions = json.load(questions_file)
    if not isinstance(questions, list):
        raise ValueError("questions.json must contain a list.")
    return questions


def parse_notice_title(title: str) -> dict[str, str] | None:
    """Split a notice title into kind, exhibit and city.

    :param title: Document title.
    :return: Metadata dict, or None for documents that are not exhibit notices.
    """
    match = NOTICE_TITLE.match(title)
    return match.groupdict() if match else None


def narrow_candidates(
    question_text: str,
    documents: list[Document],
    metadata: list[dict[str, str] | None],
) -> list[int]:
    """Use the question's stated intent to shrink the candidate set.

    Each step is applied only if it leaves at least one candidate, so an
    unusual question degrades to plain dense retrieval instead of failing.

    :param question_text: Question wording.
    :param documents: All corpus documents.
    :param metadata: Parsed notice metadata, aligned with ``documents``.
    :return: Indices of the documents that remain candidates.
    """
    lowered = question_text.lower()
    candidates = [i for i, meta in enumerate(metadata) if meta is not None]

    def keep(predicate) -> None:
        nonlocal candidates
        kept = [i for i in candidates if predicate(metadata[i])]
        if kept:
            candidates = kept

    if "current access notice" in lowered:
        keep(lambda meta: meta["kind"] == CURRENT_KIND)
    keep(lambda meta: meta["city"].lower() in lowered)
    keep(lambda meta: meta["exhibit"].lower() in lowered)

    return candidates or list(range(len(documents)))


def build_encoder() -> Any:
    """Load the single embedding model shared by queries and documents.

    :return: A SentenceTransformer instance.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(ENCODER_MODEL)


def retrieve_documents(
    documents: list[Document],
    questions: list[dict[str, str]],
    encoder: Any | None = None,
) -> list[dict[str, str]]:
    """Return one source document for every question.

    :param documents: Complete source documents (no chunking).
    :param questions: Ordered task questions.
    :param encoder: Optional encoder (defaults to e5-small-v2).
    :return: Top source document ID for each question.
    """
    encoder = encoder or build_encoder()
    document_vectors = np.asarray(
        encoder.encode(
            [PASSAGE_PREFIX + doc.searchable_text for doc in documents],
            normalize_embeddings=True,
            show_progress_bar=True,
        )
    )
    query_vectors = np.asarray(
        encoder.encode(
            [QUERY_PREFIX + question["question"] for question in questions],
            normalize_embeddings=True,
            show_progress_bar=True,
        )
    )
    similarities = query_vectors @ document_vectors.T
    metadata = [parse_notice_title(doc.title) for doc in documents]

    results: list[dict[str, str]] = []
    for question, row in zip(questions, similarities):
        candidates = narrow_candidates(question["question"], documents, metadata)
        best = max(candidates, key=lambda index: row[index])
        results.append(
            {
                "question_id": question["question_id"],
                "document_id": documents[best].document_id,
            }
        )
    return results


def parse_arguments() -> argparse.Namespace:
    """Parse command-line file locations.

    :return: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path("corpus.jsonl"))
    parser.add_argument("--questions", type=Path, default=Path("questions.json"))
    parser.add_argument("--output", type=Path, default=Path("retrieved_ids.json"))
    return parser.parse_args()


def main() -> None:
    """Run retrieval, save IDs, and print the derived flag."""
    arguments = parse_arguments()
    documents = load_corpus(arguments.corpus)
    questions = load_questions(arguments.questions)
    results = retrieve_documents(documents, questions)
    arguments.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    flag = derive_flag(results, questions, load_verification_codes(arguments.corpus))
    print(f"Saved {len(results)} results to {arguments.output}.")
    print(flag)


if __name__ == "__main__":
    main()
