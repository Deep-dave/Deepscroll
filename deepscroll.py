import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import re
import fitz
from groq import Groq

# ═══════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
AI_MODEL = "llama-3.3-70b-versatile"

# ═══════════════════════════════════════════════════════
#  TRANSLATIONS
# ═══════════════════════════════════════════════════════

TR = {
    "EN": {
        "sub": "Scroll wisdom. Skip the noise.",
        "upload": "📁 Upload PDF",
        "classics": "📚 Classics",
        "load": "📖 Load",
        "reading": "📚 Reading...",
        "building": "🧠 Building idea chain...",
        "next_ch": "Next Chapter →",
        "done": "🎉 Done!",
        "done_sub": "Drop another book.",
        "reset": "🔄 New Book",
        "land_t": "Drop a book. Start scrolling.",
        "land_s": "Any PDF becomes a visual journey.",
        "music": "🎵 Music",
        "tap": "tap",
        "what_means": "What it means",
        "example_label": "Example",
        "takeaway_label": "Takeaway",
        "ai": "Write hook in MAX 12 words in English. Write meaning, example, takeaway in English.",
    },
    "DE": {
        "sub": "Scrolle Wissen. Kein Lärm.",
        "upload": "📁 PDF laden",
        "classics": "📚 Klassiker",
        "load": "📖 Laden",
        "reading": "📚 Liest...",
        "building": "🧠 Baut Ideenkette...",
        "next_ch": "Weiter →",
        "done": "🎉 Fertig!",
        "done_sub": "Lade ein neues Buch.",
        "reset": "🔄 Neues Buch",
        "land_t": "Buch hochladen. Loscrollen.",
        "land_s": "Jedes PDF wird zur Reise.",
        "music": "🎵 Musik",
        "tap": "tippen",
        "what_means": "Was es bedeutet",
        "example_label": "Beispiel",
        "takeaway_label": "Fazit",
        "ai": "Write hook in MAX 12 words in German. Write meaning, example, takeaway in German.",
    },
    "UA": {
        "sub": "Скроль мудрість. Без шуму.",
        "upload": "📁 PDF",
        "classics": "📚 Класика",
        "load": "📖 Читати",
        "reading": "📚 Читаю...",
        "building": "🧠 Будую ланцюг ідей...",
        "next_ch": "Далі →",
        "done": "🎉 Готово!",
        "done_sub": "Кинь нову книгу.",
        "reset": "🔄 Нова книга",
        "land_t": "Кинь книгу. Скроль.",
        "land_s": "Будь-який PDF стане подорожжю.",
        "music": "🎵 Музика",
        "tap": "тап",
        "what_means": "Що це значить",
        "example_label": "Приклад",
        "takeaway_label": "Висновок",
        "ai": "Write hook in MAX 12 words in Ukrainian. Write meaning, example, takeaway in Ukrainian.",
    },
    "FR": {
        "sub": "Scrollez le savoir. Zéro bruit.",
        "upload": "📁 PDF",
        "classics": "📚 Classiques",
        "load": "📖 Charger",
        "reading": "📚 Lecture...",
        "building": "🧠 Construction...",
        "next_ch": "Suivant →",
        "done": "🎉 Terminé !",
        "done_sub": "Chargez un autre livre.",
        "reset": "🔄 Nouveau",
        "land_t": "Déposez un livre. Scrollez.",
        "land_s": "Chaque PDF devient un voyage.",
        "music": "🎵 Musique",
        "tap": "appuyez",
        "what_means": "Ce que ça veut dire",
        "example_label": "Exemple",
        "takeaway_label": "À retenir",
        "ai": "Write hook in MAX 12 words in French. Write meaning, example, takeaway in French.",
    },
}


def t(key):
    lang = st.session_state.get("lang", "EN")
    return TR.get(lang, TR["EN"]).get(key, key)


# ═══════════════════════════════════════════════════════
#  PAGE CONFIG
# ═══════════════════════════════════════════════════════

st.set_page_config(page_title="DeepScroll", page_icon="🧠", layout="centered")

# ═══════════════════════════════════════════════════════
#  STYLES
# ═══════════════════════════════════════════════════════

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');

    .stApp {
        background-color: #050505;
        font-family: 'Space Grotesk', sans-serif;
    }
    #MainMenu, header, footer, .stDeployButton { display: none !important; }
    .block-container { padding-top: 1rem !important; max-width: 480px !important; }

    /* ── HERO CARD ── */
    .hero {
        position: relative;
        border-radius: 22px;
        overflow: hidden;
        margin-bottom: 0;
        height: 340px;
        display: flex;
        align-items: flex-end;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        animation: pop 0.4s ease-out;
    }
    .hero-bg {
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        object-fit: cover;
        z-index: 1;
        background: #111;
    }
    .hero-grad {
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background: linear-gradient(
            to bottom,
            rgba(0,0,0,0.05) 0%,
            rgba(0,0,0,0.4) 50%,
            rgba(0,0,0,0.92) 100%
        );
        z-index: 2;
    }
    .hero-body {
        position: relative;
        z-index: 3;
        padding: 25px;
        width: 100%;
    }
    .hero-txt {
        color: #fff;
        font-size: 1.5em;
        font-weight: 700;
        line-height: 1.4;
        text-shadow: 0 2px 12px rgba(0,0,0,0.8);
    }
    .hero-foot {
        color: rgba(255,255,255,0.4);
        font-size: 0.75em;
        margin-top: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .mood-tag {
        background: rgba(233,69,96,0.25);
        color: #e94560;
        padding: 2px 10px;
        border-radius: 20px;
        font-weight: 600;
    }
    .tap-label {
        color: rgba(255,255,255,0.3);
        font-size: 0.9em;
        letter-spacing: 1px;
    }
    @keyframes pop {
        from { opacity: 0; transform: translateY(25px) scale(0.97); }
        to   { opacity: 1; transform: translateY(0) scale(1); }
    }

    /* ── EXPLANATION CARD ── */
    .explain-card {
        background: linear-gradient(145deg, #0d1117, #161b22);
        border: 1px solid #1a2332;
        border-radius: 0 0 22px 22px;
        padding: 22px 25px;
        margin-top: 0;
        margin-bottom: 10px;
        animation: slideReveal 0.4s ease-out;
        box-shadow: 0 8px 30px rgba(0,0,0,0.4);
    }
    @keyframes slideReveal {
        from {
            opacity: 0;
            transform: translateY(-15px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    .explain-section {
        margin-bottom: 16px;
    }
    .explain-section:last-child {
        margin-bottom: 0;
    }
    .explain-label {
        color: #e94560;
        font-size: 0.7em;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 5px;
    }
    .explain-text {
        color: #c8c8c8;
        font-size: 0.95em;
        line-height: 1.65;
    }

    /* ── Make expander look invisible ── */
    .stExpander {
        border: none !important;
        margin-top: -10px !important;
        margin-bottom: 0 !important;
    }
    .stExpander > details {
        border: none !important;
        background: transparent !important;
    }
    .stExpander > details > summary {
        display: none !important;
    }
    .stExpander > details[open] > summary {
        display: none !important;
    }

    /* ── OTHER ── */
    .conn {
        text-align: center;
        color: #e94560;
        font-size: 22px;
        margin: 6px 0;
        opacity: 0.4;
    }
    .ch-t {
        color: #e94560;
        font-size: 1.6em;
        font-weight: 700;
        text-align: center;
        margin: 12px 0 3px;
    }
    .ch-s {
        color: #444;
        text-align: center;
        font-size: 0.8em;
        margin-bottom: 18px;
    }
    .land {
        text-align: center;
        padding: 70px 20px;
    }
    .land h2 { color: #ccc; font-weight: 700; }
    .land p { color: #555; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  GROQ
# ═══════════════════════════════════════════════════════

@st.cache_resource
def get_groq():
    try:
        return Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        st.error(f"❌ {e}")
        return None


client = get_groq()


# ═══════════════════════════════════════════════════════
#  MUSIC
# ═══════════════════════════════════════════════════════

MUSIC = {
    "dark": [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-11.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-14.mp3",
    ],
    "epic": [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3",
    ],
    "calm": [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-12.mp3",
    ],
    "mysterious": [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-14.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
    ],
    "hopeful": [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3",
    ],
    "intense": [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
    ],
    "melancholic": [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-12.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
    ],
}


# ═══════════════════════════════════════════════════════
#  IMAGES
# ═══════════════════════════════════════════════════════

def get_image_url(prompt, idx=0):
    seed = abs(hash(prompt + str(idx))) % 100000
    return f"https://picsum.photos/seed/{seed}/800/600"


# ═══════════════════════════════════════════════════════
#  PDF
# ═══════════════════════════════════════════════════════

def extract_pdf(pdf_bytes):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text")
            if not page_text or len(page_text.strip()) < 10:
                blocks = page.get_text("blocks")
                if isinstance(blocks, list):
                    page_text = "\n".join(
                        b[4] for b in blocks
                        if isinstance(b, tuple) and len(b) > 4
                        and isinstance(b[4], str)
                    )
            if isinstance(page_text, str) and page_text.strip():
                text += page_text + "\n\n"
        doc.close()
        text = re.sub(r'\n{3,}', '\n\n', text).strip()
        return text if len(text) > 50 else ""
    except Exception as e:
        st.error(f"❌ Could not read PDF: {e}")
        return ""


def split_chapters(text):
    if not text or len(text) < 100:
        return ["Text too short."]

    for pattern in [
        r'(?=\n\s*(?:CHAPTER|Chapter)\s+[\dIVXLCDM]+)',
        r'(?=\n\s*(?:PART|Part)\s+[\dIVXLCDM]+)',
    ]:
        parts = re.split(pattern, text)
        parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 200]
        if len(parts) >= 2:
            return parts[:50]

    paras = re.split(r'\n\s*\n', text)
    if len(paras) >= 4:
        chunks, current = [], ""
        for p in paras:
            p = p.strip()
            if not p:
                continue
            if len(current) + len(p) > 2500 and len(current) > 500:
                chunks.append(current.strip())
                current = p
            else:
                current += "\n\n" + p
        if current.strip():
            chunks.append(current.strip())
        if len(chunks) >= 2:
            return chunks[:50]

    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current = [], ""
    for s in sentences:
        if len(current) + len(s) > 2500 and len(current) > 500:
            chunks.append(current.strip())
            current = s
        else:
            current += " " + s
    if current.strip():
        chunks.append(current.strip())

    return chunks[:50] if chunks else [text[:3000]]


# ═══════════════════════════════════════════════════════
#  AI
# ═══════════════════════════════════════════════════════

def make_chain(chapter_text):
    if not client:
        return [{"hook": "No AI.", "meaning": "", "example": "", "takeaway": "", "visual": "abstract", "mood": "calm"}]

    ai_lang = t("ai")

    try:
        r = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"""You summarize book chapters into scrollable cards that TEACH the reader.

Each card has 4 parts:
1. hook: Short punchy sentence (MAX 12 words). Makes reader curious.
2. meaning: What the author ACTUALLY means. 1-2 simple sentences. Faithful to the chapter.
3. example: One CONCRETE example from the book, history, or real life. 1 sentence.
4. takeaway: One short conclusion or lesson. 1 sentence.

CRITICAL RULES:
- Do NOT write vague motivational quotes
- Do NOT write generic philosophy like "power corrupts"
- EXPLAIN the actual ideas from THIS specific chapter
- Make it simple enough for a student
- The hook should make the reader want to tap for more
- The meaning should actually TEACH something new
- The example must be SPECIFIC not abstract
- Generate exactly 5 cards
- visual: 2-3 English words for a landscape/nature photo
- mood: one of: dark, epic, calm, mysterious, hopeful, intense, melancholic
- {ai_lang}

Return ONLY a JSON array:
[{{"hook":"short headline","meaning":"clear explanation","example":"specific example","takeaway":"lesson learned","visual":"photo keywords","mood":"calm"}}]

GOOD:
hook: "A prince must learn when NOT to be good."
meaning: "Machiavelli argues that always being moral makes a ruler vulnerable. Sometimes survival requires tough choices that go against conventional morality."
example: "Cesare Borgia used calculated cruelty to unify Romagna, but the result was peace and order for the people."
takeaway: "Effectiveness sometimes matters more than moral purity in leadership."

BAD:
hook: "Power is a double-edged sword." (too generic, not from the book)
meaning: "The author discusses power." (too vague, says nothing)"""
                },
                {
                    "role": "user",
                    "content": f"Summarize this chapter into idea cards:\n\n{chapter_text[:3000]}"
                }
            ],
            model=AI_MODEL,
            temperature=0.7,
            max_tokens=2000,
        )
        return parse_json(r.choices[0].message.content.strip())
    except Exception as e:
        st.warning(f"⚠️ AI error: {e}")
        return [{"hook": "Error. Refresh.", "meaning": "", "example": "", "takeaway": "", "visual": "abstract", "mood": "calm"}]


def make_title(chapter_text):
    if not client:
        return "..."
    ai_lang = t("ai")
    try:
        r = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"Poetic title, 2-4 words. {ai_lang} Return ONLY the title:\n\n{chapter_text[:1500]}"
            }],
            model=AI_MODEL,
            temperature=0.9,
            max_tokens=20,
        )
        return r.choices[0].message.content.strip().strip('"\'')[:50]
    except Exception:
        return "..."


def parse_json(raw):
    cleaned = re.sub(r'```json\s*', '', raw)
    cleaned = re.sub(r'```\s*', '', cleaned).strip()

    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return validate(result)
    except json.JSONDecodeError:
        pass

    match = re.search(r'\[.*\]', cleaned, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return validate(result)
        except json.JSONDecodeError:
            pass

    objs = []
    for o in re.findall(r'\{[^{}]+\}', cleaned):
        try:
            objs.append(json.loads(o))
        except json.JSONDecodeError:
            pass
    if objs:
        return validate(objs)

    return [{"hook": raw[:200], "meaning": "", "example": "", "takeaway": "", "visual": "abstract", "mood": "calm"}]


def validate(chain):
    moods = {"dark", "epic", "calm", "mysterious", "hopeful", "intense", "melancholic"}
    out = []
    for item in chain:
        if not isinstance(item, dict):
            continue
        v = {
            "hook": str(item.get("hook", item.get("idea", "..."))),
            "meaning": str(item.get("meaning", "")),
            "example": str(item.get("example", "")),
            "takeaway": str(item.get("takeaway", "")),
            "visual": str(item.get("visual", item.get("visual_prompt", "abstract"))),
            "mood": str(item.get("mood", "calm")).lower().strip(),
        }
        if v["mood"] not in moods:
            v["mood"] = "calm"
        out.append(v)
    return out or [{"hook": "...", "meaning": "", "example": "", "takeaway": "", "visual": "abstract", "mood": "calm"}]


# ═══════════════════════════════════════════════════════
#  FREE BOOKS
# ═══════════════════════════════════════════════════════

BOOKS = {
    "📜 Art of War — Sun Tzu": "https://www.gutenberg.org/cache/epub/132/pg132.txt",
    "🏛️ Meditations — Marcus Aurelius": "https://www.gutenberg.org/cache/epub/2680/pg2680.txt",
    "🧠 Beyond Good & Evil — Nietzsche": "https://www.gutenberg.org/cache/epub/4363/pg4363.txt",
    "👑 The Prince — Machiavelli": "https://www.gutenberg.org/cache/epub/1232/pg1232.txt",
    "📖 Frankenstein — Shelley": "https://www.gutenberg.org/cache/epub/84/pg84.txt",
    "🕳️ The Republic — Plato": "https://www.gutenberg.org/cache/epub/1497/pg1497.txt",
}


def download_book(url):
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        text = r.text
        for m in ["*** START OF THE PROJECT", "*** START OF THIS", "***START OF"]:
            idx = text.find(m)
            if idx != -1:
                nl = text.find('\n', idx)
                if nl != -1:
                    text = text[nl + 1:]
                break
        for m in ["*** END OF THE PROJECT", "*** END OF THIS", "***END OF",
                  "End of the Project Gutenberg", "End of Project Gutenberg"]:
            idx = text.find(m)
            if idx != -1:
                text = text[:idx]
                break
        text = text.strip()
        return text if len(text) > 100 else ""
    except Exception as e:
        st.error(f"❌ Download failed: {e}")
        return ""


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

def main():
    # ── INIT ──
    defaults = {
        "lang": "EN",
        "chains": {},
        "current_chapter": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── HEADER ──
    st.markdown(
        "<h1 style='text-align:center;color:#e94560;font-size:2.3em;"
        "margin:8px 0 0;'>🧠 DeepScroll</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align:center;color:#444;font-size:0.85em;"
        f"margin:4px 0 12px;'>{t('sub')}</p>",
        unsafe_allow_html=True,
    )

    # ── LANGUAGE ──
    lang_cols = st.columns(4)
    for i, (code, flag) in enumerate([("EN", "🇬🇧"), ("DE", "🇩🇪"), ("UA", "🇺🇦"), ("FR", "🇫🇷")]):
        with lang_cols[i]:
            label = f"✓ {flag}" if code == st.session_state["lang"] else flag
            if st.button(label, key=f"lang_{code}", use_container_width=True):
                if code != st.session_state["lang"]:
                    st.session_state["lang"] = code
                    st.session_state["chains"] = {}
                    st.rerun()

    st.markdown("---")

    # ── SOURCE ──
    tab1, tab2 = st.tabs([t("upload"), t("classics")])
    book_ready = False

    with tab1:
        uploaded = st.file_uploader("Upload", type=["pdf"], label_visibility="collapsed")
        if uploaded:
            file_id = f"{uploaded.name}_{uploaded.size}"
            if st.session_state.get("file_id") != file_id:
                st.session_state["pdf_bytes"] = uploaded.read()
                st.session_state["file_id"] = file_id
                for k in ["chapters", "chains", "current_chapter", "raw_text"]:
                    st.session_state.pop(k, None)
                st.session_state["chains"] = {}
                st.session_state["current_chapter"] = 0
            book_ready = True

    with tab2:
        sel = st.selectbox("Pick", list(BOOKS.keys()), label_visibility="collapsed")
        if st.button(t("load"), use_container_width=True):
            with st.spinner(t("reading")):
                txt = download_book(BOOKS[sel])
                if txt:
                    st.session_state["raw_text"] = txt
                    for k in ["chapters", "chains", "current_chapter", "pdf_bytes", "file_id"]:
                        st.session_state.pop(k, None)
                    st.session_state["chains"] = {}
                    st.session_state["current_chapter"] = 0
                    st.rerun()
        if "raw_text" in st.session_state:
            book_ready = True

    # ── PROCESS ──
    if book_ready and "chapters" not in st.session_state:
        with st.spinner(t("reading")):
            if "pdf_bytes" in st.session_state:
                raw = extract_pdf(st.session_state["pdf_bytes"])
            elif "raw_text" in st.session_state:
                raw = st.session_state["raw_text"]
            else:
                raw = ""
            if raw and len(raw) > 50:
                st.session_state["chapters"] = split_chapters(raw)
                st.session_state["current_chapter"] = 0
                st.session_state["chains"] = {}
                st.rerun()
            else:
                st.error("❌ Could not extract text. Try a different PDF.")
                return

    # ── LANDING ──
    if "chapters" not in st.session_state:
        st.markdown(f"""
            <div class="land">
                <p style="font-size:3.5em;">📖</p>
                <h2>{t('land_t')}</h2>
                <p>{t('land_s')}</p>
            </div>
        """, unsafe_allow_html=True)
        return

    # ── DISPLAY ──
    chapters = st.session_state["chapters"]
    total = len(chapters)
    cur = st.session_state["current_chapter"]
    if cur >= total:
        cur = total - 1
        st.session_state["current_chapter"] = cur

    # Navigation
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if cur > 0 and st.button("⬅️", key="prev", use_container_width=True):
            st.session_state["current_chapter"] = cur - 1
            st.rerun()
    with c2:
        st.markdown(
            f"<p style='text-align:center;color:#555;margin-top:8px;'>"
            f"{cur + 1} / {total}</p>",
            unsafe_allow_html=True,
        )
    with c3:
        if cur < total - 1 and st.button("➡️", key="nxt", use_container_width=True):
            st.session_state["current_chapter"] = cur + 1
            st.rerun()

    # Generate chain
    chains = st.session_state["chains"]
    if cur not in chains:
        with st.spinner(t("building")):
            ch_text = chapters[cur]
            title = make_title(ch_text)
            chain = make_chain(ch_text)
            chains[cur] = {"title": title, "chain": chain}
            st.session_state["chains"] = chains

    data = chains[cur]

    # Title
    st.markdown(f'<div class="ch-t">{data["title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ch-s">{cur + 1} / {total}</div>', unsafe_allow_html=True)

    # ── MUSIC ──
    if data["chain"]:
        mood = data["chain"][0].get("mood", "calm")
        tracks = MUSIC.get(mood, MUSIC["calm"])
        tracks_json = json.dumps(tracks)

        with st.expander(f"🎵 {t('music')} — {mood.upper()}", expanded=False):
            components.html(f"""
                <div style="
                    font-family: 'Segoe UI', sans-serif;
                    background: #111;
                    border-radius: 12px;
                    padding: 15px;
                    color: #ccc;
                ">
                    <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
                        <button id="toggleBtn" onclick="toggleMusic()" style="
                            background: #e94560;
                            border: none;
                            color: white;
                            width: 40px;
                            height: 40px;
                            border-radius: 50%;
                            font-size: 18px;
                            cursor: pointer;
                        ">▶</button>
                        <button onclick="nextTrack()" style="
                            background: #222;
                            border: 1px solid #333;
                            color: #ccc;
                            padding: 8px 16px;
                            border-radius: 20px;
                            cursor: pointer;
                            font-size: 14px;
                        ">⏭ Next</button>
                        <div style="flex:1; display:flex; align-items:center; gap:8px;">
                            <span style="font-size:12px;">🔈</span>
                            <input type="range" id="volSlider" min="0" max="100" value="25"
                                style="flex:1; accent-color:#e94560; height:4px;"
                                oninput="setVolume(this.value)">
                            <span style="font-size:12px;">🔊</span>
                        </div>
                    </div>
                    <div id="trackInfo" style="font-size:11px; color:#555; text-align:center;">
                        Track 1 / {len(tracks)}
                    </div>
                </div>
                <script>
                    var tracks = {tracks_json};
                    var currentTrack = 0;
                    var targetVolume = 0.25;
                    var isPlaying = false;
                    var audio = new Audio(tracks[0]);
                    audio.volume = 0;
                    audio.addEventListener('ended', function() {{
                        nextTrack();
                    }});
                    function fadeIn() {{
                        var vol = 0;
                        var fadeInterval = setInterval(function() {{
                            vol += 0.005;
                            if (vol >= targetVolume) {{
                                vol = targetVolume;
                                clearInterval(fadeInterval);
                            }}
                            audio.volume = vol;
                        }}, 100);
                    }}
                    function toggleMusic() {{
                        var btn = document.getElementById('toggleBtn');
                        if (isPlaying) {{
                            audio.pause();
                            btn.innerHTML = '▶';
                            isPlaying = false;
                        }} else {{
                            audio.play();
                            fadeIn();
                            btn.innerHTML = '⏸';
                            isPlaying = true;
                        }}
                    }}
                    function nextTrack() {{
                        currentTrack = (currentTrack + 1) % tracks.length;
                        var wasPlaying = isPlaying;
                        audio.src = tracks[currentTrack];
                        document.getElementById('trackInfo').innerHTML =
                            'Track ' + (currentTrack + 1) + ' / ' + tracks.length;
                        if (wasPlaying) {{
                            audio.volume = 0;
                            audio.play();
                            fadeIn();
                        }}
                    }}
                    function setVolume(val) {{
                        targetVolume = val / 100;
                        if (isPlaying) {{
                            audio.volume = targetVolume;
                        }}
                    }}
                    setTimeout(function() {{
                        audio.play().then(function() {{
                            isPlaying = true;
                            document.getElementById('toggleBtn').innerHTML = '⏸';
                            fadeIn();
                        }}).catch(function() {{}});
                    }}, 2000);
                </script>
            """, height=100)

    # ── CARDS ──
    chain = data["chain"]
    for i, node in enumerate(chain):
        hook = node["hook"]
        meaning = node.get("meaning", "")
        example = node.get("example", "")
        takeaway = node.get("takeaway", "")
        visual = node["visual"]
        mood = node["mood"]
        img = get_image_url(visual, idx=cur * 100 + i)

        tap_text = t("tap")

        # Hero card with hook
        st.markdown(f"""
            <div class="hero">
                <img class="hero-bg" src="{img}" loading="lazy"
                     onerror="this.src='https://picsum.photos/seed/fb{cur}{i}/800/600'">
                <div class="hero-grad"></div>
                <div class="hero-body">
                    <div class="hero-txt">{hook}</div>
                    <div class="hero-foot">
                        <span class="mood-tag">{mood}</span>
                        <span>{i + 1}/{len(chain)}</span>
                        <span class="tap-label">{tap_text} ▾</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Expandable explanation
        has_content = meaning or example or takeaway
        if has_content:
            is_open = st.session_state.get(f"card_{cur}_{i}", False)

            if st.button(
                "▾" if not is_open else "▴",
                key=f"tap_{cur}_{i}",
                use_container_width=True,
            ):
                st.session_state[f"card_{cur}_{i}"] = not is_open
                st.rerun()

            if is_open:
                explain_html = '<div class="explain-card">'
                if meaning:
                    explain_html += f'''
                        <div class="explain-section">
                            <div class="explain-label">📖 {t("what_means")}</div>
                            <div class="explain-text">{meaning}</div>
                        </div>'''
                if example:
                    explain_html += f'''
                        <div class="explain-section">
                            <div class="explain-label">💡 {t("example_label")}</div>
                            <div class="explain-text">{example}</div>
                        </div>'''
                if takeaway:
                    explain_html += f'''
                        <div class="explain-section">
                            <div class="explain-label">🔑 {t("takeaway_label")}</div>
                            <div class="explain-text">{takeaway}</div>
                        </div>'''
                explain_html += '</div>'
                st.markdown(explain_html, unsafe_allow_html=True)

        # Connector
        if i < len(chain) - 1:
            st.markdown('<div class="conn">⟱</div>', unsafe_allow_html=True)

    # ── END ──
    st.markdown("---")
    if cur < total - 1:
        if st.button(t("next_ch"), use_container_width=True, type="primary", key="next_ch"):
            st.session_state["current_chapter"] = cur + 1
            st.rerun()
    else:
        st.markdown(f"""
            <div style="text-align:center;padding:30px;">
                <h2 style="color:#e94560;">{t('done')}</h2>
                <p style="color:#555;">{t('done_sub')}</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button(t("reset"), use_container_width=True, key="reset_btn"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


if __name__ == "__main__":
    main()
