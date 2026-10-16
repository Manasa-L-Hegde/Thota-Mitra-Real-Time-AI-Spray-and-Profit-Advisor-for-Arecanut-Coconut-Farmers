import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

DOCS_CORPUS_DIR = settings.BASE_DIR / "docs_corpus"

# Unverified crops and unverified synthetic chemicals strictly refused by policy
UNVERIFIED_CROPS_AND_CHEMICALS = {
    "wheat", "rice", "tomato", "cotton", "potato", "onion", "sugarcane",
    "soybean", "chilli", "chili", "maize", "groundnut", "apple", "grape",
    "cabbage", "rubber", "mango", "streptomycin", "tetracycline",
    "glyphosate", "chlorpyrifos", "monocrotophos", "antibiotic",
    "antibiotics", "pesticides", "insecticide"
}

# Multilingual Kannada -> English agronomy & system vocabulary mappings for accurate retrieval
BILINGUAL_SYNONYMS = {
    "ಕೊಳೆರೋಗ": "koleroga fruit rot mahali phytophthora outbreak",
    "ಕೊಳೆ ರೋಗ": "koleroga fruit rot mahali phytophthora outbreak",
    "ಮಹಾಲಿ": "mahali koleroga fruit rot phytophthora meadii",
    "ಬೋರ್ಡೋ": "bordeaux mixture copper sulphate quicklime",
    "ಬೋರ್ಡೊ": "bordeaux mixture copper sulphate quicklime",
    "ಮೈಲುತುತ್ತ": "copper sulphate blue vitriol",
    "ಸುಣ್ಣ": "quicklime lime slaked",
    "ಸುಳಿ ಕೊಳೆ": "bud rot coconut crown phytophthora palmivora",
    "ಸುಳಿಕೊಳೆ": "bud rot coconut crown phytophthora palmivora",
    "ಸಿಂಪರಣೆ": "spray spraying application bordeaux window dry",
    "ಸಿಂಪಡಣೆ": "spray spraying application bordeaux window dry",
    "ಸಿಂಪಡಿಸಬೇಕು": "spray spraying when to spray window timing schedule",
    "ಸಿಂಪಡಿಸುವುದು": "spray spraying application window timing",
    "ಸ್ಪ್ರೇ": "spray spraying spray-window window",
    "ಔಷಧಿ": "fungicide medicine copper chemical bordeaux application",
    "ಔಷಧ": "fungicide medicine copper chemical bordeaux application",
    "ಮದ್ದು": "fungicide medicine remedy treatment bordeaux spray",
    "ಗೊಬ್ಬರ": "manure fertilizer compost",
    "ಅಡಿಕೆ": "arecanut betelnut adike",
    "ತೆಂಗು": "coconut thengu",
    "ಮಳೆ": "rain monsoon rainfall precipitation dry dry-window",
    "ತೇವಾಂಶ": "humidity moisture",
    "ಹಾಳೆ": "areca sheath leaf",
    "ಜಿಗುಟು": "adhesive rosin sticker soap",
    "ಎಚ್ಚರಿಕೆ": "alert alerts notification notifications reminder outbreak",
    "ಅಲರ್ಟ್": "alert alerts notification notifications",
    "ಸೂಚನೆ": "alert reminder advice guidance notice",
    "ಜ್ಞಾಪನೆ": "reminder schedule kau 40-day notification",
    "ಸೂಚ್ಯಂಕ": "conducive index conducive-conditions score humidity",
    "ವೆಚ್ಚ": "cost expense labour wage economics cultivation",
    "ಖರ್ಚು": "cost expense economics labour",
    "ದರ": "price mandi apmc market rates modal",
    "ಬೆಲೆ": "price mandi apmc market rates",
    "ಲಾಭ": "profit yield economics break-even revenue",
    "ಆದಾಯ": "profit income yield economics revenue",
    "ಕಾರ್ಯ": "how it works system guide thota mitra",
    "ಕೆಲಸ": "how it works system guide thota mitra",
    "ಕಿಟಕಿ": "window dry-window dry spray",
    "ವೇಳಾಪಟ್ಟಿ": "schedule kau 40-day timing round",
}

STOP_WORDS = {
    "how", "what", "where", "which", "who", "whom", "this", "that", "these",
    "those", "with", "from", "into", "during", "before", "after", "above", "below",
    "to", "of", "in", "for", "on", "by", "about", "against", "between", "through",
    "the", "and", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "can", "could", "would",
    "years", "year", "month"
}

class AdvisoryRAGService:
    def __init__(self, corpus_dir: Path = DOCS_CORPUS_DIR):
        self.corpus_dir = corpus_dir
        self.chunks: List[Dict[str, Any]] = []
        self._load_corpus()

    def _load_corpus(self):
        self.chunks = []
        if not self.corpus_dir.exists():
            return

        # Read both .txt and .md files
        file_paths = sorted(list(self.corpus_dir.glob("*.txt")) + list(self.corpus_dir.glob("*.md")))

        for file_path in file_paths:
            doc_name = file_path.name
            try:
                content = file_path.read_text(encoding="utf-8")
                # Split into logical sections by markdown headers (##), numbered points, or uppercase headings
                sections = re.split(r'\n(?=[0-9]+\.|\b[A-Z\s]{4,}:|#{1,3}\s)', content)
                for sec in sections:
                    clean = sec.strip()
                    if len(clean) > 35:
                        self.chunks.append({
                            "doc_name": doc_name,
                            "file_path": str(file_path),
                            "text": clean,
                            "tokens": self._tokenize(clean)
                        })
            except Exception as exc:
                logger.error(f"Error reading {file_path}: {exc}")

    def _tokenize(self, text: str) -> set:
        words = re.findall(r'[\w]+', text.lower())
        return set(words) - STOP_WORDS

    def _expand_query(self, query: str) -> str:
        expanded = query.lower()
        # Kannada synonyms expansion
        for kn_term, en_terms in BILINGUAL_SYNONYMS.items():
            if kn_term in query:
                expanded += f" {en_terms}"

        # English phrase and intent expansions
        lower_q = query.lower()
        if any(term in lower_q for term in ["alert", "notification", "notify", "reminder"]):
            expanded += " alert alerts notification notifications reminder visual audio kn-in outbreak 40-day kau schedule spray-window"
        if any(term in lower_q for term in ["spray window", "dry window", "when to spray", "when should i spray"]):
            expanded += " spray window dry-window dry hours bordeaux 40-day kau rain wind 1.0 15 km/h"
        if any(term in lower_q for term in ["conducive", "index", "conducive index"]):
            expanded += " conducive conditions index 0 100 humidity temperature rainy cloud heuristic"
        if any(term in lower_q for term in ["how does", "how it works", "what is thota mitra"]):
            expanded += " thota mitra system guide alerts spray window bordeaux schedule"
        if any(term in lower_q for term in ["medicine", "remedy", "fungicide", "treatment"]):
            expanded += " 1% bordeaux mixture copper sulphate quicklime fungicide application"
        if any(term in lower_q for term in ["cost", "price", "profit", "mandi", "economics"]):
            expanded += " cost price profit mandi apmc economics labour wage 75% break-even"
        if any(term in lower_q for term in ["bud rot", "crown rot"]):
            expanded += " bud rot coconut crown phytophthora palmivora bordeaux paste"
        if any(term in lower_q for term in ["koleroga", "mahali", "fruit rot"]):
            expanded += " koleroga fruit rot mahali phytophthora meadii outbreak 40-50 days frontiers"

        return expanded

    def query(self, question: str, max_passages: int = 3) -> Dict[str, Any]:
        """
        Retrieves relevant passages strictly from /docs_corpus.
        Answers questions about agronomy, spray windows, alerts, schedules, and costs.
        Strictly refuses unverified chemical names or non-arecanut/coconut crops.
        """
        if not self.chunks:
            self._load_corpus()

        refusal_response = {
            "question": question,
            "found_in_corpus": False,
            "answer_en": (
                "This topic is not covered in the verified CPCRI/KAU reference corpus. "
                "We refuse to guess or recommend unverified chemicals. "
                "Please consult your local Horticulture Officer or Krishi Vigyan Kendra (KVK)."
            ),
            "answer_kn": (
                "ಈ ವಿಷಯವು ಪರಿಶೀಲಿತ CPCRI/KAU ಉಲ್ಲೇಖ ದಸ್ತಾವೇಜುಗಳಲ್ಲಿ ಒಳಗೊಂಡಿಲ್ಲ. "
                "ಪರಿಶೀಲಿಸದ ಔಷಧಿ ಅಥವಾ ವಿಷಯದ ಬಗ್ಗೆ ನಾವು ಊಹಿಸಿ ಸಲಹೆ ನೀಡುವುದಿಲ್ಲ. "
                "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಹತ್ತಿರದ ತೋಟಗಾರಿಕಾ ಇಲಾಖೆ ಅಥವಾ ಕೃಷಿ ವಿಜ್ಞಾನ ಕೇಂದ್ರವನ್ನು (KVK) ಸಂಪರ್ಕಿಸಿ."
            ),
            "sources": [],
            "passages": [],
            "refusal_reason": "NOT_FOUND_IN_CORPUS"
        }

        if not self.chunks:
            return refusal_response

        # Check for unverified crops or synthetic chemicals
        words_in_q = set(re.findall(r'[\w]+', question.lower()))
        if words_in_q & UNVERIFIED_CROPS_AND_CHEMICALS:
            return refusal_response

        expanded = self._expand_query(question)
        query_words = [
            w for w in re.findall(r'[\w]+', expanded.lower())
            if len(w) > 1 and w not in STOP_WORDS
        ]

        if not query_words:
            return refusal_response

        scored_chunks = []
        lower_q = question.lower()

        for chunk in self.chunks:
            score = 0.0
            chunk_tokens = chunk["tokens"]
            chunk_text_lower = chunk["text"].lower()

            matched_terms = [w for w in query_words if w in chunk_tokens]
            if matched_terms:
                score += float(len(matched_terms)) * 0.8

            # Targeted intent bonuses
            # 1. Alerts & Notifications
            if any(term in lower_q for term in ["alert", "notification", "reminder", "ಎಚ್ಚರಿಕೆ", "ಅಲರ್ಟ್", "ಸೂಚನೆ"]):
                if any(term in chunk_text_lower for term in ["alert", "notification", "audio", "visual", "reminder", "ಎಚ್ಚರಿಕೆ", "outbreak"]):
                    score += 4.0

            # 2. Spray window & timing
            if any(term in lower_q for term in ["spray", "window", "when", "ಸಿಂಪಡಣೆ", "ಸಿಂಪರಣೆ", "ಸಿಂಪಡಿಸಬೇಕು"]):
                if any(term in chunk_text_lower for term in ["spray", "window", "dry", "adhesion", "40 days", "schedule", "ಸಿಂಪರಣೆ"]):
                    score += 3.5

            # 3. Koleroga / Mahali / Fruit rot
            if any(term in lower_q for term in ["koleroga", "mahali", "fruit rot", "ಕೊಳೆರೋಗ", "ಮಹಾಲಿ"]):
                if any(term in chunk_text_lower for term in ["koleroga", "mahali", "fruit rot", "ಕೊಳೆರೋಗ", "phytophthora"]):
                    score += 3.5

            # 4. Bordeaux mixture preparation & medicine
            if any(term in lower_q for term in ["bordeaux", "ಬೋರ್ಡೋ", "ಮದ್ದು", "ಔಷಧ", "medicine", "copper"]):
                if any(term in chunk_text_lower for term in ["bordeaux", "copper sulphate", "quicklime", "ಬೋರ್ಡೋ", "ಮೈಲುತುತ್ತ"]):
                    score += 3.5

            # 5. Conducive index
            if any(term in lower_q for term in ["conducive", "index", "ಸೂಚ್ಯಂಕ"]):
                if any(term in chunk_text_lower for term in ["conducive", "index", "heuristic", "ಸೂಚ್ಯಂಕ"]):
                    score += 4.0

            # 6. Economics / Cost / Mandi / Profit
            if any(term in lower_q for term in ["cost", "price", "profit", "mandi", "ವೆಚ್ಚ", "ದರ", "ಬೆಲೆ", "ಲಾಭ"]):
                if any(term in chunk_text_lower for term in ["cost", "labour", "mandi", "profit", "benchmark", "ಬೆಲೆ", "ವೆಚ್ಚ"]):
                    score += 3.5

            # 7. Bud rot
            if any(term in lower_q for term in ["bud rot", "ಸುಳಿ", "crown rot"]):
                if any(term in chunk_text_lower for term in ["bud rot", "crown", "palmivora", "ಸುಳಿ"]):
                    score += 4.0

            if score >= 1.2:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        if not scored_chunks or scored_chunks[0][0] < 1.2:
            return refusal_response

        top_matches = scored_chunks[:max_passages]
        passages = [match[1]["text"] for match in top_matches]
        sources = list(dict.fromkeys(match[1]["doc_name"] for match in top_matches))

        # Check for optional LLM generation via env var
        openai_key = os.getenv("OPENAI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")

        answer_en = None
        answer_kn = None

        if openai_key or groq_key:
            try:
                answer_en, answer_kn = self._call_llm_synthesis(question, passages, openai_key or groq_key)
            except Exception as e:
                logger.warning(f"LLM synthesis failed: {e}. Falling back to direct passages.")

        # Fallback if no API key: return retrieved passages directly
        if not answer_en:
            answer_en = f"Retrieved guidance from official documents:\n\n" + "\n\n---\n\n".join(passages[:2])
            answer_kn = f"ಅಧಿಕೃತ ಕೃಷಿ ದಾಖಲೆಗಳಿಂದ ಪಡೆದ ಮಾಹಿತಿ:\n\n" + "\n\n---\n\n".join(passages[:2])

        return {
            "question": question,
            "found_in_corpus": True,
            "answer_en": answer_en,
            "answer_kn": answer_kn,
            "sources": sources,
            "passages": passages,
            "refusal_reason": None,
            "disclaimer": "Answers are generated strictly from CPCRI/KAU/UAS documents. Verify with local agricultural officers."
        }

    def _call_llm_synthesis(self, question: str, passages: List[str], api_key: str):
        import httpx
        system_prompt = (
            "You are Thota Mitra's agricultural assistant for Karnataka arecanut and coconut farmers. "
            "CRITICAL: Answer ONLY using facts directly stated in the provided reference passages. "
            "Do NOT invent or extrapolate. "
            "Provide your response in two parts separated by '---KN---': "
            "Part 1 in clear English, Part 2 in clear formal Kannada (ಕನ್ನಡ)."
        )
        context = "\n\n".join([f"Passage {i+1}:\n{p}" for i, p in enumerate(passages)])
        user_prompt = f"Passages:\n{context}\n\nFarmer Question: {question}"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini" if "sk-" in api_key else "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }
        url = "https://api.openai.com/v1/chat/completions" if "sk-" in api_key else "https://api.groq.com/openai/v1/chat/completions"

        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                result = resp.json()
                content = result["choices"][0]["message"]["content"]
                if "---KN---" in content:
                    parts = content.split("---KN---")
                    return parts[0].strip(), parts[1].strip()
                return content, content

        return None, None


advisory_service = AdvisoryRAGService()

