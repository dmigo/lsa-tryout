import re
import asyncio
from typing import Dict, List, Any, Tuple, Optional
from collections import Counter
from bs4 import BeautifulSoup
import spacy
from textstat import flesch_reading_ease, flesch_kincaid_grade
import numpy as np


class ContentAnalyzer:
    """Advanced content analysis for SEO optimization."""

    def __init__(self):
        self.nlp = None
        self._load_nlp_model()

    def _load_nlp_model(self):
        """Load spaCy NLP model (fallback if not available)."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: spaCy model not found. Some advanced features will be limited.")
            self.nlp = None

    def analyze_content(self, html_content: str, url: str = "") -> Dict[str, Any]:
        """Comprehensive content analysis."""
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract text content
        text_content = self._extract_clean_text(soup)

        # Basic metrics
        basic_metrics = self._analyze_basic_metrics(text_content)

        # SEO-specific analysis
        seo_analysis = self._analyze_seo_elements(soup)

        # AI readiness analysis
        ai_readiness = self._analyze_ai_readiness(text_content, soup)

        # Content structure
        structure_analysis = self._analyze_content_structure(soup)

        # Readability analysis
        readability = self._analyze_readability(text_content)

        # Keyword analysis
        keyword_analysis = self._analyze_keywords(text_content)

        # Combine all analyses
        return {
            'url': url,
            'basic_metrics': basic_metrics,
            'seo_elements': seo_analysis,
            'ai_readiness': ai_readiness,
            'structure': structure_analysis,
            'readability': readability,
            'keywords': keyword_analysis,
            'overall_score': self._calculate_overall_score(
                basic_metrics, seo_analysis, ai_readiness, structure_analysis
            )
        }

    def _extract_clean_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from HTML."""
        # Remove script, style, and other non-content elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()

        # Get text and clean it
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return '\n'.join(chunk for chunk in chunks if chunk)

    def _analyze_basic_metrics(self, text: str) -> Dict[str, Any]:
        """Analyze basic content metrics."""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        paragraphs = text.split('\n\n')

        # Filter empty elements
        words = [w for w in words if w.strip()]
        sentences = [s for s in sentences if s.strip()]
        paragraphs = [p for p in paragraphs if p.strip()]

        return {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'paragraph_count': len(paragraphs),
            'avg_words_per_sentence': len(words) / len(sentences) if sentences else 0,
            'avg_sentences_per_paragraph': len(sentences) / len(paragraphs) if paragraphs else 0,
            'character_count': len(text),
            'character_count_no_spaces': len(text.replace(' ', ''))
        }

    def _analyze_seo_elements(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze SEO-specific HTML elements."""
        # Title tag
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""

        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_desc_text = meta_desc.get('content', '').strip() if meta_desc else ""

        # Meta keywords (deprecated but still worth checking)
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        meta_keywords_text = meta_keywords.get('content', '').strip() if meta_keywords else ""

        # Heading structure
        headings = {}
        for i in range(1, 7):
            h_tags = soup.find_all(f'h{i}')
            headings[f'h{i}'] = {
                'count': len(h_tags),
                'texts': [h.get_text().strip() for h in h_tags]
            }

        # Images
        images = soup.find_all('img')
        img_analysis = {
            'total_images': len(images),
            'images_with_alt': len([img for img in images if img.get('alt')]),
            'images_without_alt': len([img for img in images if not img.get('alt')]),
            'alt_texts': [img.get('alt', '') for img in images if img.get('alt')]
        }

        # Links
        links = soup.find_all('a', href=True)
        internal_links = []
        external_links = []

        for link in links:
            href = link.get('href', '')
            if href.startswith(('http://', 'https://')):
                external_links.append(href)
            elif href.startswith('/') or not href.startswith(('mailto:', 'tel:')):
                internal_links.append(href)

        return {
            'title': {
                'text': title_text,
                'length': len(title_text),
                'word_count': len(title_text.split()) if title_text else 0
            },
            'meta_description': {
                'text': meta_desc_text,
                'length': len(meta_desc_text),
                'word_count': len(meta_desc_text.split()) if meta_desc_text else 0
            },
            'meta_keywords': meta_keywords_text,
            'headings': headings,
            'images': img_analysis,
            'links': {
                'internal_count': len(internal_links),
                'external_count': len(external_links),
                'total_count': len(links)
            }
        }

    def _analyze_ai_readiness(self, text: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze content readiness for AI search engines."""
        # Question-answer format detection
        questions = re.findall(r'\b(?:what|how|why|when|where|who|which|can|could|should|will|would|is|are|do|does|did)\b[^.!?]*\?', text, re.IGNORECASE)

        # FAQ structure detection
        faq_indicators = re.findall(r'\b(?:faq|frequently asked|common questions|q&a)\b', text, re.IGNORECASE)

        # Structured data detection
        schema_scripts = soup.find_all('script', type='application/ld+json')
        faq_schema = any('FAQ' in script.get_text() for script in schema_scripts)
        qa_schema = any('QAPage' in script.get_text() for script in schema_scripts)

        # Direct answer patterns
        answer_patterns = re.findall(r'\b(?:the answer is|in summary|to summarize|in conclusion|simply put)\b', text, re.IGNORECASE)

        # List and step patterns (good for AI)
        list_patterns = len(re.findall(r'(?:^\d+\.|^[•\-*]\s|first|second|third|next|then|finally)', text, re.MULTILINE | re.IGNORECASE))

        # Entity mentions (people, places, organizations)
        entities = self._extract_entities(text) if self.nlp else []

        return {
            'question_count': len(questions),
            'questions': questions[:5],  # First 5 questions
            'has_faq_structure': len(faq_indicators) > 0,
            'faq_indicators': faq_indicators,
            'structured_data': {
                'total_schemas': len(schema_scripts),
                'has_faq_schema': faq_schema,
                'has_qa_schema': qa_schema
            },
            'answer_patterns': len(answer_patterns),
            'list_patterns': list_patterns,
            'entities': entities[:10],  # First 10 entities
            'ai_optimization_score': self._calculate_ai_score(
                len(questions), len(faq_indicators), len(schema_scripts),
                len(answer_patterns), list_patterns
            )
        }

    def _analyze_content_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze content structure and organization."""
        # Heading hierarchy
        heading_structure = self._analyze_heading_hierarchy(soup)

        # Table of contents detection
        toc_indicators = soup.find_all(['div', 'nav'], class_=re.compile(r'toc|table.*contents', re.I))

        # Content sections
        sections = soup.find_all(['section', 'article', 'div'], class_=re.compile(r'content|section|article', re.I))

        # Breadcrumbs
        breadcrumbs = soup.find_all(['nav', 'div'], class_=re.compile(r'breadcrumb', re.I))

        return {
            'heading_hierarchy': heading_structure,
            'has_table_of_contents': len(toc_indicators) > 0,
            'content_sections': len(sections),
            'has_breadcrumbs': len(breadcrumbs) > 0,
            'structure_score': self._calculate_structure_score(heading_structure, len(toc_indicators), len(sections))
        }

    def _analyze_heading_hierarchy(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze heading hierarchy for proper structure."""
        headings = []

        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                headings.append({
                    'level': i,
                    'text': heading.get_text().strip(),
                    'length': len(heading.get_text().strip())
                })

        # Check for proper hierarchy
        hierarchy_issues = []
        if headings:
            for i, heading in enumerate(headings[:-1]):
                next_heading = headings[i + 1]
                if next_heading['level'] > heading['level'] + 1:
                    hierarchy_issues.append(f"Jump from H{heading['level']} to H{next_heading['level']}")

        return {
            'total_headings': len(headings),
            'by_level': {f'h{i}': len([h for h in headings if h['level'] == i]) for i in range(1, 7)},
            'hierarchy_issues': hierarchy_issues,
            'has_h1': any(h['level'] == 1 for h in headings),
            'multiple_h1': len([h for h in headings if h['level'] == 1]) > 1
        }

    def _analyze_readability(self, text: str) -> Dict[str, Any]:
        """Analyze content readability."""
        if not text.strip():
            return {'error': 'No text content to analyze'}

        try:
            # Flesch Reading Ease
            flesch_ease = flesch_reading_ease(text)

            # Flesch-Kincaid Grade Level
            fk_grade = flesch_kincaid_grade(text)

            # Simple metrics
            words = text.split()
            sentences = re.split(r'[.!?]+', text)
            long_words = [w for w in words if len(w) > 6]

            avg_word_length = sum(len(w) for w in words) / len(words) if words else 0

            return {
                'flesch_reading_ease': round(flesch_ease, 1),
                'flesch_kincaid_grade': round(fk_grade, 1),
                'avg_word_length': round(avg_word_length, 1),
                'long_words_percentage': round(len(long_words) / len(words) * 100, 1) if words else 0,
                'readability_level': self._get_readability_level(flesch_ease)
            }

        except Exception as e:
            return {'error': f'Readability analysis failed: {str(e)}'}

    def _analyze_keywords(self, text: str) -> Dict[str, Any]:
        """Analyze keyword usage and distribution."""
        if not text.strip():
            return {}

        # Clean and tokenize text
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

        # Remove common stop words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among', 'within', 'along', 'following', 'across', 'behind', 'beyond', 'plus', 'except', 'but', 'this', 'that', 'these', 'those', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'have', 'has', 'had', 'was', 'were', 'been', 'being', 'are', 'you', 'your', 'yours', 'they', 'them', 'their', 'theirs', 'she', 'her', 'hers', 'him', 'his', 'its', 'our', 'ours', 'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'than', 'too', 'very', 'just', 'now'}

        filtered_words = [w for w in words if w not in stop_words and len(w) > 2]

        # Count word frequencies
        word_counts = Counter(filtered_words)
        total_words = len(filtered_words)

        # Get top keywords
        top_keywords = word_counts.most_common(20)

        # Analyze keyword density
        keyword_density = {}
        for word, count in top_keywords[:10]:
            density = (count / total_words) * 100
            keyword_density[word] = round(density, 2)

        return {
            'total_words': total_words,
            'unique_words': len(word_counts),
            'top_keywords': top_keywords[:10],
            'keyword_density': keyword_density,
            'vocabulary_richness': round(len(word_counts) / total_words, 3) if total_words > 0 else 0
        }

    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract named entities using spaCy."""
        if not self.nlp:
            return []

        try:
            doc = self.nlp(text[:1000000])  # Limit text length for performance
            entities = []

            for ent in doc.ents:
                if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT']:
                    entities.append({
                        'text': ent.text,
                        'label': ent.label_,
                        'description': spacy.explain(ent.label_)
                    })

            return entities

        except Exception:
            return []

    def _calculate_ai_score(self, questions: int, faq_indicators: int,
                          schemas: int, answer_patterns: int, list_patterns: int) -> float:
        """Calculate AI readiness score."""
        score = 0

        # Question score (0-30 points)
        score += min(questions * 5, 30)

        # FAQ structure (0-20 points)
        if faq_indicators > 0:
            score += 20

        # Structured data (0-25 points)
        score += min(schemas * 8, 25)

        # Answer patterns (0-15 points)
        score += min(answer_patterns * 3, 15)

        # List patterns (0-10 points)
        score += min(list_patterns * 2, 10)

        return round(min(score, 100), 1)

    def _calculate_structure_score(self, heading_hierarchy: Dict, toc_count: int, sections: int) -> float:
        """Calculate content structure score."""
        score = 0

        # Heading structure (0-40 points)
        if heading_hierarchy.get('has_h1') and not heading_hierarchy.get('multiple_h1'):
            score += 15

        total_headings = heading_hierarchy.get('total_headings', 0)
        if total_headings >= 3:
            score += 15

        if len(heading_hierarchy.get('hierarchy_issues', [])) == 0:
            score += 10

        # Table of contents (0-20 points)
        if toc_count > 0:
            score += 20

        # Content sections (0-20 points)
        if sections >= 3:
            score += 20
        elif sections >= 1:
            score += 10

        # Bonus for well-structured content
        if score >= 60 and total_headings >= 5:
            score += 20

        return round(min(score, 100), 1)

    def _calculate_overall_score(self, basic_metrics: Dict, seo_elements: Dict,
                                ai_readiness: Dict, structure: Dict) -> float:
        """Calculate overall content quality score."""
        scores = []

        # Word count score (0-25 points)
        word_count = basic_metrics.get('word_count', 0)
        if 300 <= word_count <= 2500:
            scores.append(25)
        elif word_count > 2500:
            scores.append(20)
        elif word_count >= 100:
            scores.append(15)
        else:
            scores.append(5)

        # SEO elements score (0-25 points)
        seo_score = 0
        if seo_elements.get('title', {}).get('length', 0) > 0:
            seo_score += 8
        if seo_elements.get('meta_description', {}).get('length', 0) > 0:
            seo_score += 8
        if seo_elements.get('headings', {}).get('h1', {}).get('count', 0) == 1:
            seo_score += 9
        scores.append(seo_score)

        # AI readiness score (0-25 points)
        ai_score = ai_readiness.get('ai_optimization_score', 0) / 4
        scores.append(ai_score)

        # Structure score (0-25 points)
        structure_score = structure.get('structure_score', 0) / 4
        scores.append(structure_score)

        return round(sum(scores), 1)

    def _get_readability_level(self, flesch_score: float) -> str:
        """Convert Flesch score to readability level."""
        if flesch_score >= 90:
            return "Very Easy"
        elif flesch_score >= 80:
            return "Easy"
        elif flesch_score >= 70:
            return "Fairly Easy"
        elif flesch_score >= 60:
            return "Standard"
        elif flesch_score >= 50:
            return "Fairly Difficult"
        elif flesch_score >= 30:
            return "Difficult"
        else:
            return "Very Difficult"