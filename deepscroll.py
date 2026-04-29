import streamlit as st
import requests
import requests.utils
import json
import re
import fitz  # PyMuPDF
from groq import Groq

# ═══════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
AI_MODEL = "llama-3.3-70b-versatile"

# ═══════════════════════════════════════════════════════
#  TRANSLATIONS — 4 Languages
# ═══════════════════════════════════════════════════════

TRANSLATIONS = {
    "English": {
        "title": "🧠 DeepScroll",
        "subtitle": "Doomscroll through knowledge. Chain by chain. Idea by idea.",
        "choose_source": "Choose your source:",
        "upload_pdf": "📁 Upload a PDF",
        "pick_classic": "📚 Pick a free classic",
        "load_book": "📖 Load this book",
        "downloading": "Downloading...",
        "analyzing": "📚 Analyzing the book structure...",
        "building_chain": "🧠 Building the idea chain... (~10 seconds)",
        "section_of": "Section {current} of {total}",
        "mood_label": "Mood",
        "idea_label": "idea",
        "continue_next": "📖 Continue to next section →",
        "book_complete": "🎉 You've completed this book!",
        "upload_another": "Upload another one and keep scrolling.",
        "start_over": "🔄 Start Over",
        "landing_title": "Upload a PDF or pick a classic above",
        "landing_sub": "DeepScroll will transform it into a visual, musical, scrollable chain of ideas.",
        "prev": "⬅️ Prev",
        "next": "Next ➡️",
        "language": "🌍 Language",
        "ai_language_instruction": "Write all ideas in English.",
    },
    "Deutsch": {
        "title": "🧠 DeepScroll",
        "subtitle": "Scrolle durch Wissen. Kette für Kette. Idee für Idee.",
        "choose_source": "Wähle deine Quelle:",
        "upload_pdf": "📁 PDF hochladen",
        "pick_classic": "📚 Kostenlosen Klassiker wählen",
        "load_book": "📖 Buch laden",
        "downloading": "Wird heruntergeladen...",
        "analyzing": "📚 Buchstruktur wird analysiert...",
        "building_chain": "🧠 Ideenkette wird erstellt... (~10 Sekunden)",
        "section_of": "Abschnitt {current} von {total}",
        "mood_label": "Stimmung",
        "idea_label": "Idee",
        "continue_next": "📖 Weiter zum nächsten Abschnitt →",
        "book_complete": "🎉 Du hast dieses Buch abgeschlossen!",
        "upload_another": "Lade ein weiteres hoch und scrolle weiter.",
        "start_over": "🔄 Neu starten",
        "landing_title": "Lade ein PDF hoch oder wähle einen Klassiker",
        "landing_sub": "DeepScroll verwandelt es in eine visuelle, musikalische, scrollbare Ideenkette.",
        "prev": "⬅️ Zurück",
        "next": "Weiter ➡️",
        "language": "🌍 Sprache",
        "ai_language_instruction": "Write all ideas in German (Deutsch).",
    },
    "Українська": {
        "title": "🧠 DeepScroll",
        "subtitle": "Скроль крізь знання. Ланка за ланкою. Ідея за ідеєю.",
        "choose_source": "Обери джерело:",
        "upload_pdf": "📁 Завантажити PDF",
        "pick_classic": "📚 Обрати безкоштовну класику",
        "load_book": "📖 Завантажити книгу",
        "downloading": "Завантаження...",
        "analyzing": "📚 Аналіз структури книги...",
        "building_chain": "🧠 Будую ланцюг ідей... (~10 секунд)",
        "section_of": "Розділ {current} з {total}",
        "mood_label": "Настрій",
        "idea_label": "ідея",
        "continue_next": "📖 Далі до наступного розділу →",
        "book_complete": "🎉 Ти завершив цю книгу!",
        "upload_another": "Завантаж іншу і продовжуй скролити.",
        "start_over": "🔄 Почати спочатку",
        "landing_title": "Завантаж PDF або обери класику вище",
        "landing_sub": "DeepScroll перетворить книгу у візуальний, музичний, скролюваний ланцюг ідей.",
        "prev": "⬅️ Назад",
        "next": "Далі ➡️",
        "language": "🌍 Мова",
        "ai_language_instruction": "Write all ideas in Ukrainian (Українська).",
    },
    "Français": {
        "title": "🧠 DeepScroll",
        "subtitle": "Scrollez à travers le savoir. Maillon par maillon. Idée par idée.",
        "choose_source": "Choisissez votre source :",
        "upload_pdf": "📁 Télécharger un PDF",
        "pick_classic": "📚 Choisir un classique gratuit",
        "load_book": "📖 Charger ce livre",
        "downloading": "Téléchargement...",
        "analyzing": "📚 Analyse de la structure du livre...",
        "building_chain": "🧠 Construction de la chaîne d'idées... (~10 secondes)",
        "section_of": "Section {current} sur {total}",
        "mood_label": "Ambiance",
        "idea_label": "idée",
        "continue_next": "📖 Continuer vers la section suivante →",
        "book_complete": "🎉 Vous avez terminé ce livre !",
        "upload_another": "Téléchargez-en un autre et continuez à scroller.",
        "start_over": "🔄 Recommencer",
        "landing_title": "Téléchargez un PDF ou choisissez un classique ci-dessus",
        "landing_sub": "DeepScroll le transformera en une chaîne d'idées visuelle, musicale et défilante.",
        "prev": "⬅️ Préc",
        "next": "Suiv ➡️",
        "language": "🌍 Langue",
        "ai_language_instruction": "Write all ideas in French (Français).",
    },
}


def t(key):
    """Get translation for current language."""
    lang = st.session_state.get("language", "English")
    return TRANSLATIONS.get(lang, TRANSLATIONS["English"]).get(key, key)


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

    .stApp {
        background-color: #0a0a0a;
        font-family: 'Inter', sans-serif;
    }

    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

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
        height: 250px;
        object-fit: cover;
        background-color: #111;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    .chain-connector {
        text-align: center;
        color: #e94560;
        font-size: 28px;
        margin: 5px 0;
        opacity: 0.7;
    }

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

    .idea-meta {
        margin-top: 12px;
        color: #444;
        font-size: 0.8em;
        display: flex;
        justify-content: space-between;
    }

    .landing {
        text-align: center;
        padding: 60px 20px;
        color: #555;
    }

    .landing h3 { color: #ccc; }
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
        st.error(f"❌ Could not connect to Groq: {e}")
        return None


client = get_groq_client()


# ═══════════════════════════════════════════════════════
#  MUSIC LIBRARY
# ═══════════════════════════════════════════════════════

MOOD_MUSIC = {
    "dark": "https://cdn.pixabay.com/audio/2022/10/25/audio_380a83e40d.mp3",
    "epic": "https://cdn.pixabay.com/audio/2022/02/15/audio_1b8d58e497.mp3",
    "calm": "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3",
    "mysterious": "https://cdn.pixabay.com/audio/2022/10/25/audio_380a83e40d.mp3",
    "hopeful": "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3",
    "intense": "https://cdn.pixabay.com/audio/2022/02/15/audio_1b8d58e497.mp3",
    "melancholic": "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3",
}


def get_music_url(mood):
    mood_key = mood.lower().strip()
    return MOOD_MUSIC.get(mood_key, MOOD_MUSIC["calm"])


# ═══════════════════════════════════════════════════════
#  IMAGE — Fast Unsplash instead of slow Pollinations
# ═══════════════════════════════════════════════════════

def get_image_url(visual_prompt):
    """
    Use Unsplash Source for INSTANT image loading.
    AI gives us a keyword, Unsplash gives us a photo in <1 second.
    """
    try:
        # Extract 1-2 key words for Unsplash search
        words = re.sub(r'[^\w\s]', '', visual_prompt)
        # Take first 2 meaningful words
        keywords = [w for w in words.split() if len(w) > 3][:2]
        query = ",".join(keywords) if keywords else "abstract"
        return f"https://source.unsplash.com/600x350/?{query}"
    except Exception:
        return "https://source.unsplash.com/600x350/?abstract"


# ═══════════════════════════════════════════════════════
#  PDF EXTRACTION
# ═══════════════════════════════════════════════════════

def extract_text_from_pdf(pdf_bytes):
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
    if not full_text or len(full_text) < 100:
        return ["This PDF appears to be empty or too short to process."]

    # Strategy 1: "Chapter" keyword
    pattern1 = r'(?=(?:^|\n)\s*(?:CHAPTER|Chapter|chapter)\s+[\dIVXLCDM]+)'
    parts = re.split(pattern1, full_text)
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 100]

    if len(parts) >= 2:
        return parts

    # Strategy 2: Double newlines
    paragraphs = re.split(r'\n\s*\n\s*\n', full_text)
    if len(paragraphs) >= 3:
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

    # Strategy 3: Fixed chunks
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
    if not client:
        return [{"idea": "AI not configured.", "visual_prompt": "error", "mood": "dark"}]

    lang_instruction = t("ai_language_instruction")

    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"""You create IDEA CHAINS — logical sequences of connected insights.

RULES:
- Each idea is 1-2 sentences, punchy and clear
- Ideas CONNECT logically (cause->effect, question->answer, setup->revelation)
- Generate 4-6 ideas per chapter
- visual_prompt: 1-3 English keywords for a photo search (e.g. "dark cave", "ocean sunset", "ancient library")
- mood: exactly one of: dark, epic, calm, mysterious, hopeful, intense, melancholic
- {lang_instruction}

Return ONLY a valid JSON array. No markdown, no backticks.
[{{"idea": "text", "visual_prompt": "keyword keyword", "mood": "calm"}}]"""
                },
                {
                    "role": "user",
                    "content": f"Create an idea chain:\n\n{chapter_text[:3000]}"
                }
            ],
            model=AI_MODEL,
            temperature=0.7,
            max_tokens=2000,
        )

        raw = response.choices[0].message.content.strip()
        return parse_ai_json(raw)

    except Exception as e:
        st.warning(f"⚠️ AI error: {e}")
        return [{
            "idea": "Could not generate ideas. Try refreshing.",
            "visual_prompt": "abstract knowledge",
            "mood": "calm"
        }]


def generate_chapter_title(chapter_text):
    if not client:
        return "Untitled"

    lang_instruction = t("ai_language_instruction")

    try:
        response = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": (
                    f"Give this text a short creative title (2-5 words). "
                    f"{lang_instruction} "
                    f"Return ONLY the title.\n\n{chapter_text[:1500]}"
                )
            }],
            model=AI_MODEL,
            temperature=0.9,
            max_tokens=30,
        )
        title = response.choices[0].message.content.strip().strip('"\'')
        return title[:60] if len(title) > 60 else title
    except Exception:
        return "Untitled"


def parse_ai_json(raw_text):
    cleaned = re.sub(r'```json\s*', '', raw_text)
    cleaned = re.sub(r'```\s*', '', cleaned).strip()

    # Try direct parse
    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return validate_chain(result)
    except json.JSONDecodeError:
        pass

    # Try finding array
    json_match = re.search(r'\[.*\]', cleaned, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group())
            if isinstance(result, list):
                return validate_chain(result)
        except json.JSONDecodeError:
            pass

    # Try individual objects
    objects = re.findall(r'\{[^{}]+\}', cleaned)
    if objects:
        result = []
        for obj_str in objects:
            try:
                result.append(json.loads(obj_str))
            except json.JSONDecodeError:
                continue
        if result:
            return validate_chain(result)

    return [{"idea": raw_text[:500], "visual_prompt": "abstract", "mood": "calm"}]


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

    return validated if validated else [
        {"idea": "Could not parse.", "visual_prompt": "abstract", "mood": "calm"}
    ]


# ═══════════════════════════════════════════════════════
#  FREE BOOK LIBRARY
# ═══════════════════════════════════════════════════════

FREE_BOOKS = {
    "📜 The Art of War — Sun Tzu": "https://www.gutenberg.org/cache/epub/132/pg132.txt",
    "🏛️ Meditations — Marcus Aurelius": "https://www.gutenberg.org/cache/epub/2680/pg2680.txt",
    "🧠 Beyond Good and Evil — Nietzsche": "https://www.gutenberg.org/cache/epub/4363/pg4363.txt",
    "👑 The Prince — Machiavelli": "https://www.gutenberg.org/cache/epub/1232/pg1232.txt",
    "🔬 The Origin of Species — Darwin": "https://www.gutenberg.org/cache/epub/1228/pg1228.txt",
    "📖 Frankenstein — Mary Shelley": "https://www.gutenberg.org/cache/epub/84/pg84.txt",
    "🕳️ The Republic — Plato": "https://www.gutenberg.org/cache/epub/1497/pg1497.txt",
    "🌑 Heart of Darkness — Conrad": "https://www.gutenberg.org/cache/epub/219/pg219.txt",
}


def download_gutenberg_book(url):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        text = response.text

        for marker in ["*** START OF", "***START OF"]:
            idx = text.find(marker)
            if idx != -1:
                nl = text.find('\n', idx)
                if nl != -1:
                    text = text[nl + 1:]
                break

        for marker in ["*** END OF", "***END OF", "End of the Project Gutenberg"]:
            idx = text.find(marker)
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
    # Language selector (top of page)
    if "language" not in st.session_state:
        st.session_state.language = "English"

    lang_col1, lang_col2 = st.columns([3, 1])
    with lang_col2:
        new_lang = st.selectbox(
            t("language"),
            ["English", "Deutsch", "Українська", "Français"],
            index=["English", "Deutsch", "Українська", "Français"].index(
                st.session_state.language
            ),
            label_visibility="collapsed",
        )
        if new_lang != st.session_state.language:
            st.session_state.language = new_lang
            # Clear cached chains so they regenerate in new language
            st.session_state.pop("chains", None)
            st.rerun()

    # Header
    st.markdown(
        f"<h1 style='text-align:center; color:#e94560; font-size:2.8em; "
        f"margin-bottom:0;'>{t('title')}</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align:center; color:#555; margin-top:5px; "
        f"margin-bottom:30px;'>{t('subtitle')}</p>",
        unsafe_allow_html=True,
    )

    # Source selection
    st.markdown("---")
    source = st.radio(
        t("choose_source"),
        [t("upload_pdf"), t("pick_classic")],
        horizontal=True,
        label_visibility="collapsed",
    )

    book_text = None

    if source == t("upload_pdf"):
        uploaded_file = st.file_uploader(
            "PDF", type=["pdf"], label_visibility="collapsed"
        )
        if uploaded_file:
            if "pdf_bytes" not in st.session_state:
                st.session_state.pdf_bytes = uploaded_file.read()
            book_text = "__PDF__"

    else:
        selected_book = st.selectbox(
            "Book", list(FREE_BOOKS.keys()), label_visibility="collapsed"
        )
        if st.button(t("load_book"), use_container_width=True):
            with st.spinner(t("downloading")):
                text = download_gutenberg_book(FREE_BOOKS[selected_book])
                if text:
                    st.session_state.book_text_raw = text
                    st.session_state.book_source = selected_book
                    for key in ["chapters", "chains", "current_chapter", "pdf_bytes"]:
                        st.session_state.pop(key, None)

        if "book_text_raw" in st.session_state:
            book_text = "__GUTENBERG__"

    # Process book
    if book_text and "chapters" not in st.session_state:
        with st.spinner(t("analyzing")):
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
                st.error("Could not extract text.")
                return

    # Display
    if "chapters" not in st.session_state:
        st.markdown(f"""
            <div class="landing">
                <p style="font-size:4em;">📖</p>
                <h3>{t('landing_title')}</h3>
                <p>{t('landing_sub')}</p>
            </div>
        """, unsafe_allow_html=True)
        return

    chapters = st.session_state.chapters
    total = len(chapters)
    current = st.session_state.current_chapter

    # Navigation
    st.markdown("---")
    nav1, nav2, nav3 = st.columns([1, 2, 1])

    with nav1:
        if current > 0:
            if st.button(t("prev"), use_container_width=True):
                st.session_state.current_chapter -= 1
                st.rerun()

    with nav2:
        st.markdown(
            f"<p style='text-align:center; color:#666; margin-top:8px;'>"
            f"{t('section_of').format(current=current + 1, total=total)}</p>",
            unsafe_allow_html=True,
        )

    with nav3:
        if current < total - 1:
            if st.button(t("next"), use_container_width=True):
                st.session_state.current_chapter += 1
                st.rerun()

    # Generate chain
    if current not in st.session_state.chains:
        with st.spinner(t("building_chain")):
            chapter_text = chapters[current]
            title = generate_chapter_title(chapter_text)
            chain = generate_idea_chain(chapter_text)
            st.session_state.chains[current] = {"title": title, "chain": chain}

    data = st.session_state.chains[current]

    # Chapter title
    st.markdown(
        f'<div class="chapter-title">{data["title"]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="chapter-subtitle">'
        f'{t("section_of").format(current=current + 1, total=total)}</div>',
        unsafe_allow_html=True,
    )

    # Music
    if data["chain"]:
        mood = data["chain"][0].get("mood", "calm")
        music_url = get_music_url(mood)

        st.markdown(f"""
            <div class="music-bar">
                🎵 {t('mood_label')}: <strong style="color:#e94560;">
                {mood.upper()}</strong>
                <audio controls loop style="width:100%; margin-top:10px;">
                    <source src="{music_url}" type="audio/mpeg">
                </audio>
            </div>
        """, unsafe_allow_html=True)

    # Idea cards
    chain = data["chain"]
    for i, node in enumerate(chain):
        idea = node.get("idea", "")
        visual = node.get("visual_prompt", "abstract")
        mood = node.get("mood", "calm")
        img_url = get_image_url(visual)

        st.markdown(f"""
            <div class="scroll-card">
                <img src="{img_url}"
                     alt="{visual}"
                     loading="lazy"
                     onerror="this.style.display='none'">
                <div class="idea-text">{idea}</div>
                <div class="idea-meta">
                    <span>💠 {mood}</span>
                    <span>{t('idea_label')} {i + 1} / {len(chain)}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if i < len(chain) - 1:
            st.markdown(
                '<div class="chain-connector">⟱</div>',
                unsafe_allow_html=True,
            )

    # End of chapter
    st.markdown("---")

    if current < total - 1:
        if st.button(t("continue_next"), use_container_width=True, type="primary"):
            st.session_state.current_chapter += 1
            st.rerun()
    else:
        st.markdown(f"""
            <div style="text-align:center; padding:40px; color:#e94560;">
                <h2>{t('book_complete')}</h2>
                <p style="color:#666;">{t('upload_another')}</p>
            </div>
        """, unsafe_allow_html=True)

        if st.button(t("start_over"), use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


if __name__ == "__main__":
    main()
        
