import streamlit as st
import requests
import json
import re
import fitz  # PyMuPDF
from groq import Groq

# ═══════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
AI_MODEL = "llama-3.3-70b-versatile"

# ═══════════════════════════════════════════════════════
#  TRANSLATIONS
# ═══════════════════════════════════════════════════════

TRANSLATIONS = {
    "EN": {
        "subtitle": "Scroll through wisdom, not garbage.",
        "upload_pdf": "📁 Upload PDF",
        "pick_classic": "📚 Free Classics",
        "load_book": "📖 Load Book",
        "downloading": "Downloading...",
        "analyzing": "📚 Reading the book...",
        "building": "🧠 Building idea chain...",
        "section": "{c} / {t}",
        "idea": "idea",
        "next_chapter": "Next Chapter →",
        "complete": "🎉 Book Complete!",
        "complete_sub": "Upload another and keep scrolling.",
        "restart": "🔄 New Book",
        "landing_t": "Drop a book. Start scrolling.",
        "landing_s": "Any PDF becomes a visual journey.",
        "ai_lang": "Write all ideas in English.",
    },
    "DE": {
        "subtitle": "Scrolle durch Wissen, nicht Müll.",
        "upload_pdf": "📁 PDF hochladen",
        "pick_classic": "📚 Kostenlose Klassiker",
        "load_book": "📖 Laden",
        "downloading": "Lädt...",
        "analyzing": "📚 Buch wird gelesen...",
        "building": "🧠 Ideenkette wird gebaut...",
        "section": "{c} / {t}",
        "idea": "Idee",
        "next_chapter": "Nächstes Kapitel →",
        "complete": "🎉 Buch fertig!",
        "complete_sub": "Lade ein neues hoch.",
        "restart": "🔄 Neues Buch",
        "landing_t": "Buch hochladen. Loscrollen.",
        "landing_s": "Jedes PDF wird zur visuellen Reise.",
        "ai_lang": "Write all ideas in German.",
    },
    "UA": {
        "subtitle": "Скроль крізь мудрість, не сміття.",
        "upload_pdf": "📁 Завантажити PDF",
        "pick_classic": "📚 Безкоштовна класика",
        "load_book": "📖 Завантажити",
        "downloading": "Завантаження...",
        "analyzing": "📚 Читаю книгу...",
        "building": "🧠 Будую ланцюг ідей...",
        "section": "{c} / {t}",
        "idea": "ідея",
        "next_chapter": "Наступний розділ →",
        "complete": "🎉 Книгу завершено!",
        "complete_sub": "Завантаж нову і продовжуй.",
        "restart": "🔄 Нова книга",
        "landing_t": "Кинь книгу. Починай скролити.",
        "landing_s": "Будь-який PDF стане візуальною подорожжю.",
        "ai_lang": "Write all ideas in Ukrainian.",
    },
    "FR": {
        "subtitle": "Scrollez à travers le savoir, pas les déchets.",
        "upload_pdf": "📁 Télécharger PDF",
        "pick_classic": "📚 Classiques gratuits",
        "load_book": "📖 Charger",
        "downloading": "Téléchargement...",
        "analyzing": "📚 Lecture du livre...",
        "building": "🧠 Construction de la chaîne...",
        "section": "{c} / {t}",
        "idea": "idée",
        "next_chapter": "Chapitre suivant →",
        "complete": "🎉 Livre terminé !",
        "complete_sub": "Téléchargez-en un autre.",
        "restart": "🔄 Nouveau livre",
        "landing_t": "Déposez un livre. Commencez à scroller.",
        "landing_s": "Chaque PDF devient un voyage visuel.",
        "ai_lang": "Write all ideas in French.",
    },
}


def t(key):
    lang = st.session_state.get("lang", "EN")
    return TRANSLATIONS.get(lang, TRANSLATIONS["EN"]).get(key, key)


# ═══════════════════════════════════════════════════════
#  PAGE CONFIG
# ═══════════════════════════════════════════════════════

st.set_page_config(
    page_title="DeepScroll",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════
#  MASSIVE STYLE OVERHAUL
# ═══════════════════════════════════════════════════════

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');

    /* ── GLOBAL ── */
    .stApp {
        background-color: #050505;
        font-family: 'Space Grotesk', sans-serif;
    }

    #MainMenu, header, footer { visibility: hidden; }
    .stDeployButton { display: none; }

    /* Remove streamlit padding */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 500px !important;
    }

    /* ── HERO CARD — Image as background ── */
    .hero-card {
        position: relative;
        border-radius: 24px;
        overflow: hidden;
        margin-bottom: 12px;
        min-height: 320px;
        display: flex;
        align-items: flex-end;
        box-shadow: 0 12px 40px rgba(0,0,0,0.6);
        animation: slideUp 0.5s ease-out;
    }

    .hero-card-bg {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        z-index: 1;
    }

    /* Dark gradient overlay so text is readable */
    .hero-card-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(
            to bottom,
            rgba(0,0,0,0.1) 0%,
            rgba(0,0,0,0.3) 40%,
            rgba(0,0,0,0.85) 100%
        );
        z-index: 2;
    }

    .hero-card-content {
        position: relative;
        z-index: 3;
        padding: 30px 25px 25px 25px;
        width: 100%;
    }

    .hero-text {
        color: #ffffff;
        font-size: 1.4em;
        font-weight: 600;
        line-height: 1.5;
        text-shadow: 0 2px 8px rgba(0,0,0,0.7);
        margin-bottom: 12px;
    }

    .hero-meta {
        color: rgba(255,255,255,0.5);
        font-size: 0.8em;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .hero-mood {
        background: rgba(233, 69, 96, 0.3);
        color: #e94560;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
    }

    @keyframes slideUp {
        from { opacity: 0; transform: translateY(30px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ── CHAIN CONNECTOR ── */
    .chain-line {
        text-align: center;
        color: #e94560;
        font-size: 24px;
        margin: 4px 0;
        opacity: 0.5;
    }

    /* ── CHAPTER HEADER ── */
    .ch-title {
        color: #e94560;
        font-size: 1.8em;
        font-weight: 700;
        text-align: center;
        margin: 15px 0 5px 0;
    }

    .ch-sub {
        color: #444;
        text-align: center;
        font-size: 0.85em;
        margin-bottom: 20px;
    }

    /* ── MUSIC CONTROLS (minimal) ── */
    .music-controls {
        position: fixed;
        bottom: 70px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(20,20,20,0.95);
        border: 1px solid #222;
        border-radius: 50px;
        padding: 8px 20px;
        display: flex;
        align-items: center;
        gap: 15px;
        z-index: 999;
        backdrop-filter: blur(10px);
    }

    .music-controls button {
        background: none;
        border: none;
        color: #e94560;
        font-size: 20px;
        cursor: pointer;
        padding: 5px;
    }

    .music-controls button:hover {
        color: #ff6b81;
    }

    .music-controls input[type="range"] {
        width: 80px;
        accent-color: #e94560;
    }

    /* ── LANGUAGE SWITCHER ── */
    .lang-bar {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        display: flex;
        gap: 8px;
        z-index: 999;
    }

    .lang-btn {
        background: #111;
        border: 1px solid #333;
        color: #888;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8em;
        cursor: pointer;
        text-decoration: none;
        font-family: 'Space Grotesk', sans-serif;
    }

    .lang-btn:hover { border-color: #e94560; color: #e94560; }

    .lang-btn.active {
        border-color: #e94560;
        color: #e94560;
        background: rgba(233,69,96,0.1);
    }

    /* ── LANDING ── */
    .landing-page {
        text-align: center;
        padding: 80px 20px;
    }

    .landing-page h2 {
        color: #ddd;
        font-weight: 700;
        margin-bottom: 10px;
    }

    .landing-page p { color: #555; }

    /* ── COMPLETION ── */
    .complete-page {
        text-align: center;
        padding: 50px 20px;
    }

    .complete-page h2 { color: #e94560; }
    .complete-page p { color: #555; }

    /* ── Extra bottom padding for fixed controls ── */
    .bottom-spacer { height: 130px; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  GROQ CLIENT
# ═══════════════════════════════════════════════════════

@st.cache_resource
def get_groq_client():
    try:
        return Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        st.error(f"❌ Groq error: {e}")
        return None


client = get_groq_client()


# ═══════════════════════════════════════════════════════
#  MUSIC — Royalty free tracks
# ═══════════════════════════════════════════════════════

MOOD_TRACKS = {
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
        "https://cdn.pixabay.com/audio/2023/10/24/audio_3f4171b6f8.mp3",
        "https://cdn.pixabay.com/audio/2022/10/25/audio_380a83e40d.mp3",
    ],
    "hopeful": [
        "https://cdn.pixabay.com/audio/2023/09/04/audio_4b3fa84c5f.mp3",
        "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3",
    ],
    "intense": [
        "https://cdn.pixabay.com/audio/2024/06/13/audio_529399bf96.mp3",
        "https://cdn.pixabay.com/audio/2022/02/15/audio_1b8d58e497.mp3",
    ],
    "melancholic": [
        "https://cdn.pixabay.com/audio/2023/09/04/audio_4b3fa84c5f.mp3",
        "https://cdn.pixabay.com/audio/2022/10/25/audio_380a83e40d.mp3",
    ],
}


def get_tracks_for_mood(mood):
    return MOOD_TRACKS.get(mood.lower().strip(), MOOD_TRACKS["calm"])


# ═══════════════════════════════════════════════════════
#  IMAGES — Instant via Unsplash
# ═══════════════════════════════════════════════════════

def get_image_url(visual_prompt, index=0):
    """Get an instant photo from Unsplash based on keywords."""
    try:
        words = re.sub(r'[^\w\s]', '', visual_prompt)
        keywords = [w.lower() for w in words.split() if len(w) > 3][:3]
        query = ",".join(keywords) if keywords else "abstract"
        # Add index to get different images for different cards
        return f"https://source.unsplash.com/800x600/?{query}&sig={index}"
    except Exception:
        return f"https://source.unsplash.com/800x600/?abstract&sig={index}"


# ═══════════════════════════════════════════════════════
#  PDF & TEXT PROCESSING
# ═══════════════════════════════════════════════════════

def extract_text_from_pdf(pdf_bytes):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_text = ""
        for page in doc:
            txt = page.get_text()
            if txt:
                full_text += txt + "\n"
        doc.close()
        return full_text.strip()
    except Exception as e:
        st.error(f"❌ PDF error: {e}")
        return ""


def split_into_chapters(full_text):
    if not full_text or len(full_text) < 100:
        return ["Text too short."]

    # Strategy 1: Chapter markers
    pattern = r'(?=(?:^|\n)\s*(?:CHAPTER|Chapter|chapter)\s+[\dIVXLCDM]+)'
    parts = re.split(pattern, full_text)
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 100]
    if len(parts) >= 2:
        return parts

    # Strategy 2: Large paragraph gaps
    paragraphs = re.split(r'\n\s*\n\s*\n', full_text)
    if len(paragraphs) >= 3:
        chunks = []
        current = ""
        for para in paragraphs:
            if len(current) + len(para) > 3000 and current:
                chunks.append(current.strip())
                current = para
            else:
                current += "\n\n" + para
        if current.strip():
            chunks.append(current.strip())
        if len(chunks) >= 2:
            return chunks

    # Strategy 3: Fixed size
    return [
        full_text[i:i + 2500].strip()
        for i in range(0, len(full_text), 2500)
        if len(full_text[i:i + 2500].strip()) > 50
    ] or [full_text[:3000]]


# ═══════════════════════════════════════════════════════
#  AI FUNCTIONS
# ═══════════════════════════════════════════════════════

def generate_idea_chain(chapter_text):
    if not client:
        return [{"idea": "AI not connected.", "visual_prompt": "error", "mood": "calm"}]

    lang_inst = t("ai_lang")

    try:
        resp = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"""You create IDEA CHAINS — logical sequences of connected insights.

RULES:
- Each idea: 1-2 sentences, punchy, clear
- Ideas CONNECT logically
- Generate 4-6 ideas
- visual_prompt: 2-3 English keywords for photo search (e.g. "dark forest night", "ocean waves sunset")
- mood: one of: dark, epic, calm, mysterious, hopeful, intense, melancholic
- {lang_inst}

Return ONLY valid JSON array:
[{{"idea":"text","visual_prompt":"keywords","mood":"calm"}}]"""
                },
                {
                    "role": "user",
                    "content": f"Create idea chain:\n\n{chapter_text[:3000]}"
                }
            ],
            model=AI_MODEL,
            temperature=0.7,
            max_tokens=2000,
        )
        return parse_ai_json(resp.choices[0].message.content.strip())
    except Exception as e:
        st.warning(f"⚠️ AI error: {e}")
        return [{"idea": "Error generating ideas.", "visual_prompt": "abstract", "mood": "calm"}]


def generate_chapter_title(chapter_text):
    if not client:
        return "..."

    lang_inst = t("ai_lang")

    try:
        resp = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"Give this text a poetic title (2-5 words). {lang_inst} Return ONLY the title:\n\n{chapter_text[:1500]}"
            }],
            model=AI_MODEL,
            temperature=0.9,
            max_tokens=30,
        )
        return resp.choices[0].message.content.strip().strip('"\'')[:60]
    except Exception:
        return "..."


def parse_ai_json(raw):
    cleaned = re.sub(r'```json\s*', '', raw)
    cleaned = re.sub(r'```\s*', '', cleaned).strip()

    for attempt in [
        lambda: json.loads(cleaned),
        lambda: json.loads(re.search(r'\[.*\]', cleaned, re.DOTALL).group()),
    ]:
        try:
            result = attempt()
            if isinstance(result, list):
                return validate_chain(result)
        except (json.JSONDecodeError, AttributeError):
            continue

    objects = re.findall(r'\{[^{}]+\}', cleaned)
    result = []
    for o in objects:
        try:
            result.append(json.loads(o))
        except json.JSONDecodeError:
            continue
    if result:
        return validate_chain(result)

    return [{"idea": raw[:500], "visual_prompt": "abstract", "mood": "calm"}]


def validate_chain(chain):
    valid_moods = {"dark", "epic", "calm", "mysterious", "hopeful", "intense", "melancholic"}
    validated = []
    for item in chain:
        if not isinstance(item, dict):
            continue
        v = {
            "idea": str(item.get("idea", "...")),
            "visual_prompt": str(item.get("visual_prompt", "abstract")),
            "mood": str(item.get("mood", "calm")).lower().strip(),
        }
        if v["mood"] not in valid_moods:
            v["mood"] = "calm"
        validated.append(v)
    return validated or [{"idea": "...", "visual_prompt": "abstract", "mood": "calm"}]


# ═══════════════════════════════════════════════════════
#  FREE BOOKS
# ═══════════════════════════════════════════════════════

FREE_BOOKS = {
    "📜 Art of War — Sun Tzu": "https://www.gutenberg.org/cache/epub/132/pg132.txt",
    "🏛️ Meditations — Marcus Aurelius": "https://www.gutenberg.org/cache/epub/2680/pg2680.txt",
    "🧠 Beyond Good & Evil — Nietzsche": "https://www.gutenberg.org/cache/epub/4363/pg4363.txt",
    "👑 The Prince — Machiavelli": "https://www.gutenberg.org/cache/epub/1232/pg1232.txt",
    "📖 Frankenstein — Shelley": "https://www.gutenberg.org/cache/epub/84/pg84.txt",
    "🕳️ The Republic — Plato": "https://www.gutenberg.org/cache/epub/1497/pg1497.txt",
    "🌑 Heart of Darkness — Conrad": "https://www.gutenberg.org/cache/epub/219/pg219.txt",
}


def download_gutenberg_book(url):
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        text = resp.text

        for m in ["*** START OF", "***START OF"]:
            idx = text.find(m)
            if idx != -1:
                nl = text.find('\n', idx)
                if nl != -1:
                    text = text[nl + 1:]
                break

        for m in ["*** END OF", "***END OF", "End of the Project Gutenberg"]:
            idx = text.find(m)
            if idx != -1:
                text = text[:idx]
                break

        return text.strip()
    except Exception as e:
        st.error(f"❌ Download failed: {e}")
        return ""


# ═══════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════

def main():
    # ── Init state ──
    if "lang" not in st.session_state:
        st.session_state.lang = "EN"
    if "music_index" not in st.session_state:
        st.session_state.music_index = 0

    # ── HEADER ──
    st.markdown(
        "<h1 style='text-align:center; color:#e94560; font-size:2.5em; "
        "margin:10px 0 0 0;'>🧠 DeepScroll</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align:center; color:#444; margin:5px 0 20px 0; "
        f"font-size:0.9em;'>{t('subtitle')}</p>",
        unsafe_allow_html=True,
    )

    # ── SOURCE PICKER ──
    tab1, tab2 = st.tabs([t("upload_pdf"), t("pick_classic")])

    book_text = None

    with tab1:
        uploaded = st.file_uploader("PDF", type=["pdf"], label_visibility="collapsed")
        if uploaded:
            if "pdf_bytes" not in st.session_state:
                st.session_state.pdf_bytes = uploaded.read()
            book_text = "__PDF__"

    with tab2:
        sel = st.selectbox("Book", list(FREE_BOOKS.keys()), label_visibility="collapsed")
        if st.button(t("load_book"), use_container_width=True):
            with st.spinner(t("downloading")):
                txt = download_gutenberg_book(FREE_BOOKS[sel])
                if txt:
                    st.session_state.book_text_raw = txt
                    for k in ["chapters", "chains", "current_chapter", "pdf_bytes"]:
                        st.session_state.pop(k, None)

        if "book_text_raw" in st.session_state:
            book_text = "__GUT__"

    # ── PROCESS BOOK ──
    if book_text and "chapters" not in st.session_state:
        with st.spinner(t("analyzing")):
            raw = (
                extract_text_from_pdf(st.session_state.pdf_bytes)
                if book_text == "__PDF__"
                else st.session_state.book_text_raw
            )
            if raw:
                st.session_state.chapters = split_into_chapters(raw)
                st.session_state.current_chapter = 0
                st.session_state.chains = {}
                st.rerun()
            else:
                st.error("Empty text.")
                return

    # ── LANDING ──
    if "chapters" not in st.session_state:
        st.markdown(f"""
            <div class="landing-page">
                <p style="font-size:4em;">📖</p>
                <h2>{t('landing_t')}</h2>
                <p>{t('landing_s')}</p>
            </div>
        """, unsafe_allow_html=True)
        render_language_bar()
        return

    # ── DISPLAY ──
    chapters = st.session_state.chapters
    total = len(chapters)
    cur = st.session_state.current_chapter

    # Navigation
    n1, n2, n3 = st.columns([1, 2, 1])
    with n1:
        if cur > 0 and st.button("⬅️", use_container_width=True):
            st.session_state.current_chapter -= 1
            st.session_state.chains.pop(cur - 1, None)  # Regenerate in case of lang change
            st.rerun()
    with n2:
        st.markdown(
            f"<p style='text-align:center;color:#555;margin-top:8px;'>"
            f"{t('section').format(c=cur + 1, t=total)}</p>",
            unsafe_allow_html=True,
        )
    with n3:
        if cur < total - 1 and st.button("➡️", use_container_width=True):
            st.session_state.current_chapter += 1
            st.rerun()

    # Generate chain
    if cur not in st.session_state.chains:
        with st.spinner(t("building")):
            ch_text = chapters[cur]
            title = generate_chapter_title(ch_text)
            chain = generate_idea_chain(ch_text)
            st.session_state.chains[cur] = {"title": title, "chain": chain}

    data = st.session_state.chains[cur]

    # Chapter title
    st.markdown(f'<div class="ch-title">{data["title"]}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="ch-sub">{t("section").format(c=cur + 1, t=total)}</div>',
        unsafe_allow_html=True,
    )

    # ── IDEA CARDS (image as background!) ──
    chain = data["chain"]
    for i, node in enumerate(chain):
        idea = node["idea"]
        visual = node["visual_prompt"]
        mood = node["mood"]
        img = get_image_url(visual, index=cur * 100 + i)

        st.markdown(f"""
            <div class="hero-card">
                <img class="hero-card-bg" src="{img}" loading="lazy"
                     onerror="this.src='https://source.unsplash.com/800x600/?abstract&sig={i}'">
                <div class="hero-card-overlay"></div>
                <div class="hero-card-content">
                    <div class="hero-text">{idea}</div>
                    <div class="hero-meta">
                        <span class="hero-mood">{mood}</span>
                        <span>{t('idea')} {i + 1}/{len(chain)}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if i < len(chain) - 1:
            st.markdown('<div class="chain-line">⟱</div>', unsafe_allow_html=True)

    # ── Next chapter / Complete ──
    st.markdown("---")
    if cur < total - 1:
        if st.button(t("next_chapter"), use_container_width=True, type="primary"):
            st.session_state.current_chapter += 1
            st.rerun()
    else:
        st.markdown(f"""
            <div class="complete-page">
                <h2>{t('complete')}</h2>
                <p>{t('complete_sub')}</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button(t("restart"), use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    # ── MUSIC PLAYER (hidden, controlled via JS) ──
    if chain:
        mood = chain[0].get("mood", "calm")
        tracks = get_tracks_for_mood(mood)
        mi = st.session_state.music_index % len(tracks)
        track_url = tracks[mi]

        st.markdown(f"""
            <div class="music-controls" id="musicBar">
                <button onclick="
                    var a = document.getElementById('bgMusic');
                    if(a.paused) {{ a.play(); this.innerHTML='⏸'; }}
                    else {{ a.pause(); this.innerHTML='▶️'; }}
                ">▶️</button>
                <input type="range" min="0" max="100" value="40"
                    oninput="document.getElementById('bgMusic').volume = this.value/100">
                <button onclick="
                    var a = document.getElementById('bgMusic');
                    a.src = '{tracks[(mi + 1) % len(tracks)]}';
                    a.play();
                    document.querySelector('.music-controls button').innerHTML='⏸';
                ">⏭️</button>
            </div>
            <audio id="bgMusic" loop preload="auto">
                <source src="{track_url}" type="audio/mpeg">
            </audio>
        """, unsafe_allow_html=True)

    # ── LANGUAGE BAR ──
    render_language_bar()

    # ── Bottom spacer ──
    st.markdown('<div class="bottom-spacer"></div>', unsafe_allow_html=True)


def render_language_bar():
    """Render fixed language buttons at bottom of screen."""
    current_lang = st.session_state.get("lang", "EN")

    # We use Streamlit columns for language because JS can't change session_state
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    l1, l2, l3, l4 = st.columns(4)
    langs = [("EN", "🇬🇧", l1), ("DE", "🇩🇪", l2), ("UA", "🇺🇦", l3), ("FR", "🇫🇷", l4)]

    for code, flag, col in langs:
        with col:
            label = f"{flag} {code}"
            if code == current_lang:
                label = f"✓ {flag} {code}"
            if st.button(label, key=f"lang_{code}", use_container_width=True):
                if code != current_lang:
                    st.session_state.lang = code
                    st.session_state.pop("chains", None)
                    st.rerun()


if __name__ == "__main__":
    main()
