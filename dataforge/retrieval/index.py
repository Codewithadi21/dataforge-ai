"""Simple scoped TF-IDF retrieval with provenance; retrieval != truth guarantee."""
from dataclasses import dataclass
from pathlib import Path
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass(frozen=True)
class Chunk:
    source_id: str
    path: str
    section: str
    text: str

class DocumentIndex:
    def __init__(self, knowledge_dir: Path) -> None:
        self.knowledge_dir = knowledge_dir.resolve()
        self.chunks: list[Chunk] = []
        self.vectorizer: TfidfVectorizer | None = None
        self.matrix = None
        self._build()

    def _build(self) -> None:
        if not self.knowledge_dir.is_dir():
            return
        for p in sorted(self.knowledge_dir.rglob("*")):
            if p.is_symlink() or not p.is_file() or p.suffix.lower() not in {".md", ".txt", ".pdf"}:
                continue
            if not p.resolve().is_relative_to(self.knowledge_dir) or p.stat().st_size > 2_000_000:
                continue
            if p.suffix.lower() == ".pdf":
                try:
                    from pypdf import PdfReader
                except ImportError:
                    continue
                pages = PdfReader(str(p)).pages
                content = "\n".join((page.extract_text() or "") for page in pages)
            else:
                content = p.read_text(encoding="utf-8")
            section = "Overview"
            segments: list[tuple[str, str]] = []
            for line in content.splitlines():
                if re.match(r"^#{1,4}\s+", line):
                    section = line.lstrip("# ").strip()
                    segments.append((section, ""))
                elif line.strip():
                    if not segments:
                        segments.append((section, ""))
                    last_title, last_content = segments[-1]
                    # Bounded paragraph chunks so large documents are not sent whole.
                    if len(last_content) + len(line) > 1000:
                        segments.append((section, line))
                    else:
                        segments[-1] = (last_title, last_content + " " + line.strip())
            rel = p.relative_to(self.knowledge_dir).as_posix()
            for i, (heading, text) in enumerate(segments):
                if len(text.strip()) >= 20:
                    self.chunks.append(Chunk(f"doc:{rel}:{i}", f"knowledge/{rel}", heading, text.strip()))
        if self.chunks:
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=20000)
            self.matrix = self.vectorizer.fit_transform([c.section + " " + c.text for c in self.chunks])

    def search(self, question: str, k: int = 3, minimum_score: float = 0.065) -> list[tuple[Chunk, float]]:
        if self.vectorizer is None or self.matrix is None:
            return []
        v = self.vectorizer.transform([question])
        scores = cosine_similarity(v, self.matrix).ravel()
        order = sorted(range(len(scores)), key=lambda i: float(scores[i]), reverse=True)
        return [(self.chunks[i], round(float(scores[i]), 4)) for i in order[:k] if scores[i] >= minimum_score]
