from typing import List

import numpy as np

from semantic_router.encoders import BaseEncoder
from semantic_router.schema import DocumentSplit
from semantic_router.splitters.base import BaseSplitter


class CumulativeSimSplitter(BaseSplitter):

    """
    Called "cumulative sim" because we check the similarities of the embeddings of cumulative concatenated documents with the next document.
    """

    def __init__(
        self,
        encoder: BaseEncoder,
        name: str = "cumulative_similarity_splitter",
        score_threshold: float = 0.45,
    ):
        super().__init__(name=name, score_threshold=score_threshold, encoder=encoder)
        encoder.score_threshold = score_threshold

    def __call__(self, docs: List[str]):
        total_docs = len(docs)
        # Check if there's only a single document
        if total_docs == 1:
            raise ValueError(
                "There is only one document provided; at least two are required to determine topics based on similarity."
            )
        splits = []
        curr_split_start_idx = 0

        for idx in range(0, total_docs):
            if idx + 1 < total_docs:  # Ensure there is a next document to compare with.
                if idx == 0:
                    # On the first iteration, compare the first document directly to the second.
                    curr_split_docs = docs[idx]
                else:
                    # For subsequent iterations, compare cumulative documents up to the current one with the next.
                    curr_split_docs = "\n".join(docs[curr_split_start_idx : idx + 1])
                next_doc = docs[idx + 1]

                # Embedding and similarity calculation remains the same.
                curr_split_docs_embed = self.encoder([curr_split_docs])[0]
                next_doc_embed = self.encoder([next_doc])[0]
                curr_sim_score = np.dot(curr_split_docs_embed, next_doc_embed) / (
                    np.linalg.norm(curr_split_docs_embed)
                    * np.linalg.norm(next_doc_embed)
                )
                # Decision to split based on similarity score.
                if curr_sim_score < self.score_threshold:
                    splits.append(
                        DocumentSplit(
                            docs=list(docs[curr_split_start_idx : idx + 1]),
                            is_triggered=True,
                            triggered_score=curr_sim_score,
                        )
                    )
                    curr_split_start_idx = (
                        idx + 1
                    )  # Update the start index for the next segment.

        # Add the last segment after the loop.
        if curr_split_start_idx < total_docs:
            splits.append(DocumentSplit(docs=list(docs[curr_split_start_idx:])))

        return splits
