import streamlit as st
import requests
import requests.utils
import json
import re
import io
import fitz  # PyMuPDF
from groq import Groq

# ═══════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]  # Get from console.groq.com
AI_MODEL = "llama-3.3-70b-versatile"

# ═══════════════════════════════════════════════════════
#  PAGE SETUP
# ═══════════════════════════════════════════════════════

st.set_page_config(
    page_title="DeepScroll",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════
#  STYLING
# ═══════════════════════════════════════════════════════

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');

    /* ── Global ── */
    .stApp {
        background-color: #0a0a0a;
        font-family: 'Inter', sans-serif;
    }

    /* Hide Streamlit's default elements for cleaner look */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* ── Scroll Card ── */
    .scroll-card {
        border-radius: 20px;
        padding: 25px;
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        margin-bottom: 15px;
        border: 1px solid #0f3460;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        animation: fadeIn 0.6s ease-out;
    }

    .scroll-card img {
        width: 100%;
        border-radius: 12px;
        margin-bottom: 15px;
        min-height: 200px;
        background-color: #111;
        object-fit: cover;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ── Chain Connector ── */
    .chain-connector {
        text-align: center;
        color: #e94560;
        font-size: 28px;
        margin: 5px 0;
        opacity: 0.7;
    }

    /* ── Text ── */
    .idea-text {
        color: #e0e0e0;
        font-size: 1.25em;
        line-height: 1.7;
        font-weight: 400;
    }

    .chapter-title {
        color: #e94560;
        font-size: 2em;
        font-weight: 900;
        text-align: center;
        margin-bottom: 5px;
    }

    .chapter-subtitle {
        color: #666;
        text-align: center;
        font-size: 0.9em;
        margin-bottom: 25px;
    }

    /* ── Music Bar ── */
    .music-bar {
        background: #111;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        border: 1px solid #222;
        margin-bottom: 25px;
    }

    .music-bar audio {
        width: 100%;
        margin-top: 10px;
        border-radius: 8px;
    }

    /* ── Idea Counter ── */
    .idea-meta {
        margin-top: 12px;
        color: #444;
        font-size: 0.8em;
        display: flex;
        justify-content: space-between;
    }

    /* ── Landing Page ── */
    .landing {
        text-align: center;
        padding: 60px 20px;
        color: #555;
    }

    .landing h3 { color: #ccc; }

    /* ── Book Picker ── */
    .book-option {
        background: #111;
        border: 1px solid #222;
        border-radius: 10px;
        padding: 12px 16px;
        margin: 5px 0;
        color: #ccc;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  GROQ CLIENT (with error handling)
# ═══════════════════════════════════════════════════════

@st.cache_resource
def get_groq_client():
    """Create and cache the Groq client."""
    try:
        return Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        st.error(f"❌ Could not connect to Groq: {e}")
        return None

client = get_groq_client()


# ═══════════════════════════════════════════════════════
#  MUSIC LIBRARY (Royalty-free, mapped by mood)
# ═══════════════════════════════════════════════════════

MOOD_MUSIC = {
    "dark": [
        "https://cdn.pixabay.com/audio/2022/10/25/audio_380a83e40d.mp3",
        "https://cdn.pixabay.com/audio/2023/10/24/audio_3f4171b6f8.mp3",
    ],
    "epic": [
        "https://cdn.pixabay.com/audio/2022/02/15/audio_1b8d58e497.mp3",
        "https://cdn.pixabay.com/audio/2024/06/13/audio_529399bf96.mp3",
    ],
    "calm": [
        "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3",
        "https://cdn.pixabay.com/audio/2023/09/04/audio_4b3fa84c5f.mp3",
    ],
    "mysterious": [
        "https://cdn.pixabay.com/audio/2022/10/25/audio_380a83e40d.mp3",
        "https://cdn.pixabay.com/audio/2023/10/24/audio_3f4171b6f8.mp3",
    ],
    "hopeful": [
        "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3",
        "https://cdn.pixabay.com/audio/2023/07/19/audio_9b26e1d8c3.mp3",
    ],
    "intense": [
        "https://cdn.pixabay.com/audio/2022/02/15/audio_1b8d58e497.mp3",
        "https://cdn.pixabay.com/audio/2024/06/13/audio_529399bf96.mp3",
    ],
    "melancholic": [
        "https://cdn.pixabay.com/audio/2023/09/04/audio_4b3fa84c5f.mp3",
        "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3",
    ],
}


def get_music_url(mood):
    """Get a music URL for a given mood with fallback."""
    mood_key = mood.lower().strip()
    tracks = MOOD_MUSIC.get(mood_key, MOOD_MUSIC["calm"])
    # Try first track, if it fails the audio player just won't play
    return tracks[0] if tracks else MOOD_MUSIC["calm"][0]


# ═══════════════════════════════════════════════════════
#  PDF EXTRACTION
# ═══════════════════════════════════════════════════════

def extract_text_from_pdf(pdf_bytes):
    """Extract all text from a PDF file."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_text = ""
        for page in doc:
            page_text = page.get_text()
            if page_text:
                full_text += page_text + "\n"
        doc.close()
        return full_text.strip()
    except Exception as e:
        st.error(f"❌ Could not read PDF: {e}")
        return ""


def split_into_chapters(full_text):
    """
    Split book text into chapters using multiple strategies.
    Strategy 1: Look for 'Chapter X' patterns
    Strategy 2: Look for numbered sections
    Strategy 3: Fall back to fixed-size chunks
    """
    if not full_text or len(full_text) < 100:
        return ["This PDF appears to be empty or too short to process."]

    # Strategy 1: "Chapter" keyword
    pattern1 = r'(?=(?:^|\n)\s*(?:CHAPTER|Chapter|chapter)\s+[\dIVXLCDM]+)'
    parts = re.split(pattern1, full_text)
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 100]

    if len(parts) >= 2:
        return parts

    # Strategy 2: Double newlines (paragraph groups)
    paragraphs = re.split(r'\n\s*\n\s*\n', full_text)
    if len(paragraphs) >= 3:
        # Group paragraphs into chunks of ~3000 chars
        chunks = []
        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) > 3000 and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += "\n\n" + para
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        if len(chunks) >= 2:
            return chunks

    # Strategy 3: Fixed-size chunks (last resort)
    chunk_size = 2500
    chunks = []
    for i in range(0, len(full_text), chunk_size):
        chunk = full_text[i:i + chunk_size].strip()
        if len(chunk) > 50:
            chunks.append(chunk)

    return chunks if chunks else [full_text[:3000]]


# ═══════════════════════════════════════════════════════
#  AI FUNCTIONS
# ═══════════════════════════════════════════════════════

def generate_idea_chain(chapter_text):
    """
    THE CORE: Transform a chapter into a logical chain of connected ideas.
    Returns: list of dicts [{idea, visual_prompt, mood}, ...]
    """
    if not client:
        return [{"idea": "AI client not configured.", "visual_prompt": "error", "mood": "dark"}]

    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are a genius book analyst who creates 
IDEA CHAINS — a logical sequence of connected insights that tell 
the story of what a chapter is about.

RULES:
- Each idea is 1-2 sentences, punchy and clear
- Ideas must CONNECT logically (cause->effect, question->answer, setup->revelation)
- Generate 4-6 ideas per chapter
- visual_prompt should be a vivid scene description for an image generator (no text in images)
- mood must be exactly one of: dark, epic, calm, mysterious, hopeful, intense, melancholic

You MUST return ONLY a valid JSON array. No markdown, no backticks, no explanation.
Example format:
[{"idea": "insight here", "visual_prompt": "scene description here", "mood": "calm"}]"""
                },
                {
                    "role": "user",
                    "content": f"Create an idea chain for this text:\n\n{chapter_text[:3000]}"
                }
            ],
            model=AI_MODEL,
            temperature=0.7,
            max_tokens=2000,
        )

        raw = response.choices[0].message.content.strip()
        return parse_ai_json(raw)

    except Exception as e:
        st.warning(f"⚠️ AI call failed: {e}")
        return [{
            "idea": "Could not generate ideas for this chapter. Try refreshing.",
            "visual_prompt": "abstract geometric shapes floating in space",
            "mood": "calm"
        }]


def generate_chapter_title(chapter_text):
    """Generate a creative short title for a chapter."""
    if not client:
        return "Untitled Chapter"

    try:
        response = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": (
                    "Give this text a short, creative title (2-5 words). "
                    "Return ONLY the title, nothing else. No quotes.\n\n"
                    f"{chapter_text[:1500]}"
                )
            }],
            model=AI_MODEL,
            temperature=0.9,
            max_tokens=30,
        )
        title = response.choices[0].message.content.strip()
        # Clean up any quotes or extra formatting
        title = title.strip('"\'').strip()
        # Limit length
        if len(title) > 60:
            title = title[:60] + "..."
        return title
    except Exception:
        return "Untitled Chapter"


def parse_ai_json(raw_text):
    """
    Robustly parse JSON from AI response.
    Handles: markdown backticks, extra text, malformed JSON.
    """
    # Remove markdown code blocks if present
    cleaned = re.sub(r'```json\s*', '', raw_text)
    cleaned = re.sub(r'```\s*', '', cleaned)
    cleaned = cleaned.strip()

    # Try 1: Direct parse
    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return validate_chain(result)
    except json.JSONDecodeError:
        pass

    # Try 2: Find JSON array in the text
    json_match = re.search(r'\[.*\]', cleaned, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group())
            if isinstance(result, list):
                return validate_chain(result)
        except json.JSONDecodeError:
            pass

    # Try 3: Find individual JSON objects
    objects = re.findall(r'\{[^{}]+\}', cleaned)
    if objects:
        result = []
        for obj_str in objects:
            try:
                obj = json.loads(obj_str)
                result.append(obj)
            except json.JSONDecodeError:
                continue
        if result:
            return validate_chain(result)

    # Fallback: Return raw text as a single idea
    return [{
        "idea": raw_text[:500],
        "visual_prompt": "abstract flowing knowledge and wisdom",
        "mood": "calm"
    }]


def validate_chain(chain):
    """Ensure every item in the chain has required fields."""
    valid_moods = {"dark", "epic", "calm", "mysterious", "hopeful", "intense", "melancholic"}
    validated = []

    for item in chain:
        if not isinstance(item, dict):
            continue
        validated_item = {
            "idea": str(item.get("idea", "...")),
            "visual_prompt": str(item.get("visual_prompt", "abstract art")),
            "mood": str(item.get("mood", "calm")).lower().strip(),
        }
        if validated_item["mood"] not in valid_moods:
            validated_item["mood"] = "calm"
        validated.append(validated_item)

    return validated if validated else [{
        "idea": "Could not parse this chapter.",
        "visual_prompt": "abstract geometric pattern",
        "mood": "calm"
    }]


# ═══════════════════════════════════════════════════════
#  IMAGE GENERATION
# ═══════════════════════════════════════════════════════

def get_image_url(visual_prompt):
    """Generate an image URL via Pollinations AI (free, no API key)."""
    try:
        # Clean the prompt for URL safety
        clean_prompt = visual_prompt.replace('\n', ' ').replace('\r', ' ')
        clean_prompt = re.sub(r'[^\w\s,.-]', '', clean_prompt)  # Remove special chars
        clean_prompt = clean_prompt[:200]  # Limit length
        styled = f"{clean_prompt}, digital art, cinematic lighting, atmospheric, detailed"
        encoded = requests.utils.quote(styled)
        return f"https://image.pollinations.ai/prompt/{encoded}?width=600&height=350&nologo=true"
    except Exception:
        return "https://image.pollinations.ai/prompt/abstract%20art?width=600&height=350&nologo=true"


# ═══════════════════════════════════════════════════════
#  FREE BOOK LIBRARY (Project Gutenberg)
# ═══════════════════════════════════════════════════════

FREE_BOOKS = {
    "📜 The Art of War — Sun Tzu": "https://www.gutenberg.org/cache/epub/132/pg132.txt",
    "🏛️ Meditations — Marcus Aurelius": "https://www.gutenberg.org/cache/epub/2680/pg2680.txt",
    "🧠 Beyond Good and Evil — Nietzsche": "https://www.gutenberg.org/cache/epub/4363/pg4363.txt",
    "👑 The Prince — Machiavelli": "https://www.gutenberg.org/cache/epub/1232/pg1232.txt",
    "🔬 The Origin of Species — Darwin": "https://www.gutenberg.org/cache/epub/1228/pg1228.txt",
    "📖 Frankenstein — Mary Shelley": "https://www.gutenberg.org/cache/epub/84/pg84.txt",
    "🕳️ The Republic — Plato": "https://www.gutenberg.org/cache/epub/1497/pg1497.txt",
    "🌑 Heart of Darkness — Joseph Conrad": "https://www.gutenberg.org/cache/epub/219/pg219.txt",
}


def download_gutenberg_book(url):
    """Download a book from Project Gutenberg."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        text = response.text

        # Remove Gutenberg header/footer
        start_markers = ["*** START OF", "***START OF"]
        end_markers = ["*** END OF", "***END OF", "End of the Project Gutenberg"]

        for marker in start_markers:
            idx = text.find(marker)
            if idx != -1:
                newline_after = text.find('\n', idx)
                if newline_after != -1:
                    text = text[newline_after + 1:]
                break

        for marker in end_markers:
            idx = text.find(marker)
            if idx != -1:
                text = text[:idx]
                break

        return text.strip()
    except Exception as e:
        st.error(f"❌ Could not download book: {e}")
        return ""


# ═══════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════

def main():
    # Header
    st.markdown(
        "<h1 style='text-align:center; color:#e94560; font-size:2.8em; "
        "margin-bottom:0;'>🧠 DeepScroll</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; color:#555; margin-top:5px; "
        "margin-bottom:30px;'>Doomscroll through knowledge. "
        "Chain by chain. Idea by idea.</p>",
        unsafe_allow_html=True,
    )

    # ── Source Selection ──
    st.markdown("---")
    source = st.radio(
        "Choose your source:",
        ["📁 Upload a PDF", "📚 Pick a free classic"],
        horizontal=True,
        label_visibility="collapsed",
    )

    book_text = None

    if source == "📁 Upload a PDF":
        uploaded_file = st.file_uploader(
            "Drop your book here",
            type=["pdf"],
            label_visibility="collapsed",
        )
        if uploaded_file:
            # Read bytes once and store
            if "pdf_bytes" not in st.session_state:
                st.session_state.pdf_bytes = uploaded_file.read()
            book_text = "__PDF__"

    else:
        selected_book = st.selectbox(
            "Pick a book:",
            list(FREE_BOOKS.keys()),
            label_visibility="collapsed",
        )
        if st.button("📖 Load this book", use_container_width=True):
            with st.spinner(f"Downloading {selected_book}..."):
                text = download_gutenberg_book(FREE_BOOKS[selected_book])
                if text:
                    st.session_state.book_text_raw = text
                    st.session_state.book_source = selected_book
                    # Clear old data
                    for key in ["chapters", "chains", "current_chapter"]:
                        st.session_state.pop(key, None)

        if "book_text_raw" in st.session_state:
            book_text = "__GUTENBERG__"

    # ── Process the book ──
    if book_text and "chapters" not in st.session_state:
        with st.spinner("📚 Analyzing the book structure..."):
            if book_text == "__PDF__":
                raw_text = extract_text_from_pdf(st.session_state.pdf_bytes)
            else:
                raw_text = st.session_state.book_text_raw

            if raw_text:
                chapters = split_into_chapters(raw_text)
                st.session_state.chapters = chapters
                st.session_state.current_chapter = 0
                st.session_state.chains = {}
                st.rerun()
            else:
                st.error("Could not extract text from this file.")
                return

    # ── Display chapters ──
    if "chapters" not in st.session_state:
        # Landing page
        st.markdown("""
            <div class="landing">
                <p style="font-size:4em;">📖</p>
                <h3>Upload a PDF or pick a classic above</h3>
                <p>DeepScroll will transform it into a visual,<br>
                musical, scrollable chain of ideas.</p>
            </div>
        """, unsafe_allow_html=True)
        return

    chapters = st.session_state.chapters
    total = len(chapters)
    current = st.session_state.current_chapter

    # Navigation
    st.markdown("---")
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])

    with nav_col1:
        if current > 0:
            if st.button("⬅️ Prev", use_container_width=True):
                st.session_state.current_chapter -= 1
                st.rerun()

    with nav_col2:
        st.markdown(
            f"<p style='text-align:center; color:#666; margin-top:8px;'>"
            f"Section {current + 1} / {total}</p>",
            unsafe_allow_html=True,
        )

    with nav_col3:
        if current < total - 1:
            if st.button("Next ➡️", use_container_width=True):
                st.session_state.current_chapter += 1
                st.rerun()

    # Generate chain for current chapter if not cached
    if current not in st.session_state.chains:
        with st.spinner("🧠 Building the idea chain... This takes ~10 seconds"):
            chapter_text = chapters[current]
            title = generate_chapter_title(chapter_text)
            chain = generate_idea_chain(chapter_text)
            st.session_state.chains[current] = {
                "title": title,
                "chain": chain,
            }

    data = st.session_state.chains[current]

    # Chapter Title
    st.markdown(
        f'<div class="chapter-title">{data["title"]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="chapter-subtitle">Section {current + 1} of {total}</div>',
        unsafe_allow_html=True,
    )

    # Music Player
    if data["chain"]:
        dominant_mood = data["chain"][0].get("mood", "calm")
        music_url = get_music_url(dominant_mood)

        st.markdown(f"""
            <div class="music-bar">
                🎵 Mood: <strong style="color:#e94560;">
                {dominant_mood.upper()}</strong>
                <audio controls loop style="width:100%; margin-top:10px;">
                    <source src="{music_url}" type="audio/mpeg">
                    Your browser does not support audio.
                </audio>
            </div>
        """, unsafe_allow_html=True)

    # Idea Chain Cards
    chain = data["chain"]
    for i, node in enumerate(chain):
        idea = node.get("idea", "")
        visual = node.get("visual_prompt", "abstract art")
        mood = node.get("mood", "calm")
        img_url = get_image_url(visual)

        st.markdown(f"""
            <div class="scroll-card">
                <img src="{img_url}"
                     alt="Visual for: {idea[:50]}"
                     loading="lazy"
                     onerror="this.src='https://image.pollinations.ai/prompt/abstract%20art?width=600&height=350&nologo=true'">
                <div class="idea-text">{idea}</div>
                <div class="idea-meta">
                    <span>💠 {mood}</span>
                    <span>idea {i + 1} / {len(chain)}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Chain connector arrow
        if i < len(chain) - 1:
            st.markdown(
                '<div class="chain-connector">⟱</div>',
                unsafe_allow_html=True,
            )

    # End of chapter
    st.markdown("---")

    if current < total - 1:
        if st.button(
            "📖 Continue to next section →",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.current_chapter += 1
            st.rerun()
    else:
        st.markdown("""
            <div style="text-align:center; padding:40px; color:#e94560;">
                <h2>🎉 You've completed this book!</h2>
                <p style="color:#666;">Upload another one and keep scrolling.</p>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🔄 Start Over", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ═══════════════════════════════════════════════════════
#  RUN
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    main()
