import streamlit as st
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
        "reading": "📚 Reading the book...",
        "building": "🧠 Building idea chain...",
        "next_ch": "Next Chapter →",
        "done": "🎉 Done!",
        "done_sub": "Drop another book.",
        "reset": "🔄 New Book",
        "land_t": "Drop a book. Start scrolling.",
        "land_s": "Any PDF becomes a visual journey.",
        "music": "🎵 Music",
        "ai": "Write each idea in MAX 12 words in English. Short like a billboard.",
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
        "ai": "Write each idea in MAX 12 words in German. Short like a billboard.",
    },
    "UA": {
        "sub": "Скроль мудрість. Без шуму.",
        "upload": "📁 PDF",
        "classics": "📚 Класика",
        "load": "📖 Читати",
        "reading": "📚 Читаю книгу...",
        "building": "🧠 Будую ланцюг ідей...",
        "next_ch": "Далі →",
        "done": "🎉 Готово!",
        "done_sub": "Кинь нову книгу.",
        "reset": "🔄 Нова книга",
        "land_t": "Кинь книгу. Скроль.",
        "land_s": "Будь-який PDF стане подорожжю.",
        "music": "🎵 Музика",
        "ai": "Write each idea in MAX 12 words in Ukrainian. Short like a billboard.",
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
        "ai": "Write each idea in MAX 12 words in French. Short like a billboard.",
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
#  STYLES (no JS, only CSS)
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
        margin-bottom: 10px;
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
    }
    .mood-tag {
        background: rgba(233,69,96,0.25);
        color: #e94560;
        padding: 2px 10px;
        border-radius: 20px;
        font-weight: 600;
    }
    @keyframes pop {
        from { opacity: 0; transform: translateY(25px) scale(0.97); }
        to   { opacity: 1; transform: translateY(0) scale(1); }
    }

    .conn { text-align: center; color: #e94560; font-size: 22px; margin: 3px 0; opacity: 0.4; }
    .ch-t { color: #e94560; font-size: 1.6em; font-weight: 700; text-align: center; margin: 12px 0 3px; }
    .ch-s { color: #444; text-align: center; font-size: 0.8em; margin-bottom: 18px; }
    .land { text-align: center; padding: 70px 20px; }
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
#  MUSIC — Download and serve via Streamlit natively
# ═══════════════════════════════════════════════════════

# These are direct .mp3 URLs that allow hotlinking
MUSIC_URLS = {
    "dark": "https://upload.wikimedia.org/wikipedia/commons/4/47/Pista_de_audio.ogg",
    "epic": "https://upload.wikimedia.org/wikipedia/commons/6/6e/Microtonal_music.ogg",
    "calm": "https://upload.wikimedia.org/wikipedia/commons/e/ea/Threnody_for_the_Victims_of_Hiroshima_%28excerpt%29.ogg",
    "mysterious": "https://upload.wikimedia.org/wikipedia/commons/4/47/Pista_de_audio.ogg",
    "hopeful": "https://upload.wikimedia.org/wikipedia/commons/6/6e/Microtonal_music.ogg",
    "intense": "https://upload.wikimedia.org/wikipedia/commons/6/6e/Microtonal_music.ogg",
    "melancholic": "https://upload.wikimedia.org/wikipedia/commons/e/ea/Threnody_for_the_Victims_of_Hiroshima_%28excerpt%29.ogg",
}


@st.cache_data(ttl=3600)
def download_music(url):
    """Download music file and return bytes for st.audio()."""
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return r.content
    except Exception:
        return None


# ═══════════════════════════════════════════════════════
#  IMAGES — picsum.photos (instant)
# ═══════════════════════════════════════════════════════

def get_image_url(prompt, idx=0):
    seed = abs(hash(prompt + str(idx))) % 100000
    return f"https://picsum.photos/seed/{seed}/800/600"


# ═══════════════════════════════════════════════════════
#  PDF EXTRACTION (robust)
# ═══════════════════════════════════════════════════════

def extract_pdf(pdf_bytes):
    """Extract text from PDF with multiple fallback methods."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Method 1: Standard text extraction
            page_text = page.get_text("text")

            # Method 2: If empty, try different extraction
            if not page_text or len(page_text.strip()) < 10:
                page_text = page.get_text("blocks")
                if isinstance(page_text, list):
                    page_text = "\n".join(
                        block[4] for block in page_text
                        if isinstance(block, tuple) and len(block) > 4 and isinstance(block[4], str)
                    )

            if isinstance(page_text, str) and page_text.strip():
                text += page_text + "\n\n"

        doc.close()

        # Clean up
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()

        if len(text) < 50:
            return ""

        return text

    except Exception as e:
        st.error(f"❌ Could not read this PDF: {e}")
        return ""


def split_chapters(text):
    """Split text into chapters with smart detection."""
    if not text or len(text) < 100:
        return ["Text too short to process."]

    # Strategy 1: Chapter markers
    for pattern in [
        r'(?=\n\s*(?:CHAPTER|Chapter)\s+[\dIVXLCDM]+)',
        r'(?=\n\s*(?:PART|Part)\s+[\dIVXLCDM]+)',
        r'(?=\n\s*\d+\.\s+[A-Z])',
    ]:
        parts = re.split(pattern, text)
        parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 200]
        if len(parts) >= 2:
            return parts[:50]  # Max 50 chapters

    # Strategy 2: Natural paragraph breaks
    paras = re.split(r'\n\s*\n', text)
    if len(paras) >= 4:
        chunks = []
        current = ""
        for p in paras:
            p = p.strip()
            if not p:
                continue
            if len(current) + len(p) > 2500 and len(current) > 500:
                chunks.append(current.strip())
                current = p
            else:
                current += "\n\n" + p
        if current.strip() and len(current.strip()) > 100:
            chunks.append(current.strip())
        if len(chunks) >= 2:
            return chunks[:50]

    # Strategy 3: Sentence-aware fixed chunks
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""
    for s in sentences:
        if len(current) + len(s) > 2500 and len(current) > 500:
            chunks.append(current.strip())
            current = s
        else:
            current += " " + s
    if current.strip() and len(current.strip()) > 100:
        chunks.append(current.strip())

    return chunks[:50] if chunks else [text[:3000]]


# ═══════════════════════════════════════════════════════
#  AI FUNCTIONS
# ═══════════════════════════════════════════════════════

def make_chain(chapter_text):
    if not client:
        return [{"idea": "No AI connected.", "visual": "abstract", "mood": "calm"}]

    ai_lang = t("ai")

    try:
        r = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"""You create IDEA CHAINS for people with ADHD.

CRITICAL RULES:
- Each idea: MAX 10-15 WORDS total. Like a billboard.
- NO long sentences. NO filler words. NO "the author says" or "this chapter discusses"
- Just raw insight. Punchy. Bold.
- Ideas connect: cause→effect or question→answer
- Generate exactly 5 ideas
- visual: 2-3 English words for a photo (landscape, nature, abstract — NO text, NO people faces)
- mood: one of: dark, epic, calm, mysterious, hopeful, intense, melancholic
- {ai_lang}

Return ONLY a JSON array. No markdown. No explanation.
[{{"idea":"short text","visual":"photo keywords","mood":"calm"}}]

GOOD examples:
- "Fear keeps us in cages we built ourselves."
- "Power doesn't corrupt. It reveals."
- "The cave was comfortable. Truth wasn't."
- "Every empire falls. The pattern never breaks."
BAD examples (too long):
- "The author discusses how fear is a mechanism that keeps people trapped" ← NO
- "In this chapter we learn about the nature of power" ← NO"""
                },
                {"role": "user", "content": f"Create an idea chain from this text:\n\n{chapter_text[:3000]}"}
            ],
            model=AI_MODEL,
            temperature=0.7,
            max_tokens=1200,
        )
        return parse_json(r.choices[0].message.content.strip())
    except Exception as e:
        st.warning(f"⚠️ AI error: {e}")
        return [{"idea": "Could not generate. Refresh the page.", "visual": "abstract", "mood": "calm"}]


def make_title(chapter_text):
    if not client:
        return "..."
    ai_lang = t("ai")
    try:
        r = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": (
                    f"Create a poetic title (2-4 words) for this text. "
                    f"{ai_lang} Return ONLY the title, nothing else:\n\n"
                    f"{chapter_text[:1500]}"
                )
            }],
            model=AI_MODEL,
            temperature=0.9,
            max_tokens=20,
        )
        return r.choices[0].message.content.strip().strip('"\'').strip()[:50]
    except Exception:
        return "..."


def parse_json(raw):
    # Clean markdown
    cleaned = re.sub(r'```json\s*', '', raw)
    cleaned = re.sub(r'```\s*', '', cleaned).strip()

    # Try 1: Direct
    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return validate(result)
    except json.JSONDecodeError:
        pass

    # Try 2: Find array
    match = re.search(r'\[.*\]', cleaned, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return validate(result)
        except json.JSONDecodeError:
            pass

    # Try 3: Individual objects
    objs = []
    for o in re.findall(r'\{[^{}]+\}', cleaned):
        try:
            objs.append(json.loads(o))
        except json.JSONDecodeError:
            pass
    if objs:
        return validate(objs)

    return [{"idea": raw[:200], "visual": "abstract", "mood": "calm"}]


def validate(chain):
    moods = {"dark", "epic", "calm", "mysterious", "hopeful", "intense", "melancholic"}
    out = []
    for item in chain:
        if not isinstance(item, dict):
            continue
        v = {
            "idea": str(item.get("idea", "...")),
            "visual": str(item.get("visual", item.get("visual_prompt", "abstract"))),
            "mood": str(item.get("mood", "calm")).lower().strip(),
        }
        if v["mood"] not in moods:
            v["mood"] = "calm"
        out.append(v)
    return out or [{"idea": "...", "visual": "abstract", "mood": "calm"}]


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

        # Remove Gutenberg header
        for marker in ["*** START OF THE PROJECT", "*** START OF THIS", "***START OF"]:
            idx = text.find(marker)
            if idx != -1:
                nl = text.find('\n', idx)
                if nl != -1:
                    text = text[nl + 1:]
                break

        # Remove Gutenberg footer
        for marker in ["*** END OF THE PROJECT", "*** END OF THIS", "***END OF", "End of the Project Gutenberg", "End of Project Gutenberg"]:
            idx = text.find(marker)
            if idx != -1:
                text = text[:idx]
                break

        text = text.strip()
        if len(text) < 100:
            st.error("Downloaded text is too short.")
            return ""
        return text

    except Exception as e:
        st.error(f"❌ Download failed: {e}")
        return ""


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

def main():
    # ── SAFE INIT ──
    defaults = {
        "lang": "EN",
        "chains": {},
        "current_chapter": 0,
        "music_on": False,
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
    lang_options = [("EN", "🇬🇧"), ("DE", "🇩🇪"), ("UA", "🇺🇦"), ("FR", "🇫🇷")]
    for i, (code, flag) in enumerate(lang_options):
        with lang_cols[i]:
            current_lang = st.session_state["lang"]
            label = f"✓ {flag}" if code == current_lang else flag
            if st.button(label, key=f"lang_{code}", use_container_width=True):
                if code != current_lang:
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
            # Only read once
            file_id = f"{uploaded.name}_{uploaded.size}"
            if st.session_state.get("file_id") != file_id:
                st.session_state["pdf_bytes"] = uploaded.read()
                st.session_state["file_id"] = file_id
                # Clear old data
                for k in ["chapters", "chains", "current_chapter", "raw_text"]:
                    if k in st.session_state:
                        del st.session_state[k]
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
                        if k in st.session_state:
                            del st.session_state[k]
                    st.session_state["chains"] = {}
                    st.session_state["current_chapter"] = 0
                    st.rerun()

        if "raw_text" in st.session_state:
            book_ready = True

    # ── PROCESS BOOK ──
    if book_ready and "chapters" not in st.session_state:
        with st.spinner(t("reading")):
            if "pdf_bytes" in st.session_state:
                raw = extract_pdf(st.session_state["pdf_bytes"])
            elif "raw_text" in st.session_state:
                raw = st.session_state["raw_text"]
            else:
                raw = ""

            if raw and len(raw) > 50:
                chapters = split_chapters(raw)
                st.session_state["chapters"] = chapters
                st.session_state["current_chapter"] = 0
                st.session_state["chains"] = {}
                st.rerun()
            else:
                st.error("❌ Could not extract text from this file. Try a different PDF.")
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

    # ══════════════════════════════════════
    #  DISPLAY CHAPTER
    # ══════════════════════════════════════

    chapters = st.session_state["chapters"]
    total = len(chapters)
    cur = st.session_state["current_chapter"]

    # Clamp
    if cur >= total:
        cur = total - 1
        st.session_state["current_chapter"] = cur

    # ── NAVIGATION ──
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if cur > 0:
            if st.button("⬅️", key="btn_prev", use_container_width=True):
                st.session_state["current_chapter"] = cur - 1
                st.rerun()
    with c2:
        st.markdown(
            f"<p style='text-align:center;color:#555;margin-top:8px;'>"
            f"{cur + 1} / {total}</p>",
            unsafe_allow_html=True,
        )
    with c3:
        if cur < total - 1:
            if st.button("➡️", key="btn_next", use_container_width=True):
                st.session_state["current_chapter"] = cur + 1
                st.rerun()

    # ── GENERATE CHAIN ──
    chains = st.session_state["chains"]
    if cur not in chains:
        with st.spinner(t("building")):
            ch_text = chapters[cur]
            title = make_title(ch_text)
            chain = make_chain(ch_text)
            chains[cur] = {"title": title, "chain": chain}
            st.session_state["chains"] = chains

    data = chains[cur]

    # Chapter title
    st.markdown(f'<div class="ch-t">{data["title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ch-s">{cur + 1} / {total}</div>', unsafe_allow_html=True)

    # ── MUSIC (native Streamlit — no JS!) ──
    if data["chain"]:
        mood = data["chain"][0].get("mood", "calm")
        music_url = MUSIC_URLS.get(mood, MUSIC_URLS["calm"])

        with st.expander(f"🎵 {t('music')} — {mood.upper()}", expanded=False):
            music_data = download_music(music_url)
            if music_data:
                st.audio(music_data, format="audio/ogg", loop=True)
            else:
                st.caption("Music unavailable. Try refreshing.")

    # ── IDEA CARDS ──
    chain = data["chain"]
    for i, node in enumerate(chain):
        idea = node["idea"]
        visual = node["visual"]
        mood = node["mood"]
        img = get_image_url(visual, idx=cur * 100 + i)

        st.markdown(f"""
            <div class="hero">
                <img class="hero-bg" src="{img}" loading="lazy"
                     onerror="this.src='https://picsum.photos/seed/fb{cur}{i}/800/600'">
                <div class="hero-grad"></div>
                <div class="hero-body">
                    <div class="hero-txt">{idea}</div>
                    <div class="hero-foot">
                        <span class="mood-tag">{mood}</span>
                        <span>{i + 1}/{len(chain)}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if i < len(chain) - 1:
            st.markdown('<div class="conn">⟱</div>', unsafe_allow_html=True)

    # ── END OF CHAPTER ──
    st.markdown("---")

    if cur < total - 1:
        if st.button(t("next_ch"), use_container_width=True, type="primary", key="btn_next_ch"):
            st.session_state["current_chapter"] = cur + 1
            st.rerun()
    else:
        st.markdown(f"""
            <div style="text-align:center;padding:30px;">
                <h2 style="color:#e94560;">{t('done')}</h2>
                <p style="color:#555;">{t('done_sub')}</p>
            </div>
        """, unsafe_allow_html=True)

        if st.button(t("reset"), use_container_width=True, key="btn_reset"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ═══════════════════════════════════════════════════════
#  RUN
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    main()
