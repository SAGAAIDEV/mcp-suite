"""
Transcript Classifier Module

This module provides functionality to classify and filter paragraphs in a transcript
based on their relevance and coherence. It uses Claude AI to analyze each paragraph
and determine if it contains meaningful content that should be kept in the final output.

The main use case is for processing video tutorials or educational content where:
- Some paragraphs may contain stutters, filler words, or off-topic content
- You want to keep only the most informative and coherent parts
- You need to maintain the flow and educational value of the content

The module provides:
1. Classifiers - Components that analyze and label transcript paragraphs
2. Filters - Components that select paragraphs based on classification results
3. Utility functions - Helper functions for processing transcripts in batches

Example usage:
    >>> from mcp_suite.servers.av.lib.transcribe import transcribe_media
    >>> from mcp_suite.servers.av.lib.classifier import (
    >>>     classify_transcript_paragraphs,
    >>>     filter_relevant_paragraphs
    >>> )
    >>>
    >>> # First transcribe the media file
    >>> transcript = transcribe_media("/path/to/video.mov")
    >>>
    >>> # Classify the paragraphs
    >>> classified_paragraphs = await classify_transcript_paragraphs(transcript)
    >>>
    >>> # Filter to keep only relevant paragraphs
    >>> relevant_paragraphs = filter_relevant_paragraphs(classified_paragraphs)
    >>>
    >>> # Use the filtered paragraphs for further processing
    >>> for paragraph in relevant_paragraphs:
    >>>     print(f"{paragraph['start']/1000:.2f}s - "
    >>>           f"{paragraph['end']/1000:.2f}s: {paragraph['text']}")
"""

from typing import Any, Callable, Dict, List, Optional

from assemblyai import Transcript
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, ConfigDict, Field

from config.env import LLM_API_KEYS

# ----------------------
# Classification Models
# ----------------------


class Classifier(BaseModel):
    """Base model for classification results."""

    model_config = ConfigDict(arbitrary_types_allowed=True)


class RelevanceClassifier(Classifier):
    """Classifier for determining if a paragraph is relevant and coherent."""

    relevant: bool = Field(
        default=False,
        description="Is this informative content. You want to return false for "
        "information that doesn't explain anything. Look to cut stutters "
        "or anything that lacks cohesiveness. This is audio of a video "
        "tutorial. Make sure you keep the intro paragraph.",
    )
    reasoning: str = Field(
        default="", description="Your reasoning of why this text should be kept or cut"
    )


# ----------------------
# Classifier Functions
# ----------------------


async def classify_transcript_paragraphs(
    transcript: Transcript,
    model_name: str = "claude-3-7-sonnet-latest",
    temperature: float = 0.7,
    batch_size: int = 10,
    classifier_model: type = RelevanceClassifier,
    prompt_template: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Classify paragraphs in a transcript using the specified classifier model.

    Args:
        transcript: An AssemblyAI transcript object with paragraphs
        model_name: The Claude model to use
        temperature: Model temperature (0.0 to 1.0)
        batch_size: Number of paragraphs to process in each batch
        classifier_model: The Pydantic model to use for classification
        prompt_template: Optional custom prompt template. If None, a default is used.
                         Must include '{text}' as a placeholder for the paragraph text.

    Returns:
        List of dictionaries containing paragraph data and classification results

    Example:
        >>> transcript = transcribe_media("/path/to/video.mov")
        >>> results = await classify_transcript_paragraphs(transcript)
    """

    # Get paragraphs from the transcript
    paragraphs = transcript.get_paragraphs()

    if not paragraphs:
        return []
    # Initialize the model
    model = ChatAnthropic(
        model=model_name,
        anthropic_api_key=LLM_API_KEYS.ANTHROPIC_API_KEY,
        temperature=temperature,
    )

    # Create a runnable that returns the structured output
    runnable = model.with_structured_output(classifier_model)

    # Use default prompt if none provided
    if prompt_template is None:
        prompt_template = (
            "You are an educator and video tutorial expert. You are given a "
            "paragraph of text and you need to determine if it makes the cut. "
            "The paragraph is: '{text}'"
        )

    # Create prompts for each paragraph
    prompts = [prompt_template.format(text=p.text) for p in paragraphs]

    # Process in batches to avoid rate limits
    results = []
    for i in range(0, len(prompts), batch_size):
        batch_prompts = prompts[i : i + batch_size]
        batch_results = await runnable.abatch(batch_prompts)
        results.extend(batch_results)

    # Combine paragraphs with their classification results
    classified_paragraphs = []
    for i, paragraph in enumerate(paragraphs):
        classified_paragraphs.append(
            {
                "text": paragraph.text,
                "start": paragraph.start,
                "end": paragraph.end,
                "classification": results[i],
            }
        )

    return classified_paragraphs


# ----------------------
# Filter Functions
# ----------------------


def filter_relevant_paragraphs(
    classified_paragraphs: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Filter paragraphs to keep only those classified as relevant.

    Args:
        classified_paragraphs: List of paragraphs with classification results
                              from classify_transcript_paragraphs

    Returns:
        List of paragraphs that were classified as relevant
    """
    return [p for p in classified_paragraphs if p["classification"].relevant]


def filter_paragraphs_by_criteria(
    classified_paragraphs: List[Dict[str, Any]],
    criteria_fn: Callable[[Dict[str, Any]], bool],
) -> List[Dict[str, Any]]:
    """
    Filter paragraphs using a custom criteria function.

    Args:
        classified_paragraphs: List of paragraphs with classification results
        criteria_fn: Function that takes a paragraph dict and returns True if
                    the paragraph should be kept

    Returns:
        List of paragraphs that meet the criteria
    """
    return [p for p in classified_paragraphs if criteria_fn(p)]


# ----------------------
# Legacy Function (for backward compatibility)
# ----------------------


async def get_cohesive_transcript_paragraphs(
    transcript: Transcript,
    model_name: str = "claude-3-7-sonnet-latest",
    temperature: float = 0.7,
    batch_size: int = 10,
) -> List[Dict[str, Any]]:
    """
    Legacy function that classifies paragraphs and returns only the relevant ones.

    This function is maintained for backward compatibility.
    New code should use classify_transcript_paragraphs and filter_relevant_paragraphs.

    Args:
        transcript: An AssemblyAI transcript object with paragraphs
        model_name: The Claude model to use
        temperature: Model temperature (0.0 to 1.0)
        batch_size: Number of paragraphs to process in each batch

    Returns:
        List of relevant paragraphs from the transcript
    """
    classified_paragraphs = await classify_transcript_paragraphs(
        transcript=transcript,
        model_name=model_name,
        temperature=temperature,
        batch_size=batch_size,
    )

    return filter_relevant_paragraphs(classified_paragraphs)
