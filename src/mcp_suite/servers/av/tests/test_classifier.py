"""
Tests for the classifier module in the audio/video server.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from assemblyai import Transcript

from mcp_suite.servers.av.lib.classifier import (
    Classifier,
    RelevanceClassifier,
    classify_transcript_paragraphs,
    filter_paragraphs_by_criteria,
    filter_relevant_paragraphs,
    get_cohesive_transcript_paragraphs,
)


class TestClassifierModels:
    """Tests for the classifier model classes."""

    def test_classifier_base_model(self):
        """Test the base Classifier model."""
        classifier = Classifier()
        assert classifier is not None
        assert classifier.model_config.get("arbitrary_types_allowed") is True

    def test_relevance_classifier(self):
        """Test the RelevanceClassifier model."""
        # Test default values
        classifier = RelevanceClassifier()
        assert classifier.relevant is False
        assert classifier.reasoning == ""

        # Test with custom values
        classifier = RelevanceClassifier(
            relevant=True, reasoning="This content is informative"
        )
        assert classifier.relevant is True
        assert classifier.reasoning == "This content is informative"


class TestFilterFunctions:
    """Tests for the filter functions in the classifier module."""

    def test_filter_relevant_paragraphs(self):
        """Test filtering paragraphs based on relevance."""
        # Create sample classified paragraphs
        classified_paragraphs = [
            {
                "text": "Important content",
                "start": 0,
                "end": 1000,
                "classification": RelevanceClassifier(
                    relevant=True, reasoning="Informative"
                ),
            },
            {
                "text": "Filler content",
                "start": 1000,
                "end": 2000,
                "classification": RelevanceClassifier(
                    relevant=False, reasoning="Not informative"
                ),
            },
            {
                "text": "More important content",
                "start": 2000,
                "end": 3000,
                "classification": RelevanceClassifier(
                    relevant=True, reasoning="Very informative"
                ),
            },
        ]

        # Filter paragraphs
        result = filter_relevant_paragraphs(classified_paragraphs)

        # Assert only relevant paragraphs are returned
        assert len(result) == 2
        assert result[0]["text"] == "Important content"
        assert result[1]["text"] == "More important content"

    def test_filter_paragraphs_by_criteria(self):
        """Test filtering paragraphs using a custom criteria function."""
        # Create sample classified paragraphs
        classified_paragraphs = [
            {
                "text": "Short text",  # 10 characters
                "start": 0,
                "end": 1000,
                "classification": RelevanceClassifier(relevant=True),
            },
            {
                "text": "This is a much longer text with more than 10 characters",
                "start": 1000,
                "end": 2000,
                "classification": RelevanceClassifier(relevant=True),
            },
            {
                "text": "Short",  # 5 characters
                "start": 2000,
                "end": 3000,
                "classification": RelevanceClassifier(relevant=True),
            },
        ]

        # Define a criteria function that selects paragraphs with text longer than
        # or equal to 10 chars
        def criteria_fn(p):
            return len(p["text"]) >= 10

        # Filter paragraphs
        result = filter_paragraphs_by_criteria(classified_paragraphs, criteria_fn)

        # Assert only paragraphs meeting the criteria are returned
        assert len(result) == 2
        assert result[0]["text"] == "Short text"
        assert (
            result[1]["text"]
            == "This is a much longer text with more than 10 characters"
        )

    def test_filter_functions_with_empty_input(self):
        """Test filter functions with empty input."""
        empty_paragraphs = []

        # Test filter_relevant_paragraphs with empty input
        result = filter_relevant_paragraphs(empty_paragraphs)
        assert result == []

        # Test filter_paragraphs_by_criteria with empty input
        def criteria_fn(p):
            return True  # Any criteria

        result = filter_paragraphs_by_criteria(empty_paragraphs, criteria_fn)
        assert result == []


class TestClassifierFunctions:
    """Tests for the async classifier functions."""

    @pytest.fixture
    def mock_transcript(self):
        """Create a mock transcript with paragraphs."""
        transcript = Mock(spec=Transcript)
        paragraph1 = Mock()
        paragraph1.text = "This is the first paragraph."
        paragraph1.start = 0
        paragraph1.end = 1000

        paragraph2 = Mock()
        paragraph2.text = "This is the second paragraph."
        paragraph2.start = 1000
        paragraph2.end = 2000

        transcript.get_paragraphs.return_value = [paragraph1, paragraph2]
        return transcript

    @pytest.fixture
    def mock_empty_transcript(self):
        """Create a mock transcript with no paragraphs."""
        transcript = Mock(spec=Transcript)
        transcript.get_paragraphs.return_value = []
        return transcript

    @pytest.fixture
    def mock_runnable(self):
        """Create a mock for the LangChain runnable."""
        # Mock the classification results
        results = [
            RelevanceClassifier(relevant=True, reasoning="Informative"),
            RelevanceClassifier(relevant=False, reasoning="Not informative"),
        ]

        # Create an async mock for the abatch method
        mock = AsyncMock()
        mock.abatch.return_value = results
        return mock

    @pytest.mark.asyncio
    @patch("mcp_suite.servers.av.lib.classifier.ChatAnthropic")
    async def test_classify_transcript_paragraphs(
        self, mock_chat_anthropic, mock_transcript, mock_runnable
    ):
        """Test the classify_transcript_paragraphs function."""
        # Configure the mock to return our mock runnable
        chat_instance = mock_chat_anthropic.return_value
        chat_instance.with_structured_output.return_value = mock_runnable

        # Call the function
        result = await classify_transcript_paragraphs(
            transcript=mock_transcript,
            model_name="test-model",
            temperature=0.5,
            batch_size=5,
            prompt_template=None,
        )

        # Assert the model was initialized correctly
        mock_chat_anthropic.assert_called_once()
        assert mock_chat_anthropic.call_args[1]["model"] == "test-model"
        assert mock_chat_anthropic.call_args[1]["temperature"] == 0.5

        # Assert structured output was configured with RelevanceClassifier
        chat_instance.with_structured_output.assert_called_once_with(
            RelevanceClassifier
        )

        # Assert runnable.abatch was called with the right prompts
        expected_prompt_template = (
            "You are an educator and video tutorial expert. You are given a "
            "paragraph of text and you need to determine if it makes the cut. "
            "The paragraph is: '{text}'"
        )
        expected_prompts = [
            expected_prompt_template.format(text="This is the first paragraph."),
            expected_prompt_template.format(text="This is the second paragraph."),
        ]
        mock_runnable.abatch.assert_called_once_with(expected_prompts)

        # Assert the function returns the expected classification results
        assert len(result) == 2
        assert result[0]["text"] == "This is the first paragraph."
        assert result[0]["start"] == 0
        assert result[0]["end"] == 1000
        assert result[0]["classification"].relevant is True
        assert result[0]["classification"].reasoning == "Informative"

        assert result[1]["text"] == "This is the second paragraph."
        assert result[1]["start"] == 1000
        assert result[1]["end"] == 2000
        assert result[1]["classification"].relevant is False
        assert result[1]["classification"].reasoning == "Not informative"

    @pytest.mark.asyncio
    @patch("mcp_suite.servers.av.lib.classifier.ChatAnthropic")
    async def test_classify_transcript_paragraphs_custom_prompt(
        self, mock_chat_anthropic, mock_transcript, mock_runnable
    ):
        """Test the classify_transcript_paragraphs function with custom prompt."""
        # Configure the mock to return our mock runnable
        chat_instance = mock_chat_anthropic.return_value
        chat_instance.with_structured_output.return_value = mock_runnable

        # Call the function with custom prompt template
        custom_prompt = "Custom prompt with {text}"
        _ = await classify_transcript_paragraphs(
            transcript=mock_transcript,
            model_name="test-model",
            temperature=0.5,
            batch_size=5,
            prompt_template=custom_prompt,
        )

        # Assert the runnable.abatch was called with custom prompts
        expected_prompts = [
            custom_prompt.format(text="This is the first paragraph."),
            custom_prompt.format(text="This is the second paragraph."),
        ]
        mock_runnable.abatch.assert_called_once_with(expected_prompts)

    @pytest.mark.asyncio
    @patch("mcp_suite.servers.av.lib.classifier.ChatAnthropic")
    async def test_classify_empty_transcript(
        self, mock_chat_anthropic, mock_empty_transcript
    ):
        """Test classify_transcript_paragraphs with an empty transcript."""
        # Call the function with an empty transcript
        result = await classify_transcript_paragraphs(
            transcript=mock_empty_transcript,
            model_name="test-model",
            temperature=0.5,
            batch_size=5,
        )

        # Verify we get an empty list
        assert result == []

        # The function should return early when paragraphs is empty,
        # without ever initializing the ChatAnthropic model
        mock_chat_anthropic.assert_not_called()

    @pytest.mark.asyncio
    @patch("mcp_suite.servers.av.lib.classifier.classify_transcript_paragraphs")
    async def test_get_cohesive_transcript_paragraphs(
        self, mock_classify, mock_transcript
    ):
        """Test the legacy get_cohesive_transcript_paragraphs function."""
        # Configure mock to return sample classified paragraphs
        mock_classify.return_value = [
            {
                "text": "Important content",
                "start": 0,
                "end": 1000,
                "classification": RelevanceClassifier(
                    relevant=True, reasoning="Informative"
                ),
            },
            {
                "text": "Filler content",
                "start": 1000,
                "end": 2000,
                "classification": RelevanceClassifier(
                    relevant=False, reasoning="Not informative"
                ),
            },
        ]

        # Call the function
        result = await get_cohesive_transcript_paragraphs(
            transcript=mock_transcript,
            model_name="test-model",
            temperature=0.5,
            batch_size=5,
        )

        # Assert classify_transcript_paragraphs was called correctly
        mock_classify.assert_called_once_with(
            transcript=mock_transcript,
            model_name="test-model",
            temperature=0.5,
            batch_size=5,
        )

        # Assert only relevant paragraphs are returned
        assert len(result) == 1
        assert result[0]["text"] == "Important content"

    @pytest.mark.asyncio
    @patch("mcp_suite.servers.av.lib.classifier.classify_transcript_paragraphs")
    async def test_get_cohesive_empty_transcript(
        self, mock_classify, mock_empty_transcript
    ):
        """Test get_cohesive_transcript_paragraphs with an empty transcript."""
        # Mock classify_transcript_paragraphs to return empty list
        mock_classify.return_value = []

        # Call the function with an empty transcript
        result = await get_cohesive_transcript_paragraphs(
            transcript=mock_empty_transcript,
            model_name="test-model",
            temperature=0.5,
            batch_size=5,
        )

        # Assert classify_transcript_paragraphs was called correctly
        mock_classify.assert_called_once_with(
            transcript=mock_empty_transcript,
            model_name="test-model",
            temperature=0.5,
            batch_size=5,
        )

        # Verify we get an empty list
        assert result == []


if __name__ == "__main__":  # pragma: no cover
    pytest.main(["-xvs", __file__])
