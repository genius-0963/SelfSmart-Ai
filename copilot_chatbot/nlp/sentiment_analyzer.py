"""\
SmartShelf AI - Sentiment Analyzer

Sentiment analysis and aspect-based opinion mining for customer feedback.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    pipeline = None

logger = logging.getLogger(__name__)


@dataclass
class AspectSentiment:
    aspect: str
    sentiment: float
    mention_count: int
    sample_quotes: List[str]


class SentimentAnalyzer:
    """Sentiment analysis with optional aspect extraction."""

    def __init__(self, model_name: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"):
        self.model_name = model_name
        self.classifier = None
        self._model_loaded = False

        # Don't load model immediately to speed up startup
        if TRANSFORMERS_AVAILABLE:
            logger.info(f"Sentiment analyzer initialized. Model will be loaded on first use: {model_name}")
        else:
            logger.warning("Transformers not available for sentiment analysis")

        self.aspect_keywords = {
            "price": ["price", "expensive", "cheap", "cost", "overpriced", "value"],
            "quality": ["quality", "good", "bad", "poor", "excellent", "amazing"],
            "freshness": ["fresh", "stale", "spoiled", "sour", "expired"],
            "packaging": ["packaging", "package", "broken", "leaking", "damaged"],
            "taste": ["taste", "flavor", "tasty", "bland", "delicious"],
            "service": ["service", "staff", "rude", "helpful", "friendly"],
            "availability": ["out of stock", "stockout", "available", "missing", "empty shelf"],
        }

    def analyze_texts(
        self,
        texts: List[str],
        aspect_level: bool = True,
        max_samples_per_aspect: int = 3
    ) -> Dict[str, Any]:
        """Analyze sentiment for a list of texts."""
        if not texts:
            return {
                "overall_sentiment": {"score": 0.0, "label": "neutral", "distribution": {"positive": 0, "neutral": 0, "negative": 0}},
                "key_aspects": [],
                "sample_quotes": [],
            }

        per_text = [self._analyze_single(t) for t in texts]
        scores = [r["score"] for r in per_text]
        labels = [r["label"] for r in per_text]

        dist = {
            "positive": sum(1 for l in labels if l == "positive"),
            "neutral": sum(1 for l in labels if l == "neutral"),
            "negative": sum(1 for l in labels if l == "negative"),
        }

        overall_score = sum(scores) / len(scores)
        overall_label = self._score_to_label(overall_score)

        result: Dict[str, Any] = {
            "overall_sentiment": {
                "score": round(overall_score, 3),
                "label": overall_label,
                "distribution": {
                    "positive": round(dist["positive"] / len(texts) * 100, 1),
                    "neutral": round(dist["neutral"] / len(texts) * 100, 1),
                    "negative": round(dist["negative"] / len(texts) * 100, 1),
                },
                "review_count": len(texts),
            },
            "sample_quotes": self._pick_samples(texts, per_text),
        }

        if aspect_level:
            result["key_aspects"] = self._extract_aspects(texts, per_text, max_samples_per_aspect)
        else:
            result["key_aspects"] = []

        return result

    def _load_model_if_needed(self):
        """Load the sentiment model on first use."""
        if not self._model_loaded and TRANSFORMERS_AVAILABLE:
            try:
                self.classifier = pipeline("sentiment-analysis", model=self.model_name)
                self._model_loaded = True
                logger.info(f"Sentiment model loaded: {self.model_name}")
            except Exception as e:
                logger.warning(f"Failed to load sentiment model ({self.model_name}): {e}")
                self._model_loaded = True  # Don't try again

    def _analyze_single(self, text: str) -> Dict[str, Any]:
        text = (text or "").strip()
        if not text:
            return {"label": "neutral", "score": 0.0}

        # Load model on first use
        self._load_model_if_needed()

        if self.classifier:
            try:
                out = self.classifier(text[:512])[0]
                label_raw = out.get("label", "NEUTRAL").lower()
                score_raw = float(out.get("score", 0.0))

                # Normalize label to positive/neutral/negative
                if "pos" in label_raw:
                    label = "positive"
                    score = score_raw
                elif "neg" in label_raw:
                    label = "negative"
                    score = -score_raw
                else:
                    label = "neutral"
                    score = 0.0

                return {"label": label, "score": score}
            except Exception as e:
                logger.warning(f"Sentiment model inference failed: {e}")

        # Fallback: rule-based
        return self._fallback_rule_based(text)

    def _fallback_rule_based(self, text: str) -> Dict[str, Any]:
        t = text.lower()
        pos_words = ["good", "great", "excellent", "love", "amazing", "fresh", "friendly", "delicious"]
        neg_words = ["bad", "terrible", "hate", "awful", "stale", "spoiled", "rude", "expensive", "broken"]
        pos = sum(1 for w in pos_words if w in t)
        neg = sum(1 for w in neg_words if w in t)

        if pos == neg:
            return {"label": "neutral", "score": 0.0}
        if pos > neg:
            score = min(1.0, (pos - neg) / 5)
            return {"label": "positive", "score": score}
        score = -min(1.0, (neg - pos) / 5)
        return {"label": "negative", "score": score}

    def _score_to_label(self, score: float) -> str:
        if score > 0.15:
            return "positive"
        if score < -0.15:
            return "negative"
        return "neutral"

    def _pick_samples(self, texts: List[str], per_text: List[Dict[str, Any]]) -> List[str]:
        # pick up to 2 pos and 2 neg samples
        scored = list(zip(texts, per_text))
        pos = [t for t, r in scored if r["label"] == "positive"]
        neg = [t for t, r in scored if r["label"] == "negative"]
        samples = []
        samples.extend(pos[:2])
        samples.extend(neg[:2])
        return samples[:4]

    def _extract_aspects(
        self,
        texts: List[str],
        per_text: List[Dict[str, Any]],
        max_samples_per_aspect: int
    ) -> List[Dict[str, Any]]:
        aspect_buckets: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {k: [] for k in self.aspect_keywords}

        for text, sent in zip(texts, per_text):
            t = text.lower()
            for aspect, kws in self.aspect_keywords.items():
                if any(kw in t for kw in kws):
                    aspect_buckets[aspect].append((text, sent))

        aspects: List[AspectSentiment] = []
        for aspect, items in aspect_buckets.items():
            if not items:
                continue
            scores = [it[1]["score"] for it in items]
            avg = sum(scores) / len(scores)
            quotes = [it[0] for it in items[:max_samples_per_aspect]]
            aspects.append(AspectSentiment(aspect=aspect, sentiment=avg, mention_count=len(items), sample_quotes=quotes))

        aspects.sort(key=lambda a: a.mention_count, reverse=True)
        return [
            {
                "aspect": a.aspect,
                "sentiment": round(a.sentiment, 3),
                "mention_count": a.mention_count,
                "sample_quotes": a.sample_quotes,
            }
            for a in aspects
        ]
