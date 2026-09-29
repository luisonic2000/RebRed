"""RebRed.

Local, offline-first planner for preparing Reddit commission posts. It never
logs in to Reddit, publishes content, duplicates images, or modifies artwork.
"""

from __future__ import annotations

import json
import os
import random
import re
import struct
import sys
import ctypes
import webbrowser
import subprocess
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageOps, ImageTk


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
SEPARATOR = "\n---\n"
APP_NAME = "RebRed"
APP_VERSION = "1.1-beta"
CREDITS_URL = "https://www.instagram.com/reborn_neo_art/"
TITLE_CHARACTER_LIMIT = 300


def _search_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def filter_profile_indices(profiles: list[dict[str, Any]], query: str) -> list[int]:
    """Return profile indexes matching a case- and accent-insensitive query."""
    search = _search_key(query.strip())
    return [
        index for index, profile in enumerate(profiles)
        if search in _search_key(str(profile.get("name", "")))
    ]


def title_character_count(title: str) -> tuple[int, int]:
    """Return title length and remaining characters under Reddit's title limit."""
    length = len(title)
    return length, TITLE_CHARACTER_LIMIT - length

SOCIAL_FIELDS = [
    ("vgen", "VGen"), ("artstation", "ArtStation"), ("behance", "Behance"),
    ("cara", "Cara"), ("website", "Website"), ("instagram", "Instagram"),
    ("bluesky", "Bluesky"), ("x", "X"), ("linkedin", "LinkedIn"), ("twitch", "Twitch"),
    ("youtube", "YouTube"), ("discord", "Discord"), ("kofi", "Ko-fi"),
]
SOCIAL_LABELS = dict(SOCIAL_FIELDS)
CATEGORY_LABELS = ["Anime", "Comic", "Cartoon", "Realistic", "Splash art", "Animation"]
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# These are suggested posting windows in Brasília time, not subreddit rules.
# They deliberately vary by day so that the planner does not present one
# artificial "best time" for an entire week. Every value can be edited in the
# Community settings dialog.
SUGGESTED_WEEKDAY_TIMES = {
    "Mon": "09:30, 13:00, 19:00",
    "Tue": "10:00, 13:30, 19:30",
    "Wed": "09:30, 14:00, 19:00",
    "Thu": "10:00, 13:00, 19:30",
    "Fri": "09:30, 13:30, 18:30",
    "Sat": "10:30, 14:00, 18:30",
    "Sun": "10:00, 13:30, 18:00",
}

ART_SHOWCASE_TITLES = [
    "A recent {{category}} character illustration",
    "{{category}} character piece",
    "{{category}} character study",
]
ART_SHOWCASE_BODIES = [
    "Sharing a recent {{category}} piece. I focused on the character's pose, color, and visual storytelling.",
    "A {{category}} illustration I recently finished. I would love to hear what detail stands out to you.",
    "My latest {{category}} character artwork. Thanks for taking a look!",
]


def suggested_schedule(days: str) -> dict[str, str]:
    """Return three editable local posting windows for each allowed weekday."""
    allowed = {item.strip().title()[:3] for item in days.split(",") if item.strip()}
    return {day: SUGGESTED_WEEKDAY_TIMES[day] for day in DAYS if day in allowed}

# Fifteen concise starting directions per category. They are editable in the app
# and are used only to prepare a manual draft, never to post automatically.
CATEGORY_DIRECTIONS = {
    "Anime": ["character commissions", "OC illustrations", "fanart", "character sheets", "portraits", "couple art", "party illustrations", "icons", "emotes", "key visual art", "game characters", "fantasy characters", "VTuber art", "cover art", "illustrations"],
    "Comic": ["comic pages", "sequential art", "comic covers", "character designs", "pencils and inks", "colored pages", "graphic novel art", "webcomic art", "manga pages", "lettering-ready pages", "storyboards", "splash pages", "comic pinups", "concept pages", "cover illustrations"],
    "Cartoon": ["cartoon characters", "stylized portraits", "mascot art", "children's illustrations", "cute character art", "cartoon icons", "editorial cartoons", "family portraits", "stream overlays", "emotes", "sticker art", "cartoon covers", "brand characters", "pet portraits", "playful illustrations"],
    "Realistic": ["realistic portraits", "semi-realistic characters", "book covers", "concept art", "cinematic portraits", "fantasy illustrations", "character studies", "environment art", "realistic fanart", "editorial illustrations", "digital paintings", "cover illustrations", "key art", "detailed portraits", "portrait commissions"],
    "Splash art": ["splash art", "game key art", "hero illustrations", "character key visuals", "promotional art", "fantasy splash pieces", "MOBA-style characters", "card game illustrations", "dynamic battle scenes", "launcher art", "event artwork", "game covers", "cinematic key art", "character posters", "premium illustrations"],
    "Animation": ["animated loops", "animated emotes", "GIF commissions", "short character animations", "stream alerts", "animated icons", "motion illustrations", "animated portraits", "VTuber assets", "idle animations", "animated stickers", "social loops", "logo animations", "character turnarounds", "short-form animation"],
}


def human_title_options(prefix: str = "") -> list[str]:
    """Readable, rule-neutral starting titles. Community prefixes stay intact."""
    starts = [
        "{{category}} character commissions open | {{handle}}",
        "Available for {{category}} character and illustration work | {{handle}}",
        "{{category}} art for OCs, fanart and original ideas | {{handle}}",
        "Expressive {{category}} character art and commissions | {{handle}}",
        "{{category}} commissions for characters, parties and stories | {{handle}}",
        "Open for {{category}} illustrations and custom character art | {{handle}}",
        "{{category}} art with clean linework and strong color | {{handle}}",
        "Custom {{category}} characters, fanart and illustration work | {{handle}}",
    ]
    return [prefix + title for title in starts]


HUMAN_BODY_OPTIONS = [
    "Hi! I’m {{artist_name}}, a 2D illustrator available for {{category}} commissions.\n\n"
    "I create original characters, fanart, game and comic characters, posters, cover art, full party illustrations, character sheets, icons, and emotes.\n\n"
    "{{price_block}}\n\n{{links}}\n\n{{payment_note}}\n\n{{contact_note}}\n\n{{reviews_note}}",
    "Hi! I’m {{artist_name}} and I’m open for character commissions.\n\n"
    "I draw original characters, fanart, couples, game characters, comic characters, and full party illustrations. I enjoy giving each piece expressive poses, clean linework, strong colors, and personality.\n\n"
    "{{price_block}}\n\n{{links}}\n\n{{payment_note}}\n\n{{contact_note}}",
    "I’m {{artist_name}}, a 2D illustrator open for {{category}} work.\n\n"
    "I can create character art, fanart, character sheets, icons, emotes, tabletop party art, posters, and custom illustrations for games or comics.\n\n"
    "{{price_block}} Final cost can vary with complexity, character count, and background.\n\n{{links}}\n\n{{payment_note}}\n\n{{contact_note}}",
    "Have a character, scene, band, party, or story idea you want to see illustrated? I’m {{artist_name}}, and I’m available for {{category}} commissions.\n\n"
    "I work on portraits, character-focused pieces, fanart, covers, posters, and custom illustration projects.\n\n"
    "{{price_block}}\n\n{{links}}\n\n{{contact_note}}",
    "Commission slots are open. I’m {{artist_name}}, a 2D illustrator who loves turning character ideas into polished {{category}} art.\n\n"
    "I am happy to discuss single characters, couples, groups, expressive icons, detailed scenes, and long-term creative projects.\n\n"
    "{{price_block}}\n\n{{links}}\n\n{{payment_note}}\n\n{{contact_note}}",
    "Hi! I’m {{artist_name}}. I’m currently available for {{category}} illustrations, with a focus on memorable characters and clear visual storytelling.\n\n"
    "Send your idea, visual references, and deadline through Reddit or the portfolio platform that works best for you.\n\n"
    "{{price_block}}\n\n{{links}}\n\n{{reviews_note}}",
]

# Conservative, community-specific public-contact policies. A platform absent
# from a policy never appears in the generated draft, whether the artist chose
# to store a link or an @handle for it. They remain editable in the community
# settings because moderators can change rules without notice.
COMMUNITY_LINK_POLICIES: dict[str, list[str]] = {
    "animecommission": ["vgen", "artstation", "behance", "instagram", "bluesky", "x", "discord"],
    "artcommission": ["vgen", "artstation", "behance", "cara", "website"],
    "artcommissions": ["artstation", "behance"],
    "artistsforhire": ["vgen", "artstation", "behance", "cara", "website", "instagram", "bluesky", "x", "discord"],
    "artsale": ["vgen", "artstation", "behance", "website"],
    "artstore": ["vgen", "artstation", "behance", "cara", "website", "instagram", "discord"],
    "comicbookcollabs": ["artstation", "behance", "website"],
    "comissions": ["vgen", "artstation", "behance", "discord"],
    "commissionart": ["vgen", "artstation", "behance", "cara", "website"],
    "commissions": ["vgen", "artstation", "behance", "cara", "discord"],
    "commissions_rh": ["vgen", "artstation", "behance", "instagram", "discord"],
    "dndart": ["vgen", "artstation", "behance", "website"],
    "dndcommissions": ["vgen", "artstation", "behance", "discord"],
    "gamedevclassifieds": ["artstation", "behance", "website", "linkedin"],
    "gamedevjobs": ["artstation", "behance", "website", "linkedin"],
    "hungryartists": ["vgen", "artstation", "behance", "cara", "website", "instagram", "bluesky", "x", "discord"],
    "drawforme": ["vgen", "artstation", "behance", "website", "discord"],
    "artistforhire": ["vgen", "artstation", "behance", "website", "instagram", "bluesky", "x", "discord"],
    "hireanartist": ["vgen", "artstation", "behance", "website", "instagram", "bluesky", "x", "discord"],
    "vgen": ["vgen", "artstation", "behance", "instagram", "bluesky", "x", "discord"],
    # Kept deliberately without Instagram, X or Twitter at the user's
    # requested conservative setting for this community.
    "starvingartists": ["vgen", "artstation", "behance", "cara", "website", "discord"],
    "thirstyartists": ["vgen", "artstation", "behance", "website", "bluesky", "x", "discord"],
    "tabletopartists": ["vgen", "artstation", "behance", "website", "discord"],
    "loatdearte": ["vgen", "artstation", "behance", "instagram", "discord"],
    "lojadearte": ["vgen", "artstation", "behance", "instagram", "discord"],
}

COMMUNITY_BODY_TEMPLATES: dict[str, list[str]] = {
    "animecommission": [
        "Hi! I’m {{artist_name}}, a 2D illustrator available for {{category}} character commissions. I create OCs, fanart, character sheets, icons, emotes, and detailed scenes.\n\n{{price_block}}\n\n{{links}}\n\n{{contact_note}}",
        "I’m {{artist_name}} and I’m open for {{category}} commissions, from character portraits to full party illustrations. Please share your idea, references, and deadline when you get in touch.\n\n{{price_block}}\n\n{{links}}",
    ],
    "artcommissions": [
        "I’m {{artist_name}}, a 2D illustrator available for {{category}} character artwork. My portfolio is below and the attached images show recent examples of my work.\n\n{{price_block}}\n\n{{links}}",
        "Available for custom {{category}} illustrations, including original characters, fanart, and group pieces. I can discuss scope, references, and turnaround through Reddit.\n\n{{price_block}}\n\n{{links}}",
    ],
    "hungryartists": [
        "[For Hire] I’m {{artist_name}}, a 2D illustrator offering {{category}} character commissions. I take on original characters, fanart, group scenes, and illustration work.\n\n{{price_block}}\n\n{{links}}\n\n{{contact_note}}",
        "[For Hire] {{artist_name}} here. I’m available for {{category}} artwork and can quote larger scenes, multiple characters, or commercial use after reviewing the brief.\n\n{{price_block}}\n\n{{links}}",
    ],
    "starvingartists": [
        "[For Hire] Hi! I’m {{artist_name}}, available for {{category}} character commissions. I create OCs, fanart, couples, and party illustrations.\n\n{{price_block}}\n\n{{links}}\n\nPlease contact me through Reddit or the portfolio platform above.",
        "[For Hire] I’m {{artist_name}}, a 2D illustrator open for custom {{category}} artwork. Send your idea, visual references, and deadline through Reddit to discuss the commission.\n\n{{price_block}}\n\n{{links}}",
    ],
    "drawforme": [
        "[Paid Offer] I’m {{artist_name}}, available for paid {{category}} character commissions. I can work from written descriptions and visual references.\n\n{{price_block}}\n\n{{links}}",
    ],
    "hireanartist": [
        "[For Hire] I’m {{artist_name}}, a 2D {{category}} artist available for custom paid commissions. My starting price and portfolio are included below.\n\n{{price_block}}\n\n{{links}}\n\n{{contact_note}}",
    ],
    "artistforhire": [
        "[For Hire] I’m {{artist_name}}, available for {{category}} character art, fanart, and custom illustration projects.\n\n{{price_block}}\n\n{{links}}",
    ],
    "comicbookcollabs": [
        "I’m {{artist_name}}, a 2D artist available for comic-focused {{category}} work, including covers, character designs, sequential pages, and pinups.\n\n{{price_block}}\n\n{{links}}",
    ],
    "gamedevclassifieds": [
        "[For Hire] I’m {{artist_name}}, available for {{category}} game art. I can contribute character illustrations, key art, splash pieces, and promotional assets.\n\n{{price_block}}\n\n{{links}}",
    ],
    "gamedevjobs": [
        "[For Hire] I’m {{artist_name}}, a 2D {{category}} artist looking for paid game-art work. My portfolio shows character art and illustration samples relevant to game projects.\n\n{{price_block}}\n\n{{links}}",
    ],
}

LINK_POLICY_VERSION = 1
# Marking a post must always have a visible effect. Communities without a
# published interval therefore use a conservative local 24-hour lock.
DEFAULT_LOCAL_POST_LOCK_HOURS = 24

# Post drafts remain in English. This map changes only the local app interface.
UI_PT = {
    "Communities": "Comunidades", "Each community has its own folder, drafts and rule checks.": "Cada comunidade tem sua própria pasta, rascunhos e verificações de regras.",
    "Search communities": "Buscar comunidades", "Clear": "Limpar",
    "Ready": "Agora", "Soon": "Em breve", "Outside": "Fora da janela", "Locked": "Bloqueada",
    "Add": "Adicionar", "Edit": "Editar", "Remove": "Remover", "Export community template": "Exportar modelo da comunidade",
    "Import community template": "Importar modelo da comunidade", "Copy settings to…": "Copiar configurações para…",
    "Creator profile": "Perfil do artista", "Export": "Exportar", "Import creator template": "Importar modelo de perfil",
    "Remove profile": "Excluir perfil",
    "Open selected folder": "Abrir pasta selecionada", "Choose image folder…": "Escolher pasta de imagens…",
    "Copy selected images": "Copiar imagens selecionadas", "Images to select (1–9)": "Imagens a selecionar (1–9)",
    "Selected images": "Imagens selecionadas",
    "Draft options": "Opções do rascunho", "Draft": "Rascunho", "Images": "Imagens",
    "Community tools": "Ferramentas da comunidade", "Profile tools": "Ferramentas do perfil",
    "Draft controls": "Controles do rascunho", "Draft body": "Corpo do rascunho",
    "Select an image to preview it.": "Selecione uma imagem para ver a prévia.",
    "The app reads these files only. It never copies or creates artwork.": "O programa apenas lê estes arquivos. Ele não copia nem cria arte.",
    "Content type": "Tipo de conteúdo", "Link style": "Estilo dos links", "Include starting price": "Incluir preço inicial",
    "Title": "Título", "Copy title": "Copiar título", "Post type": "Tipo de postagem",
    "Commercial use / budget": "Uso comercial / orçamento",
    "Post body": "Corpo da postagem", "Copy body": "Copiar texto", "Live rule check": "Verificação de regras",
    "Community notes": "Notas da comunidade", "Mark as posted": "Marcar como publicado",
    "Save community settings": "Salvar configurações", "Prepare a draft": "Preparar rascunho",
    "Credits": "Créditos",
    "Community settings": "Configurações da comunidade", "Community name": "Nome da comunidade", "Image folder": "Pasta de imagens",
    "Choose folder": "Escolher pasta", "Minimum interval (hours)": "Intervalo mínimo (horas)",
    "Preferred posting times": "Horários preferidos", "Time zone": "Fuso horário", "Preferred days": "Dias preferidos",
    "Good posting window": "Janela ideal", "Allowed link order": "Ordem permitida dos links",
    "Required checks": "Verificações exigidas", "Minimum price": "Preço mínimo", "Forbidden title terms": "Termos proibidos no título",
    "Required title terms": "Termos obrigatórios no título", "One required title term": "Um termo obrigatório no título",
    "Title prefix": "Prefixo do título", "Forbidden domains": "Domínios proibidos", "Required body terms": "Termos obrigatórios no texto",
    "Rules last reviewed": "Regras revisadas em", "Title options (separate options with a line containing ---)": "Opções de título (separe com uma linha contendo ---)",
    "Body options (separate options with a line containing ---)": "Opções de texto (separe com uma linha contendo ---)",
    "Notes for this community": "Notas desta comunidade", "Cancel": "Cancelar", "Save community": "Salvar comunidade",
    "Creator profile": "Perfil do artista", "Profile name": "Nome do perfil", "Starting prices": "Preços iniciais",
    "Links and public contact details": "Links e contatos públicos", "Save profile": "Salvar perfil",
    "Commission advertisements allowed": "Anúncios de commission permitidos",
    "Require @handle in title": "Exigir @handle no título", "Require a price or budget": "Exigir preço ou orçamento",
    "Require a portfolio link": "Exigir link de portfólio", "Require a social link": "Exigir rede social",
    "Open community": "Abrir comunidade", "Link": "Link", "@handle": "@arroba", "Both": "Ambos",
    "Public link": "Link público", "Platform handle": "Arroba da plataforma", "Include": "Incluir",
}


def application_dir() -> Path:
    """Keep the planner database beside a portable executable when frozen."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def data_dir() -> Path:
    """Use a user-writable Linux state directory, retaining portable Windows data."""
    if sys.platform.startswith("linux"):
        state_home = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
        directory = state_home / "rebred"
        try:
            directory.mkdir(parents=True, exist_ok=True)
            return directory
        except OSError:
            # A read-only home directory should not prevent opening the app.
            return application_dir()
    return application_dir()


# The clean distribution deliberately uses its own data file. This prevents it
# from loading a creator profile saved by an earlier personalized build when
# both executables happen to be in the same folder.
DATA_PATH = data_dir() / "rebred_data.json"


def copy_file_paths_to_clipboard(paths: list[Path]) -> None:
    """Put real files on the Windows clipboard as an Explorer-style copy.

    This uses CF_HDROP, the same clipboard data format Windows Explorer uses
    for copied files. It lets compatible browser upload fields receive the
    selected existing files with Ctrl+V without creating duplicate artwork.
    """
    if os.name != "nt":
        raise OSError("File clipboard copying is available only on Windows. On Linux, open the folder and drag the selected images into the browser.")
    if not paths:
        raise ValueError("No image files were selected.")

    # DROPFILES (20 bytes) followed by a double-null-terminated UTF-16 list.
    file_list = "\0".join(str(path.resolve()) for path in paths) + "\0\0"
    payload = struct.pack("<IiiII", 20, 0, 0, 0, 1) + file_list.encode("utf-16le")
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.OpenClipboard.restype = ctypes.c_int
    user32.CloseClipboard.restype = ctypes.c_int
    user32.EmptyClipboard.restype = ctypes.c_int
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p

    handle = kernel32.GlobalAlloc(0x0002, len(payload))  # GMEM_MOVEABLE
    if not handle:
        raise OSError("Windows could not reserve clipboard memory.")
    pointer = kernel32.GlobalLock(handle)
    if not pointer:
        kernel32.GlobalFree(handle)
        raise OSError("Windows could not prepare the copied files.")
    ctypes.memmove(pointer, payload, len(payload))
    kernel32.GlobalUnlock(handle)

    if not user32.OpenClipboard(None):
        kernel32.GlobalFree(handle)
        raise OSError("The clipboard is currently in use by another app.")
    try:
        user32.EmptyClipboard()
        # CF_HDROP = 15. After SetClipboardData succeeds, Windows owns handle.
        if not user32.SetClipboardData(15, handle):
            raise OSError("Windows could not copy the selected image files.")
        handle = None
    finally:
        user32.CloseClipboard()
        if handle:
            kernel32.GlobalFree(handle)


def default_profile(name: str = "New community") -> dict[str, Any]:
    return {
        "name": name,
        "folder": "",
        "min_interval_hours": 48,
        "preferred_times": "",
        "weekday_times": suggested_schedule(", ".join(DAYS)),
        "timezone": "America/Sao_Paulo",
        "preferred_days": ", ".join(DAYS),
        "time_before_minutes": 30,
        "time_after_minutes": 15,
        "link_order": [key for key, _label in SOCIAL_FIELDS],
        "titles": ["[For Hire] Your service | @yourhandle"],
        "bodies": [
            "Hi! I am available for commissions.\n\nPortfolio: https://example.com"
        ],
        "rules": {
            "require_handle": False,
            "banned_title_terms": [],
            "required_title_terms": [],
            "require_price": True,
            "minimum_personal": 0,
            "minimum_commercial": 0,
            "require_portfolio": False,
            "require_social": False,
            "banned_domains": [],
            "required_body_terms": [],
            "required_title_any_terms": [],
            "promotion_allowed": True,
            "title_prefix": "",
            "notes": "Add this community's rules here and update them when the subreddit changes.",
            "last_reviewed": datetime.now().strftime("%Y-%m-%d"),
        },
    }


def community_profile(
    name: str,
    *,
    interval: float = 48,
    days: str = ", ".join(DAYS),
    times: str = "",
    title_prefix: str = "",
    link_order: list[str] | None = None,
    notes: str,
    **rules: Any,
) -> dict[str, Any]:
    """Create a conservative, editable rule pack for one Reddit community."""
    profile = default_profile(name)
    profile.update({
        "min_interval_hours": interval,
        "preferred_days": days,
        "preferred_times": times,
        "weekday_times": suggested_schedule(days),
        "link_order": link_order if link_order is not None else [key for key, _ in SOCIAL_FIELDS],
        "titles": human_title_options(title_prefix),
        "bodies": list(HUMAN_BODY_OPTIONS),
    })
    profile["rules"].update(rules)
    profile["rules"].update({"title_prefix": title_prefix, "notes": notes})
    return profile


def default_data() -> dict[str, Any]:
    anime = default_profile("AnimeCommission")
    anime.update(
        {
            "min_interval_hours": 48,
            "titles": human_title_options(),
            "bodies": list(HUMAN_BODY_OPTIONS),
            "rules": {
                "require_handle": True,
                "banned_title_terms": ["[for hire]", "[commission]"],
                "required_title_terms": [],
                "require_price": True,
                "minimum_personal": 35,
                "minimum_commercial": 100,
                "require_portfolio": True,
                "require_social": True,
                "banned_domains": ["fiverr.com", "deviantart.com"],
                "required_body_terms": [],
                "notes": (
                    "Use the correct flair. Put prices, a direct public portfolio and a "
                    "secondary social link in the post body. Commercial-use offers and "
                    "budgets must be at least $100 USD. Discord may be shared publicly, "
                    "but move the conversation there only after the buyer selects an artist."
                ),
                "last_reviewed": datetime.now().strftime("%Y-%m-%d"),
            },
        }
    )
    anime["preferred_times"] = "10:00, 17:00"
    anime["weekday_times"] = suggested_schedule(", ".join(DAYS))
    anime["link_order"] = ["vgen", "artstation", "instagram", "bluesky", "x", "discord"]

    # Community profiles and schedule defaults are embedded in the program.
    # Rule packs are intentionally conservative and remain editable in Community settings.
    communities = [
        community_profile("artcommission", interval=72, days="Mon, Thu", times="10:00, 11:00",
            notes="Use an objective title. Include a direct portfolio or shop link. Check the current flair and post format before publishing."),
        community_profile("artcommissions", interval=72, days="Tue, Fri", times="12:00",
            link_order=["artstation", "behance", "website", "x", "youtube"],
            notes="Use a title without [For Hire]. The community information in your schedule disallows Instagram, email, LinkedIn and Fiverr. Keep pricing at or above $15/hour and $30 minimum.",
            require_price=True, minimum_personal=30, banned_title_terms=["[for hire]"],
            banned_domains=["instagram.com", "fiverr.com", "linkedin.com"]),
        community_profile("ArtistsforHire", interval=0, days="Mon, Tue, Wed, Thu, Fri, Sat, Sun", times="10:00, 11:00",
            notes="Use a clear service title and a public portfolio. Recheck current flair and account requirements before posting."),
        community_profile("ArtSale", interval=24, days="Wed", times="10:00", title_prefix="[For Hire] ",
            notes="Use [For Hire] in the title, include a starting price in the body, and only use public links that do not require a login.",
            required_title_terms=["[for hire]"], require_price=True, require_portfolio=True),
        community_profile("ArtStore", interval=48, days="Tue", times="11:00", title_prefix="[FOR HIRE] ",
            notes="Use [FOR HIRE] or [SELLING] in the title. Include a direct shop or portfolio link. Fiverr is not allowed.",
            required_title_any_terms=["[for hire]", "[selling]"], banned_domains=["fiverr.com"], require_portfolio=True),
        community_profile("ComicBookCollabs", interval=48, days="Mon, Thu, Sat",
            link_order=["artstation", "behance", "website", "vgen", "instagram", "x"],
            notes="Keep the offer relevant to comics and sequential art. Use a public portfolio that demonstrates the role you are offering, and check the current collaboration format before publishing.",
            require_portfolio=True),
        community_profile("comissions", interval=0, days="Mon, Tue, Wed, Thu, Fri, Sat, Sun", times="10:00", title_prefix="[For Hire] ",
            notes="Use [For Hire] and keep the offer clear. This name is intentionally spelled as the community is listed in your schedule.",
            required_title_terms=["[for hire]"]),
        community_profile("commissionart", interval=0,
            notes="No complete rule set was recorded in the schedule. This profile is included so you can save its folder and drafts, but verify the current community rules before publishing."),
        community_profile("commissions", interval=0, days="Wed, Thu, Fri, Sat, Sun", times="09:00", title_prefix="[For Hire] ",
            notes="State a starting price in the title/body. The schedule records a $30 artwork minimum or $7.50/hour. Wix, Fiverr and URL shorteners are not allowed. Mark NSFW work as spoiler and NSFW.",
            require_price=True, minimum_personal=30, required_title_terms=["[for hire]"],
            banned_domains=["wix.com", "fiverr.com", "bit.ly", "tinyurl.com"]),
        community_profile("Commissions_rh", interval=0,
            notes="No complete rule set was recorded in the schedule. Verify the current rules before publishing."),
        community_profile("DnDart", interval=336, days="Wed", times="07:00", title_prefix="[OC] [For Hire] ",
            link_order=["vgen", "artstation", "website", "instagram", "x"],
            notes="Use an original D&D-related work, [OC] and [For Hire], plus the appropriate self-post/flair. Do not post NSFW work. Rotate the artwork rather than reposting the same set.",
            required_title_terms=["[oc]", "[for hire]"], require_portfolio=True),
        community_profile("dndcommissions", interval=0, days="Mon, Tue, Wed, Thu, Fri, Sat, Sun", times="10:00, 12:00", title_prefix="[COM] ",
            notes="Use [COM] for a commission offer or [ART] for a normal art post. Keep the post D&D-related and start with different artwork when posting again.",
            required_title_any_terms=["[com]", "[art]"]),
        community_profile("gameDevClassifieds", interval=48, days="Mon, Wed, Fri", times="09:00, 14:00", title_prefix="[For Hire] ",
            link_order=["artstation", "behance", "website", "vgen", "x", "linkedin"],
            notes="Keep the offer directly related to games. Use [For Hire] or [Portfolio], identify the role and genre, show a relevant public portfolio, and meet the $30 minimum recorded in the schedule.",
            require_price=True, minimum_personal=30, require_portfolio=True, required_title_any_terms=["[for hire]", "[portfolio]"]),
        community_profile("gameDevJobs", interval=48, days="Mon, Wed, Fri", times="09:00, 14:00", title_prefix="[For Hire] ",
            link_order=["artstation", "behance", "website", "vgen", "x", "linkedin"],
            notes="Keep the offer directly related to games. Use [For Hire] or [Portfolio], identify the role and genre, show a relevant public portfolio, and meet the $30 minimum recorded in the schedule.",
            require_price=True, minimum_personal=30, require_portfolio=True, required_title_any_terms=["[for hire]", "[portfolio]"]),
        community_profile("HungryArtists", interval=168, days="Mon", times="10:00", title_prefix="[For Hire] ",
            link_order=["vgen", "artstation", "cara", "behance", "website", "instagram", "bluesky", "x", "discord"],
            notes="Use [For Hire], include a public portfolio, and meet the schedule's $30 personal and $100 commercial minimums. If you include Instagram, also include another direct portfolio link. Mark NSFW work as spoiler and NSFW.",
            require_price=True, minimum_personal=30, minimum_commercial=100, require_portfolio=True, required_title_terms=["[for hire]"]),
        community_profile("DrawForMe", interval=72, days="Mon, Wed, Fri", times="10:00",
            title_prefix="[Paid Offer] ", link_order=["vgen", "artstation", "website", "instagram", "bluesky", "x", "discord"],
            notes="Use the current paid-offer flair or title format and make it clear that the offer is paid. Keep the post commission-focused, follow the community's karma requirements, and do not promote a paid service through a free-offer post.",
            require_price=True, require_portfolio=True, required_title_any_terms=["[paid offer]", "[for hire]"]),
        community_profile("artistforhire", interval=72, days="Tue, Thu, Sat", times="10:00",
            title_prefix="[For Hire] ", link_order=["vgen", "artstation", "website", "instagram", "bluesky", "x", "discord"],
            notes="This is an artist-focused hiring board. Use [For Hire], explain the service and pricing clearly, and link to a public portfolio. It is intended for lower-cost commissions, so make the offer specific rather than a generic storefront.",
            require_price=True, require_portfolio=True, required_title_terms=["[for hire]"]),
        community_profile("hireanartist", interval=72, days="Tue, Thu, Sun", times="10:00",
            title_prefix="[For Hire] ", link_order=["vgen", "artstation", "website", "instagram", "bluesky", "x", "discord"],
            notes="Use the current artist-for-hire format, show relevant finished work, and state a realistic starting price. Check flair and account requirements immediately before posting.",
            require_price=True, require_portfolio=True, required_title_terms=["[for hire]"]),
        community_profile("VGen", interval=72, days="Mon, Thu, Sat", times="10:00",
            title_prefix="[For Hire] ", link_order=["vgen", "artstation", "instagram", "bluesky", "x", "discord"],
            notes="Share a genuine commission offer and a direct VGen link. Never offer, request, or trade VGen verification codes. Treat unsolicited payment or verification messages as scams.",
            require_portfolio=True, required_title_any_terms=["[for hire]", "commissions"]),
        community_profile("INAT", interval=0,
            notes="Use only when the offer is genuinely for an indie-game team. Check current recruitment rules, role format and payment requirements before publishing."),
        community_profile("LojaDeArte", interval=0,
            notes="Ask the moderators for posting permission and use the required flair before publishing.", promotion_allowed=False),
        community_profile("starvingartists", interval=168, title_prefix="[For Hire] ",
            notes="Use [For Hire], a clear commission offer, price and a direct portfolio. Check the current flair and account requirements before posting.",
            require_price=True, require_portfolio=True, required_title_terms=["[for hire]"]),
        community_profile("ThirstyArtists", interval=0,
            notes="This is for NSFW offers. Follow Reddit's adult-content policy and the community's current NSFW/flair requirements before publishing."),
        community_profile("tabletopartists", interval=0,
            notes="No complete rule set was recorded in the schedule. Confirm current tabletop-art and promotion rules before publishing."),
        community_profile("FantasyArt", interval=0, days="Tue, Wed, Sun", times="12:00",
            notes="This community is for sharing finished fantasy art, not commission advertising. Use its required title/credit format and do not add a commission pitch.", promotion_allowed=False),
        community_profile("Art", interval=0,
            notes="This community is for finished art, not commission advertising. Do not use a For Hire post here. Avoid sketches, WIPs and rough work.", promotion_allowed=False),
        community_profile("Furry", interval=3, days="Mon, Tue, Wed, Thu, Fri, Sat, Sun", times="10:00",
            notes="Credit the artist in the title and include the required link. NSFW work is not allowed. Follow the community's rate and tag limits.", require_portfolio=True),
        community_profile("musclegirlart", interval=0, days="Mon, Tue, Wed, Thu, Fri, Sat, Sun", times="12:00",
            notes="Use the community title format: Name (Artist's name) [Series]. Recheck the current promotion policy before adding commission details."),
        community_profile("DnD", interval=0,
            notes="Do not make a commission advertisement. Keep original art D&D-related, follow the [OC][ART] format and use the designated promotion thread if one is available.", promotion_allowed=False),
        community_profile("DungeonsAndDragons", interval=0,
            notes="Share only D&D-related character art. Do not use this profile for a commission advertisement unless the current rules specifically allow it.", promotion_allowed=False),
        community_profile("yaoi", interval=0,
            notes="Use only for adult gay content that follows the community's NSFW rules. Verify its current self-promotion policy before publishing."),
        community_profile("rule34", interval=0,
            notes="Use only for adult work that follows the community's current rules and Reddit's NSFW requirements. Verify its promotion policy before publishing."),
    ]
    for community in [anime, *communities]:
        key = community["name"].lower()
        if key in COMMUNITY_LINK_POLICIES:
            community["link_order"] = list(COMMUNITY_LINK_POLICIES[key])
        if key in COMMUNITY_BODY_TEMPLATES:
            community["bodies"] = list(COMMUNITY_BODY_TEMPLATES[key])
        community["link_policy_version"] = LINK_POLICY_VERSION

    for community in communities:
        if community["name"] == "LojaDeArte":
            community["titles"] = ["Commissions de {{category}} abertas | {{handle}}"]
            community["bodies"] = [
                "Olá! Estou disponível para commissions de {{category}}. {{emoji}}\n\n"
                "{{price_block}}\n\n{{links}}"
            ]
            community["rules"]["notes"] = (
                "Peça permissão aos moderadores e use a flair exigida antes de publicar. "
                "Este é o único perfil que prepara o resultado em português."
            )
    blank_creator = {"name": "My artist profile", "artist_name": "", "handle": "", "personal_price": 0, "commercial_price": 0, "use_emojis": False, "payment_note": "", "payment_note_pt": "", "contact_note": "", "contact_note_pt": "", "reviews_note": "", "reviews_link": "", "links": {}, "platform_handles": {}, "link_display": {}}
    return {"profiles": [anime, *communities], "creator_profiles": [blank_creator], "history": [], "image_count": 6}


def load_data() -> dict[str, Any]:
    if not DATA_PATH.exists():
        return default_data()
    try:
        loaded = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        if not isinstance(loaded.get("profiles"), list) or not isinstance(loaded.get("history"), list):
            raise ValueError("Invalid planner data")
        # Migrate first-version planner files without losing a person's work.
        defaults = default_data()
        loaded.setdefault("creator_profiles", defaults["creator_profiles"])
        loaded.setdefault("ui_language", "en")
        loaded.setdefault("ui_theme", "light")
        loaded.setdefault("image_count", 6)
        default_creators = {creator["name"]: creator for creator in defaults["creator_profiles"]}
        for creator in loaded["creator_profiles"]:
            starter_creator = default_creators.get(creator.get("name"), {})
            for key, value in starter_creator.items():
                creator.setdefault(key, value)
            creator.setdefault("platform_handles", {})
            creator.setdefault("link_display", {})
        for profile in loaded["profiles"]:
            if profile.get("name") == "ComicBook" and "Add the rules for this community" in " ".join(profile.get("bodies", [])):
                profile["name"] = "ComicBookCollabs"
        # Add new built-in communities to an existing portable database without
        # overwriting folders, templates, or rules the user already changed.
        deduplicated: list[dict[str, Any]] = []
        seen_names: set[str] = set()
        for profile in loaded["profiles"]:
            name = str(profile.get("name", "")).lower()
            if name and name not in seen_names:
                deduplicated.append(profile)
                seen_names.add(name)
        loaded["profiles"] = deduplicated
        for starter in defaults["profiles"]:
            if starter["name"].lower() not in seen_names:
                loaded["profiles"].append(starter)
                seen_names.add(starter["name"].lower())
        for profile in loaded["profiles"]:
            starter = default_profile(profile.get("name", "New community"))
            for key in ("preferred_days", "time_before_minutes", "time_after_minutes", "link_order", "timezone"):
                profile.setdefault(key, starter[key])
            profile.setdefault("weekday_times", suggested_schedule(profile.get("preferred_days", ", ".join(DAYS))))
            for key, value in starter["rules"].items():
                profile.setdefault("rules", {}).setdefault(key, value)
            # A prior rule pack accidentally left the required StarvingArtists
            # tag unavailable. Preserve all other custom settings, but repair
            # that concrete rule for portable databases from earlier betas.
            if str(profile.get("name", "")).lower() == "starvingartists":
                rules = profile.setdefault("rules", {})
                rules["title_prefix"] = "[For Hire] "
                required = rules.setdefault("required_title_terms", [])
                if "[for hire]" not in [str(item).lower() for item in required]:
                    required.append("[for hire]")
                rules["require_price"] = True
                rules["require_portfolio"] = True
                profile["min_interval_hours"] = 168
            if str(profile.get("name", "")).lower() == "artsale":
                profile.setdefault("rules", {})["require_price"] = True
        starter_profiles = {profile["name"].lower(): profile for profile in defaults["profiles"]}
        for profile in loaded["profiles"]:
            starter = starter_profiles.get(str(profile.get("name", "")).lower())
            if not starter:
                continue
            # Version 0.8 adds three suggested windows per allowed weekday.
            # Existing custom schedules are left untouched once saved.
            profile.setdefault("weekday_times", starter.get("weekday_times", suggested_schedule(profile.get("preferred_days", ", ".join(DAYS)))))
            # Apply the 0.9 conservative contact policy once. From then on,
            # people remain free to change the allowed order in settings.
            if int(profile.get("link_policy_version", 0) or 0) < LINK_POLICY_VERSION:
                profile["link_order"] = list(starter.get("link_order", []))
                profile["link_policy_version"] = LINK_POLICY_VERSION
            custom_bodies = COMMUNITY_BODY_TEMPLATES.get(str(profile.get("name", "")).lower())
            if custom_bodies and profile.get("bodies", []) == HUMAN_BODY_OPTIONS:
                profile["bodies"] = list(custom_bodies)
            for key in ("titles", "bodies"):
                existing = profile.setdefault(key, [])
                for option in starter[key]:
                    if option not in existing:
                        existing.append(option)
        return loaded
    except (OSError, ValueError, json.JSONDecodeError):
        messagebox.showwarning(
            "Planner data", "The saved data could not be read. A new local database was created."
        )
        return default_data()


def split_options(value: str) -> list[str]:
    return [item.strip() for item in value.split(SEPARATOR) if item.strip()]


def join_options(items: list[str]) -> str:
    return SEPARATOR.join(items)


def parse_csv(value: str) -> list[str]:
    return [item.strip().lower() for item in value.split(",") if item.strip()]


class ProfileDialog(tk.Toplevel):
    def __init__(self, app: "PlannerApp", profile: dict[str, Any] | None = None):
        super().__init__(app)
        self.app = app
        self.profile = profile or default_profile()
        self.result: dict[str, Any] | None = None
        self.title("Community settings")
        self.geometry("840x820")
        self.minsize(700, 600)
        self.transient(app)
        self.grab_set()

        form = ttk.Frame(self, padding=16)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)

        self.name_var = tk.StringVar(value=self.profile["name"])
        self.folder_var = tk.StringVar(value=self.profile.get("folder", ""))
        self.interval_var = tk.StringVar(value=str(self.profile.get("min_interval_hours", 48)))
        self.times_var = tk.StringVar(value=self.profile.get("preferred_times", ""))
        self.weekday_times = dict(self.profile.get("weekday_times", {}))
        self.timezone_var = tk.StringVar(value=self.profile.get("timezone", "America/Sao_Paulo"))
        self.days_var = tk.StringVar(value=self.profile.get("preferred_days", ", ".join(DAYS)))
        self.before_var = tk.StringVar(value=str(self.profile.get("time_before_minutes", 30)))
        self.after_var = tk.StringVar(value=str(self.profile.get("time_after_minutes", 15)))
        self.link_order_var = tk.StringVar(value=", ".join(self.profile.get("link_order", [])))
        rules = self.profile["rules"]
        self.handle_var = tk.BooleanVar(value=rules.get("require_handle", False))
        self.price_var = tk.BooleanVar(value=rules.get("require_price", True))
        self.portfolio_var = tk.BooleanVar(value=rules.get("require_portfolio", False))
        self.social_var = tk.BooleanVar(value=rules.get("require_social", False))
        self.personal_var = tk.StringVar(value=str(rules.get("minimum_personal", 0)))
        self.commercial_var = tk.StringVar(value=str(rules.get("minimum_commercial", 0)))
        self.banned_title_var = tk.StringVar(value=", ".join(rules.get("banned_title_terms", [])))
        self.required_title_var = tk.StringVar(value=", ".join(rules.get("required_title_terms", [])))
        self.banned_domain_var = tk.StringVar(value=", ".join(rules.get("banned_domains", [])))
        self.required_body_var = tk.StringVar(value=", ".join(rules.get("required_body_terms", [])))
        self.required_title_any_var = tk.StringVar(value=", ".join(rules.get("required_title_any_terms", [])))
        self.title_prefix_var = tk.StringVar(value=rules.get("title_prefix", ""))
        self.promotion_var = tk.BooleanVar(value=rules.get("promotion_allowed", True))
        self.reviewed_var = tk.StringVar(value=rules.get("last_reviewed", ""))

        def row(label: str, widget: tk.Widget, index: int) -> None:
            ttk.Label(form, text=label).grid(row=index, column=0, sticky="nw", padx=(0, 12), pady=5)
            widget.grid(row=index, column=1, sticky="ew", pady=5)

        row("Community name", ttk.Entry(form, textvariable=self.name_var), 0)
        folder_row = ttk.Frame(form)
        folder_row.columnconfigure(0, weight=1)
        ttk.Entry(folder_row, textvariable=self.folder_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(folder_row, text="Choose folder", command=self.choose_folder).grid(row=0, column=1, padx=(8, 0))
        row("Image folder", folder_row, 1)
        row("Minimum interval (hours)", ttk.Entry(form, textvariable=self.interval_var, width=12), 2)
        row("Preferred posting times", ttk.Entry(form, textvariable=self.times_var), 3)
        ttk.Label(form, text="Example: 09:00, 13:00, 19:00. Leave blank to use the earliest allowed time.", foreground="#666").grid(row=4, column=1, sticky="w")
        ttk.Label(form, text="Weekly suggested windows (one line per day, Brasília time)").grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 3))
        self.weekly_times_text = tk.Text(form, height=7, wrap="none")
        weekly_text = "\n".join(f"{day}: {self.weekday_times.get(day, '')}" for day in DAYS)
        self.weekly_times_text.insert("1.0", weekly_text)
        self.weekly_times_text.grid(row=6, column=0, columnspan=2, sticky="ew")
        ttk.Label(form, text="Use three times on the days you want to post. Empty a day to exclude it.", foreground="#666").grid(row=7, column=1, sticky="w")
        row("Time zone", ttk.Entry(form, textvariable=self.timezone_var), 8)
        ttk.Label(form, text="Use America/Sao_Paulo for Brasília time.", foreground="#666").grid(row=9, column=1, sticky="w")
        row("Preferred days", ttk.Entry(form, textvariable=self.days_var), 10)
        window = ttk.Frame(form)
        ttk.Label(window, text="Minutes before:").grid(row=0, column=0, padx=(0, 5))
        ttk.Entry(window, textvariable=self.before_var, width=7).grid(row=0, column=1, padx=(0, 14))
        ttk.Label(window, text="Minutes after:").grid(row=0, column=2, padx=(0, 5))
        ttk.Entry(window, textvariable=self.after_var, width=7).grid(row=0, column=3)
        row("Good posting window", window, 11)
        row("Allowed link order", ttk.Entry(form, textvariable=self.link_order_var), 12)
        ttk.Label(form, text="Use field keys such as vgen, artstation, instagram, x, discord. Only filled and allowed links appear.", foreground="#666").grid(row=13, column=1, sticky="w")

        checks = ttk.Frame(form)
        ttk.Checkbutton(checks, text="Require @handle in title", variable=self.handle_var).grid(row=0, column=0, sticky="w", padx=(0, 14))
        ttk.Checkbutton(checks, text="Require a price or budget", variable=self.price_var).grid(row=0, column=1, sticky="w")
        ttk.Checkbutton(checks, text="Require a portfolio link", variable=self.portfolio_var).grid(row=1, column=0, sticky="w", padx=(0, 14))
        ttk.Checkbutton(checks, text="Require a social link", variable=self.social_var).grid(row=1, column=1, sticky="w")
        ttk.Checkbutton(checks, text="Commission advertisements allowed", variable=self.promotion_var).grid(row=2, column=0, columnspan=2, sticky="w")
        row("Required checks", checks, 14)

        prices = ttk.Frame(form)
        ttk.Label(prices, text="Personal $:").grid(row=0, column=0, padx=(0, 5))
        ttk.Entry(prices, textvariable=self.personal_var, width=8).grid(row=0, column=1, padx=(0, 18))
        ttk.Label(prices, text="Commercial $:").grid(row=0, column=2, padx=(0, 5))
        ttk.Entry(prices, textvariable=self.commercial_var, width=8).grid(row=0, column=3)
        row("Minimum price", prices, 15)
        row("Forbidden title terms", ttk.Entry(form, textvariable=self.banned_title_var), 16)
        row("Required title terms", ttk.Entry(form, textvariable=self.required_title_var), 17)
        row("One required title term", ttk.Entry(form, textvariable=self.required_title_any_var), 18)
        row("Title prefix", ttk.Entry(form, textvariable=self.title_prefix_var), 19)
        row("Forbidden domains", ttk.Entry(form, textvariable=self.banned_domain_var), 20)
        row("Required body terms", ttk.Entry(form, textvariable=self.required_body_var), 21)
        row("Rules last reviewed", ttk.Entry(form, textvariable=self.reviewed_var), 22)

        ttk.Label(form, text="Title options (separate options with a line containing ---)").grid(row=23, column=0, columnspan=2, sticky="w", pady=(12, 4))
        self.titles_text = tk.Text(form, height=5, wrap="word")
        self.titles_text.insert("1.0", join_options(self.profile.get("titles", [])))
        self.titles_text.grid(row=24, column=0, columnspan=2, sticky="nsew")

        ttk.Label(form, text="Body options (separate options with a line containing ---)").grid(row=25, column=0, columnspan=2, sticky="w", pady=(10, 4))
        self.bodies_text = tk.Text(form, height=8, wrap="word")
        self.bodies_text.insert("1.0", join_options(self.profile.get("bodies", [])))
        self.bodies_text.grid(row=26, column=0, columnspan=2, sticky="nsew")
        form.rowconfigure(26, weight=1)

        ttk.Label(form, text="Notes for this community").grid(row=27, column=0, columnspan=2, sticky="w", pady=(10, 4))
        self.notes_text = tk.Text(form, height=4, wrap="word")
        self.notes_text.insert("1.0", rules.get("notes", ""))
        self.notes_text.grid(row=28, column=0, columnspan=2, sticky="nsew")

        actions = ttk.Frame(form)
        actions.grid(row=29, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(actions, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(actions, text="Save community", command=self.save).pack(side="right", padx=(0, 8))
        app.localize_window(self)
        app.apply_widget_theme(self)

    def choose_folder(self) -> None:
        chosen = filedialog.askdirectory(parent=self, title="Choose the image folder")
        if chosen:
            self.folder_var.set(chosen)

    @staticmethod
    def non_negative_number(value: str, label: str) -> float:
        try:
            number = float(value or 0)
        except ValueError as exc:
            raise ValueError(f"{label} must be a number.") from exc
        if number < 0:
            raise ValueError(f"{label} cannot be negative.")
        return number

    def save(self) -> None:
        try:
            name = self.name_var.get().strip()
            if not name:
                raise ValueError("Community name is required.")
            interval = self.non_negative_number(self.interval_var.get(), "Minimum interval")
            before = self.non_negative_number(self.before_var.get(), "Minutes before")
            after = self.non_negative_number(self.after_var.get(), "Minutes after")
            personal = self.non_negative_number(self.personal_var.get(), "Personal minimum")
            commercial = self.non_negative_number(self.commercial_var.get(), "Commercial minimum")
            titles = split_options(self.titles_text.get("1.0", "end"))
            bodies = split_options(self.bodies_text.get("1.0", "end"))
            if not titles or not bodies:
                raise ValueError("Add at least one title and one body option.")
            weekday_times: dict[str, str] = {}
            for raw_line in self.weekly_times_text.get("1.0", "end").splitlines():
                if not raw_line.strip():
                    continue
                if ":" not in raw_line:
                    raise ValueError("Weekly times need the format Mon: 09:00, 13:00, 19:00.")
                day, values = raw_line.split(":", 1)
                normalized_day = day.strip().title()[:3]
                if normalized_day not in DAYS:
                    raise ValueError("Weekly times use Mon, Tue, Wed, Thu, Fri, Sat or Sun.")
                if values.strip():
                    weekday_times[normalized_day] = values.strip()
        except ValueError as error:
            messagebox.showerror("Check the settings", str(error), parent=self)
            return

        self.result = {
            "name": name,
            "folder": self.folder_var.get().strip(),
            "min_interval_hours": interval,
            "preferred_times": self.times_var.get().strip(),
            "weekday_times": weekday_times,
            "timezone": self.timezone_var.get().strip() or "America/Sao_Paulo",
            "preferred_days": self.days_var.get().strip(),
            "time_before_minutes": before,
            "time_after_minutes": after,
            "link_order": [item.strip().lower() for item in self.link_order_var.get().split(",") if item.strip()],
            "titles": titles,
            "bodies": bodies,
            "rules": {
                "require_handle": self.handle_var.get(),
                "banned_title_terms": parse_csv(self.banned_title_var.get()),
                "required_title_terms": parse_csv(self.required_title_var.get()),
                "required_title_any_terms": parse_csv(self.required_title_any_var.get()),
                "title_prefix": self.title_prefix_var.get().strip(),
                "promotion_allowed": self.promotion_var.get(),
                "require_price": self.price_var.get(),
                "minimum_personal": personal,
                "minimum_commercial": commercial,
                "require_portfolio": self.portfolio_var.get(),
                "require_social": self.social_var.get(),
                "banned_domains": parse_csv(self.banned_domain_var.get()),
                "required_body_terms": parse_csv(self.required_body_var.get()),
                "notes": self.notes_text.get("1.0", "end").strip(),
                "last_reviewed": self.reviewed_var.get().strip(),
            },
        }
        self.destroy()


class CreatorDialog(tk.Toplevel):
    """A reusable artist/client profile. Community rules decide which links appear."""
    def __init__(self, app: "PlannerApp", creator: dict[str, Any] | None = None):
        super().__init__(app)
        self.app = app
        self.creator = creator or {"name": "New profile", "handle": "", "personal_price": 0, "commercial_price": 0, "use_emojis": False, "links": {}, "platform_handles": {}, "link_display": {}}
        self.result: dict[str, Any] | None = None
        self.title("Creator profile")
        self.geometry("930x800")
        self.minsize(760, 650)
        self.transient(app)
        self.grab_set()
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)
        root.columnconfigure(1, weight=3)
        root.columnconfigure(2, weight=2)
        root.columnconfigure(3, weight=1)
        self.name_var = tk.StringVar(value=self.creator.get("name", ""))
        self.handle_var = tk.StringVar(value=self.creator.get("handle", ""))
        self.personal_var = tk.StringVar(value=str(self.creator.get("personal_price", 0)))
        self.commercial_var = tk.StringVar(value=str(self.creator.get("commercial_price", 0)))
        self.emoji_var = tk.BooleanVar(value=self.creator.get("use_emojis", False))
        def add(label: str, widget: tk.Widget, row: int) -> None:
            ttk.Label(root, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
            widget.grid(row=row, column=1, columnspan=3, sticky="ew", pady=4)
        add("Profile name", ttk.Entry(root, textvariable=self.name_var), 0)
        add("@handle", ttk.Entry(root, textvariable=self.handle_var), 1)
        prices = ttk.Frame(root)
        ttk.Label(prices, text="Personal USD").pack(side="left")
        ttk.Entry(prices, textvariable=self.personal_var, width=9).pack(side="left", padx=(5, 12))
        ttk.Label(prices, text="Commercial USD").pack(side="left")
        ttk.Entry(prices, textvariable=self.commercial_var, width=9).pack(side="left", padx=5)
        add("Starting prices", prices, 2)
        ttk.Checkbutton(root, text="Use a few suitable emojis when a draft has the {{emoji}} placeholder", variable=self.emoji_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 10))
        ttk.Label(root, text="Links and public contact details").grid(row=4, column=0, columnspan=4, sticky="w", pady=(2, 4))
        ttk.Label(root, text="Public link").grid(row=5, column=1, sticky="w", padx=(0, 8))
        ttk.Label(root, text="Platform handle").grid(row=5, column=2, sticky="w", padx=(0, 8))
        ttk.Label(root, text="Include").grid(row=5, column=3, sticky="w")
        self.link_vars: dict[str, tk.StringVar] = {}
        self.platform_handle_vars: dict[str, tk.StringVar] = {}
        self.link_display_vars: dict[str, tk.StringVar] = {}
        for row, (key, label) in enumerate(SOCIAL_FIELDS, start=6):
            value = self.creator.get("links", {}).get(key, "")
            link_var = tk.StringVar(value=value)
            handle_var = tk.StringVar(value=self.creator.get("platform_handles", {}).get(key, "").lstrip("@"))
            saved_display = self.creator.get("link_display", {}).get(key, "")
            display = saved_display if saved_display in {"Link", "@handle", "Both"} else ("Link" if value else "@handle")
            display_var = tk.StringVar(value=display)
            self.link_vars[key] = link_var
            self.platform_handle_vars[key] = handle_var
            self.link_display_vars[key] = display_var
            ttk.Label(root, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
            ttk.Entry(root, textvariable=link_var).grid(row=row, column=1, sticky="ew", padx=(0, 8), pady=4)
            ttk.Entry(root, textvariable=handle_var).grid(row=row, column=2, sticky="ew", padx=(0, 8), pady=4)
            ttk.Combobox(root, textvariable=display_var, values=["Link", "@handle", "Both"], state="readonly", width=10).grid(row=row, column=3, sticky="ew", pady=4)
        actions = ttk.Frame(root)
        actions.grid(row=6 + len(SOCIAL_FIELDS), column=0, columnspan=4, sticky="e", pady=(15, 0))
        ttk.Button(actions, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(actions, text="Save profile", command=self.save).pack(side="right", padx=(0, 8))
        app.localize_window(self)
        app.apply_widget_theme(self)

    def save(self) -> None:
        try:
            personal = float(self.personal_var.get() or 0)
            commercial = float(self.commercial_var.get() or 0)
            if personal < 0 or commercial < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Check prices", "Prices must be zero or a positive number.", parent=self)
            return
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Profile name", "Profile name is required.", parent=self)
            return
        # Keep optional notes and template fields from an imported profile even
        # though this dialog is only editing its public contact information.
        self.result = dict(self.creator)
        self.result.update({
            "name": name,
            "handle": self.handle_var.get().strip().lstrip("@"),
            "personal_price": personal,
            "commercial_price": commercial,
            "use_emojis": self.emoji_var.get(),
            "links": {key: var.get().strip() for key, var in self.link_vars.items() if var.get().strip()},
            "platform_handles": {key: var.get().strip().lstrip("@") for key, var in self.platform_handle_vars.items() if var.get().strip()},
            "link_display": {key: var.get() for key, var in self.link_display_vars.items()},
        })
        self.destroy()


class PlannerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry("1220x790")
        self.minsize(980, 650)
        # Start maximized while preserving normal desktop controls. Tk uses a
        # different maximize API on common Linux window managers.
        if sys.platform.startswith("win"):
            self.state("zoomed")
        else:
            self.after_idle(self.maximize_window)
        self.data = load_data()
        self.ui_language = self.data.get("ui_language", "en")
        self.ui_theme = self.data.get("ui_theme", "light")
        self._source_widget_text: dict[str, str] = {}
        self.current_index = 0
        self.creator_index = 0
        self.profile_order: list[int] = []
        self.selected_images: list[Path] = []
        self.commercial_var = tk.BooleanVar(value=False)
        self.post_type_var = tk.StringVar(value="For Hire")
        self.category_var = tk.StringVar(value="Anime")
        self.link_style_var = tk.StringVar(value="Markdown")
        self.include_price_var = tk.BooleanVar(value=True)
        saved_image_count = self.data.get("image_count", 6)
        self.image_count_var = tk.IntVar(value=saved_image_count if isinstance(saved_image_count, int) and 1 <= saved_image_count <= 9 else 6)
        self.title_tag_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Choose a community to prepare a manual draft.")
        self.repost_notice_var = tk.StringVar(value="")
        self.community_search_var = tk.StringVar(value="")
        self.community_count_var = tk.StringVar(value="")
        self.title_count_var = tk.StringVar(value=f"0 / {TITLE_CHARACTER_LIMIT}")
        self.body_count_var = tk.StringVar(value="0 characters")
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.build_interface()
        self.capture_ui_texts()
        self.apply_ui_language()
        self.apply_ui_theme()
        self.refresh_profiles()
        self.refresh_creators()
        self.load_profile(0)
        self.after(60_000, self.refresh_clock)

    @property
    def profile(self) -> dict[str, Any]:
        return self.data["profiles"][self.current_index]

    @property
    def creator(self) -> dict[str, Any]:
        return self.data["creator_profiles"][self.creator_index]

    def maximize_window(self) -> None:
        """Request maximized mode on Linux without failing on unsupported WMs."""
        try:
            self.attributes("-zoomed", True)
        except tk.TclError:
            pass

    def build_interface(self) -> None:
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        outer = ttk.Frame(self, padding=14)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, minsize=285)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(0, weight=1)

        left = ttk.Frame(outer, padding=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        ttk.Label(left, text="Communities", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(left, text="Each community has its own folder, drafts and rule checks.", wraplength=245).pack(anchor="w", pady=(2, 10))
        search_row = ttk.Frame(left)
        search_row.pack(fill="x", pady=(0, 4))
        ttk.Label(search_row, text="Search communities").pack(side="left")
        ttk.Button(search_row, text="Clear", command=lambda: self.community_search_var.set("")).pack(side="right")
        search_entry = ttk.Entry(left, textvariable=self.community_search_var)
        search_entry.pack(fill="x", pady=(0, 4))
        self.community_search_var.trace_add("write", lambda *_args: self.refresh_profiles())
        ttk.Label(left, textvariable=self.community_count_var).pack(anchor="w", pady=(0, 5))

        legend = ttk.Frame(left)
        legend.pack(fill="x", pady=(0, 6))
        for rank, label in enumerate(("Ready", "Soon", "Outside", "Locked")):
            ttk.Label(legend, text=f"● {label}", style=f"Availability{rank}.TLabel").pack(side="left", padx=(0, 6))

        list_frame = ttk.Frame(left)
        list_frame.pack(fill="both", expand=True)
        self.profile_list = tk.Listbox(list_frame, exportselection=False, height=20, activestyle="none")
        profile_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.profile_list.yview)
        self.profile_list.configure(yscrollcommand=profile_scrollbar.set)
        self.profile_list.pack(side="left", fill="both", expand=True)
        profile_scrollbar.pack(side="right", fill="y")
        self.profile_list.bind("<<ListboxSelect>>", self.on_profile_select)
        profile_buttons = ttk.Frame(left)
        profile_buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(profile_buttons, text="Add", command=self.add_profile).pack(side="left")
        ttk.Button(profile_buttons, text="Edit", command=self.edit_profile).pack(side="left", padx=5)
        ttk.Button(profile_buttons, text="Remove", command=self.remove_profile).pack(side="left")
        ttk.Button(left, text="Export community template", command=self.export_profile).pack(fill="x", pady=(14, 4))
        ttk.Button(left, text="Import community template", command=self.import_profile).pack(fill="x")
        ttk.Button(left, text="Copy settings to…", command=self.copy_community_settings).pack(fill="x", pady=(4, 0))
        ttk.Separator(left).pack(fill="x", pady=14)
        ttk.Label(left, text="Creator profile", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.creator_combo = ttk.Combobox(left, state="readonly")
        self.creator_combo.pack(fill="x", pady=(4, 5))
        self.creator_combo.bind("<<ComboboxSelected>>", self.on_creator_select)
        creator_buttons = ttk.Frame(left)
        creator_buttons.pack(fill="x")
        ttk.Button(creator_buttons, text="Add", command=self.add_creator).pack(side="left")
        ttk.Button(creator_buttons, text="Edit", command=self.edit_creator).pack(side="left", padx=5)
        ttk.Button(creator_buttons, text="Remove profile", command=self.remove_creator).pack(side="left")
        ttk.Button(creator_buttons, text="Export", command=self.export_creator).pack(side="left")
        ttk.Button(left, text="Import creator template", command=self.import_creator).pack(fill="x", pady=(5, 0))

        right = ttk.Frame(outer, padding=8)
        right.grid(row=0, column=1, sticky="nsew")
        header = ttk.Frame(right)
        header.pack(fill="x")
        self.community_heading = ttk.Label(header, text="", font=("Segoe UI", 18, "bold"))
        self.community_heading.pack(side="left")
        self.language_button = ttk.Button(header, command=self.toggle_ui_language)
        self.language_button.pack(side="right")
        self.theme_button = ttk.Button(header, command=self.toggle_ui_theme)
        self.theme_button.pack(side="right", padx=(0, 7))
        ttk.Button(header, text="Credits", command=self.open_credits).pack(side="right", padx=(0, 7))

        metadata = ttk.Frame(right)
        metadata.pack(fill="x", pady=(4, 10))
        self.folder_label = ttk.Label(metadata, text="")
        self.folder_label.pack(side="left", fill="x", expand=True)
        ttk.Label(metadata, textvariable=self.status_var, style="Status.TLabel", anchor="e", justify="right", wraplength=520).pack(side="right")

        category_bar = ttk.LabelFrame(right, text="Draft options", padding=8)
        category_bar.pack(fill="x", pady=(0, 6))
        options_row = ttk.Frame(category_bar)
        options_row.pack(fill="x")
        actions_row = ttk.Frame(category_bar)
        actions_row.pack(fill="x", pady=(7, 0))
        ttk.Label(options_row, text="Content type").pack(side="left")
        category_picker = ttk.Combobox(options_row, textvariable=self.category_var, values=CATEGORY_LABELS, state="readonly", width=16)
        category_picker.pack(side="left", padx=(8, 16))
        category_picker.bind("<<ComboboxSelected>>", lambda _event: self.validate())
        ttk.Label(options_row, text="Link style").pack(side="left")
        links = ttk.Combobox(options_row, textvariable=self.link_style_var, values=["Markdown", "Rich text"], state="readonly", width=12)
        links.pack(side="left", padx=8)
        links.bind("<<ComboboxSelected>>", lambda _event: self.validate())
        self.include_price_check = ttk.Checkbutton(options_row, text="Include starting price", variable=self.include_price_var, command=self.validate)
        self.include_price_check.pack(side="left", padx=(8, 0))
        ttk.Label(actions_row, text="Images to select (1–9)").pack(side="left")
        image_count = ttk.Combobox(actions_row, textvariable=self.image_count_var, values=list(range(1, 10)), state="readonly", width=3)
        image_count.pack(side="left", padx=(6, 0))
        image_count.bind("<<ComboboxSelected>>", self.on_image_count_changed)
        self.title_tag_check = ttk.Checkbutton(actions_row, variable=self.title_tag_var, command=self.on_title_tag_toggle)
        self.title_tag_check.pack(side="left", padx=(12, 0))
        self.prepare_button = ttk.Button(actions_row, text="Prepare a draft", command=self.prepare_draft, width=18, style="Accent.TButton")
        self.prepare_button.pack(side="right")
        self.open_community_button = ttk.Button(actions_row, text="Open community", command=self.open_community)
        self.open_community_button.pack(side="right", padx=(0, 8))

        # The two splitters keep the workspace compact while allowing the
        # draft, image preview, rules and notes to be resized independently.
        content_stack = ttk.PanedWindow(right, orient="vertical")
        content_stack.pack(fill="both", expand=True)
        editor = ttk.PanedWindow(content_stack, orient="horizontal")
        content_stack.add(editor, weight=4)

        draft_column = ttk.Frame(editor)
        editor.add(draft_column, weight=3)
        title_heading = ttk.Frame(draft_column)
        title_heading.pack(fill="x")
        ttk.Label(title_heading, text="Title").pack(side="left")
        self.title_count_label = ttk.Label(title_heading, textvariable=self.title_count_var, style="Counter.TLabel")
        self.title_count_label.pack(side="right")
        title_frame = ttk.LabelFrame(draft_column, text="Draft controls", padding=8)
        title_frame.pack(fill="x", pady=(2, 8))
        title_frame.columnconfigure(0, weight=1)
        self.title_entry = ttk.Entry(title_frame, font=("Segoe UI", 11))
        self.title_entry.grid(row=0, column=0, sticky="ew")
        self.title_entry.bind("<KeyRelease>", lambda _event: self.validate())
        self.title_entry.bind("<FocusOut>", lambda _event: self.validate())
        ttk.Button(title_frame, text="Copy title", command=lambda: self.copy_text(self.title_entry.get(), "Title copied.")).grid(row=0, column=1, padx=(7, 0))
        ttk.Label(title_frame, text="Post type").grid(row=1, column=0, sticky="w", pady=(14, 2))
        post_type = ttk.Combobox(title_frame, textvariable=self.post_type_var, values=["For Hire", "Hiring", "Artwork / OC", "Portfolio Review", "Meta"], state="readonly")
        post_type.grid(row=2, column=0, sticky="w")
        post_type.bind("<<ComboboxSelected>>", lambda _event: self.validate())
        ttk.Checkbutton(title_frame, text="Commercial use / budget", variable=self.commercial_var, command=self.validate).grid(row=3, column=0, sticky="w", pady=(8, 0))

        body_frame = ttk.LabelFrame(draft_column, text="Draft body", padding=8)
        body_frame.pack(fill="both", expand=True)
        body_frame.columnconfigure(0, weight=1)
        body_frame.rowconfigure(0, weight=0)
        self.body_text = tk.Text(body_frame, height=13, wrap="word", font=("Segoe UI", 10))
        self.body_count_label = ttk.Label(body_frame, textvariable=self.body_count_var, style="Counter.TLabel")
        self.body_count_label.grid(row=0, column=0, sticky="e", pady=(0, 4))
        self.body_text.grid(row=1, column=0, sticky="nsew")
        body_frame.rowconfigure(1, weight=1)
        self.body_text.bind("<KeyRelease>", lambda _event: self.validate())
        ttk.Button(body_frame, text="Copy body", command=lambda: self.copy_text(self.body_text.get("1.0", "end").strip(), "Body copied.")).grid(row=0, column=1, sticky="n", padx=(7, 0))

        image_column = ttk.Frame(editor)
        editor.add(image_column, weight=2)
        ttk.Label(image_column, text="Selected images").pack(anchor="w")
        image_frame = ttk.LabelFrame(image_column, text="Images", padding=10)
        image_frame.pack(fill="both", expand=True, pady=(2, 0))
        image_frame.columnconfigure(0, weight=3)
        image_frame.columnconfigure(1, weight=2)
        image_frame.rowconfigure(0, weight=1)
        self.image_list = tk.Listbox(image_frame, exportselection=False, selectmode="extended", height=9)
        self.image_list.grid(row=0, column=0, sticky="nsew")
        self.image_list.bind("<<ListboxSelect>>", self.on_image_select)
        self.image_list.bind("<Control-c>", self.copy_selected_images)
        preview_frame = ttk.Frame(image_frame)
        preview_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.thumbnail_image: ImageTk.PhotoImage | None = None
        self.thumbnail_label = ttk.Label(preview_frame, text="Select an image to preview it.", anchor="center", justify="center", wraplength=190)
        self.thumbnail_label.pack(fill="both", expand=True)
        self.thumbnail_name = ttk.Label(preview_frame, text="", anchor="center", wraplength=190)
        self.thumbnail_name.pack(fill="x", pady=(6, 0))
        image_actions = ttk.Frame(image_frame)
        image_actions.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(image_actions, text="Choose image folder…", command=self.choose_image_folder).pack(side="left")
        ttk.Button(image_actions, text="Open selected folder", command=self.open_folder).pack(side="left", padx=(6, 0))
        ttk.Button(image_actions, text="Copy selected images", command=self.copy_selected_images).pack(side="left")
        ttk.Label(image_actions, text="The app reads these files only. It never copies or creates artwork.", wraplength=220).pack(side="left", padx=(8, 0))

        bottom = ttk.PanedWindow(content_stack, orient="horizontal")
        content_stack.add(bottom, weight=2)
        validation_box = ttk.LabelFrame(bottom, text="Live rule check", padding=8)
        bottom.add(validation_box, weight=3)
        self.validation_text = tk.Text(validation_box, height=8, wrap="word", state="disabled", font=("Segoe UI", 9))
        self.validation_text.pack(fill="both", expand=True)
        notes_box = ttk.LabelFrame(bottom, text="Community notes", padding=8)
        bottom.add(notes_box, weight=2)
        self.notes_label = ttk.Label(notes_box, text="", wraplength=360, justify="left")
        self.notes_label.pack(fill="both", expand=True)

        footer = ttk.Frame(right)
        footer.pack(fill="x", pady=(10, 0))
        self.repost_notice_label = ttk.Label(footer, textvariable=self.repost_notice_var, wraplength=500, justify="left")
        self.repost_notice_label.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.mark_posted_button = ttk.Button(footer, text="Mark as posted", command=self.mark_posted)
        self.mark_posted_button.pack(side="right")
        ttk.Button(footer, text="Save community settings", command=self.save_community_settings).pack(side="right", padx=(0, 8))

    def capture_ui_texts(self) -> None:
        """Store the original UI labels so the language selector is reversible."""
        def visit(widget: tk.Misc) -> None:
            try:
                value = str(widget.cget("text"))
            except tk.TclError:
                value = ""
            if value:
                self._source_widget_text[str(widget)] = value
            for child in widget.winfo_children():
                visit(child)
        visit(self)

    def apply_ui_language(self) -> None:
        for widget_name, english in self._source_widget_text.items():
            try:
                widget = self.nametowidget(widget_name)
                translated = UI_PT.get(english, english) if self.ui_language == "pt" else english
                widget.configure(text=translated)
            except (KeyError, tk.TclError):
                continue
        self.refresh_toggle_labels()

    def refresh_toggle_labels(self) -> None:
        self.language_button.configure(text="English" if self.ui_language == "pt" else "Português")
        if self.ui_language == "pt":
            self.theme_button.configure(text="Modo claro" if self.ui_theme == "dark" else "Modo escuro")
        else:
            self.theme_button.configure(text="Light mode" if self.ui_theme == "dark" else "Dark mode")

    def localize_window(self, root: tk.Misc) -> None:
        """Translate a newly opened settings window without touching post drafts."""
        if self.ui_language != "pt":
            return
        def visit(widget: tk.Misc) -> None:
            try:
                text = str(widget.cget("text"))
                if text:
                    widget.configure(text=UI_PT.get(text, text))
            except tk.TclError:
                pass
            for child in widget.winfo_children():
                visit(child)
        visit(root)

    def apply_widget_theme(self, root: tk.Misc) -> None:
        """Apply the selected colour palette to Tk widgets without styling drafts."""
        dark = self.ui_theme == "dark"
        background = "#20252b" if dark else "#f5f6f8"
        foreground = "#edf1f5" if dark else "#20242a"
        field = "#2b3138" if dark else "#ffffff"
        insert = "#edf1f5" if dark else "#20242a"
        def visit(widget: tk.Misc) -> None:
            if isinstance(widget, (tk.Text, tk.Listbox)):
                try:
                    widget.configure(background=field, foreground=foreground, insertbackground=insert,
                                     selectbackground="#526c86" if dark else "#bfd8f2",
                                     selectforeground="#ffffff" if dark else "#17212b",
                                     highlightthickness=1, highlightbackground="#3c444e" if dark else "#d5dce5",
                                     highlightcolor="#83a9d4" if dark else "#648bb8")
                except tk.TclError:
                    pass
            for child in widget.winfo_children():
                visit(child)
        visit(root)

    def apply_ui_theme(self) -> None:
        dark = self.ui_theme == "dark"
        background = "#20252b" if dark else "#f5f6f8"
        foreground = "#edf1f5" if dark else "#20242a"
        field = "#2b3138" if dark else "#ffffff"
        button = "#3a4b5d" if dark else "#e7edf4"
        active = "#506b87" if dark else "#d4e2f1"
        style = ttk.Style(self)
        style.theme_use("clam")
        muted = "#aeb8c4" if dark else "#687586"
        accent = "#527ca3" if dark else "#3978b8"
        accent_active = "#648fb6" if dark else "#2f699f"
        border = "#3a434e" if dark else "#d9e0e8"
        danger = "#ff9189" if dark else "#b42318"
        style.configure(".", background=background, foreground=foreground)
        style.configure("TFrame", background=background)
        style.configure("TLabel", background=background, foreground=foreground)
        style.configure("TLabelframe", background=background, foreground=foreground,
                        bordercolor=border, relief="solid")
        style.configure("TLabelframe.Label", background=background, foreground=foreground)
        style.configure("TButton", background=button, foreground=foreground, padding=(9, 6), borderwidth=0)
        style.map("TButton", background=[("active", active)])
        style.configure("Accent.TButton", background=accent, foreground="#ffffff", padding=(14, 7),
                        borderwidth=0, font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", accent_active), ("disabled", button)],
                  foreground=[("disabled", muted)])
        style.configure("TEntry", fieldbackground=field, foreground=foreground,
                        bordercolor=border, lightcolor=border, darkcolor=border)
        style.configure("TCombobox", fieldbackground=field, background=button, foreground=foreground)
        style.map("TCombobox", fieldbackground=[("readonly", field)], foreground=[("readonly", foreground)])
        style.configure("TCheckbutton", background=background, foreground=foreground)
        style.configure("TPanedwindow", background=background)
        style.configure("Status.TLabel", background=background, foreground=muted, font=("Segoe UI", 9))
        style.configure("Counter.TLabel", background=background, foreground=muted, font=("Segoe UI", 9))
        style.configure("Counter.OverLimit.TLabel", background=background, foreground=danger,
                        font=("Segoe UI", 9, "bold"))
        legend_colors = (
            ("#94d2a7", "#24723e") if dark else ("#216b3a", "#216b3a"),
            ("#e4c66d", "#80651f") if dark else ("#82600a", "#82600a"),
            ("#e29a96", "#9f4541") if dark else ("#a33832", "#a33832"),
            ("#c6a27e", "#806346") if dark else ("#805c3d", "#805c3d"),
        )
        for rank, (dark_color, light_color) in enumerate(legend_colors):
            style.configure(f"Availability{rank}.TLabel",
                            foreground=dark_color if dark else light_color,
                            background=background, font=("Segoe UI", 8, "bold"))
        self.configure(background=background)
        self.apply_widget_theme(self)
        if hasattr(self, "profile_list"):
            self.refresh_profiles()
        self.update_draft_counters()
        self.refresh_toggle_labels()

    def toggle_ui_theme(self) -> None:
        self.ui_theme = "light" if self.ui_theme == "dark" else "dark"
        self.data["ui_theme"] = self.ui_theme
        self.apply_ui_theme()
        self.save_data()

    def toggle_ui_language(self) -> None:
        self.ui_language = "pt" if self.ui_language != "pt" else "en"
        self.data["ui_language"] = self.ui_language
        self.apply_ui_language()
        self.load_profile(self.current_index)
        self.refresh_profiles()
        self.save_data()

    def save_data(self) -> None:
        try:
            DATA_PATH.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as error:
            messagebox.showerror("Could not save", f"The planner could not save its local data:\n{error}")

    def close(self) -> None:
        self.save_data()
        self.destroy()

    def refresh_profiles(self) -> None:
        current_name = self.data["profiles"][self.current_index]["name"] if self.data["profiles"] else ""
        ordered_indices = sorted(
            range(len(self.data["profiles"])),
            key=lambda index: (
                self.availability_rank(self.data["profiles"][index]),
                self.data["profiles"][index]["name"].lower(),
            ),
        )
        ordered_profiles = [self.data["profiles"][index] for index in ordered_indices]
        visible_indexes = filter_profile_indices(ordered_profiles, self.community_search_var.get())
        self.profile_order = [ordered_indices[index] for index in visible_indexes]
        self.profile_list.delete(0, "end")
        selected_list_index: int | None = None
        dark = self.ui_theme == "dark"
        colors = (
            ("#284637", "#345743", "#4d3031", "#493c30")
            if dark else ("#e0f1e4", "#fff2cf", "#fae4e3", "#eee1d3")
        )
        foregrounds = ("#e5f3e9", "#fff2cf", "#fae4e3", "#f1e5d9") if dark else ("#214a2d", "#654d12", "#752d29", "#5e4934")
        for list_index, source_index in enumerate(self.profile_order):
            profile = self.data["profiles"][source_index]
            self.profile_list.insert("end", profile["name"])
            rank = self.availability_rank(profile)
            self.profile_list.itemconfig(list_index, background=colors[rank], foreground=foregrounds[rank])
            if profile["name"] == current_name:
                selected_list_index = list_index
        if selected_list_index is not None:
            self.profile_list.selection_set(selected_list_index)
            self.profile_list.see(selected_list_index)
        total_count = len(self.data["profiles"])
        visible_count = len(self.profile_order)
        if self.ui_language == "pt":
            self.community_count_var.set(f"{visible_count} de {total_count} comunidades")
        else:
            self.community_count_var.set(f"{visible_count} of {total_count} communities")
        self.update_repost_controls()

    def refresh_clock(self) -> None:
        """Repaint availability without asking the user to refresh the app."""
        self.refresh_profiles()
        self.update_status()
        self.validate()
        self.after(60_000, self.refresh_clock)

    def refresh_creators(self) -> None:
        names = [creator["name"] for creator in self.data["creator_profiles"]]
        self.creator_combo["values"] = names
        self.creator_index = min(self.creator_index, max(0, len(names) - 1))
        if names:
            self.creator_combo.current(self.creator_index)

    def on_creator_select(self, _event: Any) -> None:
        selected = self.creator_combo.current()
        if selected >= 0:
            self.creator_index = selected
            self.validate()

    def on_profile_select(self, _event: Any) -> None:
        selection = self.profile_list.curselection()
        if selection:
            self.load_profile(self.profile_order[selection[0]])

    def load_profile(self, index: int) -> None:
        if not self.data["profiles"]:
            return
        self.current_index = index
        profile = self.profile
        if not profile.get("rules", {}).get("promotion_allowed", True):
            self.post_type_var.set("Artwork / OC")
            self.include_price_var.set(False)
        self.community_heading.config(text=profile["name"])
        folder = profile.get("folder", "")
        folder_label = "Pasta de imagens" if self.ui_language == "pt" else "Image folder"
        not_configured = "Não configurada" if self.ui_language == "pt" else "Not configured"
        self.folder_label.config(text=f"{folder_label}: {folder or not_configured}")
        self.notes_label.config(text=profile["rules"].get("notes", "No notes added."))
        self.configure_title_tag_control()
        self.configure_price_control()
        self.selected_images = []
        self.title_entry.delete(0, "end")
        self.body_text.delete("1.0", "end")
        self.load_images()
        self.update_status()
        self.update_repost_controls()
        self.validate()

    def configure_title_tag_control(self) -> None:
        if not self.profile.get("rules", {}).get("promotion_allowed", True):
            text = "Art post mode" if self.ui_language != "pt" else "Modo de postagem de arte"
            self.title_tag_var.set(False)
            self.title_tag_check.configure(text=text, state="disabled")
            return
        prefix = self.profile.get("rules", {}).get("title_prefix", "").strip()
        if not prefix:
            text = "Usar tag exigida" if self.ui_language == "pt" else "Use required title tag"
            self.title_tag_var.set(False)
            self.title_tag_check.configure(text=text, state="disabled")
            return
        label = "Usar tag" if self.ui_language == "pt" else "Use title tag"
        self.title_tag_var.set(True)
        self.title_tag_check.configure(text=f"{label}: {prefix}", state="normal")

    def configure_price_control(self) -> None:
        """Keep a required body price present before a commission draft is made."""
        requires_price = self.profile.get("rules", {}).get("require_price", False)
        promotion_allowed = self.profile.get("rules", {}).get("promotion_allowed", True)
        if requires_price and promotion_allowed:
            self.include_price_var.set(True)
            text = "Preço inicial exigido" if self.ui_language == "pt" else "Starting price required"
            self.include_price_check.configure(text=text, state="disabled")
        else:
            text = "Incluir preço inicial" if self.ui_language == "pt" else "Include starting price"
            self.include_price_check.configure(text=text, state="normal")

    def apply_title_tag(self, title: str) -> str:
        """Apply or remove the community-specific required tag at title start."""
        prefix = self.profile.get("rules", {}).get("title_prefix", "").strip()
        if not prefix:
            return title.strip()
        normalized_prefix = prefix.lower()
        clean = title.strip()
        if clean.lower().startswith(normalized_prefix):
            clean = clean[len(prefix):].lstrip()
        return f"{prefix} {clean}".strip() if self.title_tag_var.get() else clean

    def on_title_tag_toggle(self) -> None:
        current = self.title_entry.get().strip()
        if current:
            self.title_entry.delete(0, "end")
            self.title_entry.insert(0, self.apply_title_tag(current))
        self.validate()

    def load_images(self) -> None:
        self.image_list.delete(0, "end")
        self.clear_image_preview()
        folder_text = self.profile.get("folder", "")
        if not folder_text:
            self.image_list.insert("end", "Choose an image folder in Community settings.")
            return
        folder = Path(folder_text)
        if not folder.is_dir():
            self.image_list.insert("end", "Configured folder was not found.")
            return
        images = sorted(path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)
        if not images:
            self.image_list.insert("end", "No supported images in this folder.")
            return
        for image in images:
            self.image_list.insert("end", image.name)

    def image_paths(self) -> list[Path]:
        folder_text = self.profile.get("folder", "")
        folder = Path(folder_text)
        if not folder.is_dir():
            return []
        return sorted(path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)

    def on_image_select(self, _event: Any) -> None:
        selection = self.image_list.curselection()
        limit = self.image_limit()
        if len(selection) > limit:
            for index in selection[limit:]:
                self.image_list.selection_clear(index)
            selection = selection[:limit]
        paths = self.image_paths()
        self.selected_images = [paths[index] for index in selection if index < len(paths)]
        if self.selected_images:
            self.show_image_preview(self.selected_images[0])
        else:
            self.clear_image_preview()
        self.update_status()

    def image_limit(self) -> int:
        """Return the user-selected number of images, always constrained to 1–9."""
        try:
            return max(1, min(9, int(self.image_count_var.get())))
        except (tk.TclError, TypeError, ValueError):
            return 6

    def on_image_count_changed(self, _event: Any = None) -> None:
        """Persist the choice and trim an existing manual selection if needed."""
        limit = self.image_limit()
        self.image_count_var.set(limit)
        self.data["image_count"] = limit
        selection = self.image_list.curselection()
        if len(selection) > limit:
            for index in selection[limit:]:
                self.image_list.selection_clear(index)
            self.on_image_select(None)
        self.save_data()
        self.update_status()

    def clear_image_preview(self) -> None:
        """Remove the previous preview while keeping a clear empty state."""
        if not hasattr(self, "thumbnail_label"):
            return
        self.thumbnail_image = None
        self.thumbnail_label.configure(image="", text="Select an image to preview it.")
        self.thumbnail_name.configure(text="")

    def show_image_preview(self, path: Path) -> None:
        """Show a compact, read-only thumbnail for the first selected image."""
        try:
            with Image.open(path) as source:
                image = ImageOps.exif_transpose(source)
                resampling = getattr(Image, "Resampling", Image).LANCZOS
                image.thumbnail((190, 170), resampling)
                preview = ImageTk.PhotoImage(image.copy())
        except (OSError, ValueError, Image.DecompressionBombError):
            self.thumbnail_image = None
            self.thumbnail_label.configure(image="", text="Preview unavailable for this image.")
            self.thumbnail_name.configure(text=path.name)
            return
        self.thumbnail_image = preview  # Keep a reference so Tk does not discard it.
        self.thumbnail_label.configure(image=preview, text="")
        self.thumbnail_name.configure(text=path.name)

    def copy_selected_images(self, _event: Any = None) -> str:
        """Copy selected existing image files for a manual paste into a browser."""
        selection = self.image_list.curselection()
        paths = self.image_paths()
        selected = [paths[index] for index in selection[:self.image_limit()] if index < len(paths)]
        if not selected:
            messagebox.showinfo("Images not selected", "Select one or more images before copying them.", parent=self)
            return "break"
        try:
            copy_file_paths_to_clipboard(selected)
        except OSError as error:
            messagebox.showerror("Could not copy images", str(error), parent=self)
            return "break"
        self.selected_images = selected
        self.status_var.set(
            f"{len(selected)} image(s) copied. Use Ctrl+V in a compatible browser upload field."
        )
        return "break"

    def recently_used_images(self) -> set[str]:
        profile_name = self.profile["name"]
        cutoff = self.now_for(self.profile) - timedelta(hours=self.repost_interval_hours(self.profile))
        recent: set[str] = set()
        for entry in self.data["history"]:
            if entry.get("profile") != profile_name:
                continue
            try:
                created = datetime.fromisoformat(entry["created_at"])
            except (ValueError, KeyError):
                continue
            if created >= cutoff:
                for image in entry.get("images", [entry.get("image")]):
                    if image:
                        recent.add(image)
        return recent

    @staticmethod
    def now_for(profile: dict[str, Any]) -> datetime:
        # Keep the portable build dependency-free. Brasília currently uses UTC-3.
        # Other values deliberately use the local computer clock.
        if profile.get("timezone", "America/Sao_Paulo") == "America/Sao_Paulo":
            return datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=3)
        return datetime.now()

    def allowed_days(self, profile: dict[str, Any] | None = None) -> set[str]:
        selected = profile or self.profile
        values = {item.strip().title()[:3] for item in selected.get("preferred_days", "").split(",") if item.strip()}
        return values or set(DAYS)

    @staticmethod
    def parsed_times(profile: dict[str, Any], day: str | None = None) -> list[tuple[int, int]]:
        """Read a day's three suggested windows, with old schedules as fallback."""
        result: list[tuple[int, int]] = []
        weekly = profile.get("weekday_times", {})
        raw_times = weekly.get(day, "") if isinstance(weekly, dict) and day else ""
        if not raw_times:
            raw_times = profile.get("preferred_times", "")
        for value in raw_times.split(","):
            try:
                hour, minute = (int(part) for part in value.strip().split(":", 1))
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    result.append((hour, minute))
            except ValueError:
                continue
        return sorted(result)

    def last_posted_at(self, profile: dict[str, Any]) -> datetime | None:
        """Return the most recent locally recorded post for one community."""
        latest: datetime | None = None
        for entry in self.data["history"]:
            if entry.get("profile") != profile.get("name"):
                continue
            try:
                posted_at = datetime.fromisoformat(entry["created_at"])
            except (KeyError, TypeError, ValueError):
                continue
            if latest is None or posted_at > latest:
                latest = posted_at
        return latest

    @staticmethod
    def repost_interval_hours(profile: dict[str, Any]) -> float:
        """Return a rule interval or the local safety lock for unconfigured subs."""
        configured = float(profile.get("min_interval_hours", 0) or 0)
        return configured if configured > 0 else DEFAULT_LOCAL_POST_LOCK_HOURS

    def repost_lock_until(self, profile: dict[str, Any]) -> datetime | None:
        """Return the repost expiry, but only while the local interval is active."""
        last_posted = self.last_posted_at(profile)
        if last_posted is None:
            return None
        expiry = last_posted + timedelta(hours=self.repost_interval_hours(profile))
        return expiry if expiry > self.now_for(profile) else None

    def update_repost_controls(self) -> None:
        """Show the locally recorded posting lock without blocking draft work."""
        if not hasattr(self, "mark_posted_button"):
            return
        until = self.repost_lock_until(self.profile)
        locked = until is not None
        self.mark_posted_button.configure(state="disabled" if locked else "normal")
        if locked and until is not None:
            self.repost_notice_var.set(
                f"Local posting protection: do not publish in r/{self.profile['name']} until {until.strftime('%d %b, %H:%M')}. You can still prepare a new draft."
            )
        else:
            self.repost_notice_var.set("No local posting protection is active for this community.")

    def availability_rank(self, profile: dict[str, Any]) -> int:
        if self.repost_lock_until(profile) is not None:
            return 3
        now = self.now_for(profile)
        if DAYS[now.weekday()] not in self.allowed_days(profile):
            return 2
        times = self.parsed_times(profile, DAYS[now.weekday()])
        if not times:
            return 1
        before = timedelta(minutes=float(profile.get("time_before_minutes", 30)))
        after = timedelta(minutes=float(profile.get("time_after_minutes", 15)))
        for hour, minute in times:
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target - before <= now <= target + after:
                return 0
        return 1

    def availability_text(self) -> str:
        rank = self.availability_rank(self.profile)
        if rank == 3:
            until = self.repost_lock_until(self.profile)
            return f"Repost locked until {until.strftime('%d %b, %H:%M')}" if until else "Repost locked"
        return ["Good time to post", "Good day, wait for the preferred time", "Outside the preferred posting days"][rank]

    def format_link(self, key: str, value: str) -> str:
        label = SOCIAL_LABELS.get(key, key.title())
        if key == "discord" and not value.startswith("http"):
            return f"Discord: {value}"
        if self.link_style_var.get() == "Markdown":
            return f"[{label}]({value})"
        return f"{label}: {value}"

    def format_public_contact(self, key: str) -> str:
        """Render only the link, platform handle, or both selected by the artist."""
        label = SOCIAL_LABELS.get(key, key.title())
        link = self.creator.get("links", {}).get(key, "").strip()
        handle = self.creator.get("platform_handles", {}).get(key, "").strip().lstrip("@")
        choice = self.creator.get("link_display", {}).get(key, "Link")
        link_text = self.format_link(key, link) if link else ""
        handle_text = f"{label}: @{handle}" if handle else ""
        if choice == "@handle":
            return handle_text or link_text
        if choice == "Both":
            if link_text and handle:
                return f"{link_text} (@{handle})"
            return link_text or handle_text
        return link_text or handle_text

    def rendered_links(self) -> str:
        allowed = self.profile.get("link_order", [])
        portfolio_keys = ["vgen", "artstation", "behance", "cara", "website"]
        social_keys = ["instagram", "bluesky", "x", "linkedin", "twitch", "youtube", "kofi"]
        allowed_set = set(allowed)
        portfolio = [self.format_public_contact(key) for key in portfolio_keys if key in allowed_set and self.format_public_contact(key)]
        social = [self.format_public_contact(key) for key in social_keys if key in allowed_set and self.format_public_contact(key)]
        contact = [self.format_public_contact(key) for key in allowed if key not in set(portfolio_keys) | set(social_keys) and self.format_public_contact(key)]
        portuguese = self.profile["name"] == "LojaDeArte"
        sections = []
        if portfolio:
            sections.append(("Portfólio" if portuguese else "Portfolio") + ":\n" + "\n".join(portfolio))
        if social:
            sections.append(("Redes sociais" if portuguese else "Social") + ":\n" + "\n".join(social))
        if contact:
            sections.append(("Contato" if portuguese else "Contact") + ":\n" + "\n".join(contact))
        return "\n\n".join(sections)

    def render_template(self, text: str) -> str:
        creator = self.creator
        portuguese = self.profile["name"] == "LojaDeArte"
        payment_note = creator.get("payment_note_pt" if portuguese else "payment_note", "")
        contact_note = creator.get("contact_note_pt" if portuguese else "contact_note", "")
        reviews_note = creator.get("reviews_note", "").replace("{{reviews_link}}", creator.get("reviews_link", ""))
        mapping = {
            "{{handle}}": f"@{creator.get('handle', '')}" if creator.get("handle") else "",
            "{{artist_name}}": creator.get("artist_name") or creator.get("name", ""),
            "{{personal_price}}": f"${creator.get('personal_price', 0):g} USD",
            "{{commercial_price}}": f"${creator.get('commercial_price', 0):g} USD",
            "{{links}}": self.rendered_links(),
            "{{emoji}}": "✨" if creator.get("use_emojis") else "",
            "{{category}}": self.category_var.get(),
            "{{payment_note}}": payment_note,
            "{{contact_note}}": contact_note,
            "{{reviews_note}}": reviews_note,
            "{{reviews_link}}": creator.get("reviews_link", ""),
        }
        for token, replacement in mapping.items():
            text = text.replace(token, replacement)
            # Older generated options used one pair of braces because they
            # passed through an f-string. Support them as well, so saved
            # templates and a partially generated draft never show tokens.
            text = text.replace("{" + token[2:-2] + "}", replacement)
        return re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", text).strip()

    def category_options(self) -> tuple[list[str], list[str]]:
        category = self.category_var.get()
        directions = CATEGORY_DIRECTIONS.get(category, CATEGORY_DIRECTIONS["Anime"])
        handle = "{{handle}}"
        prefix = self.profile.get("rules", {}).get("title_prefix", "") if self.title_tag_var.get() else ""
        if self.profile["name"] == "LojaDeArte":
            titles = [f"Commissions de {category} abertas | {handle}" for _direction in directions]
            bodies = [
                f"Olá! Estou disponível para commissions de {category.lower()}. "
                "{{emoji}}\n\n{{price_block}}\n\n{{links}}"
                for _direction in directions
            ]
            return titles, bodies
        titles = [f"{prefix}{category}-style {direction} available | {handle}" for direction in directions]
        bodies = [
            f"Hi! I’m {{artist_name}}, a 2D illustrator available for {category.lower()} {direction}. "
            "{{emoji}}\n\n"
            "I can adapt the piece to your character, references, and the mood you want for the final illustration.\n\n"
            "{{price_block}}\n\n{{links}}\n\n{{payment_note}}\n\n{{contact_note}}"
            for direction in directions
        ]
        return titles, bodies

    def showcase_options(self) -> tuple[list[str], list[str]]:
        """Neutral art-sharing drafts for communities that are not ad boards."""
        category = self.category_var.get()
        name = self.profile["name"].lower()
        if name in {"dnd", "dungeonsanddragons"}:
            titles = [
                "[OC] [ART] {{category}} D&D character illustration",
                "[OC] [ART] A recent D&D character piece",
                "[OC] [ART] {{category}} adventurer illustration",
            ]
            bodies = [
                "Sharing a recent D&D character illustration. I focused on the character's identity, equipment, and the feeling of an adventure.",
                "A D&D character piece I recently finished. I would love to know which detail you notice first.",
                "My latest original D&D character artwork. Thanks for taking a look!",
            ]
            return titles, bodies
        return list(ART_SHOWCASE_TITLES), list(ART_SHOWCASE_BODIES)

    def prepare_draft(self) -> None:
        # Read the visible selector again. This prevents a stale creator index
        # from producing an empty links block after the user changes profiles.
        visible_creator = self.creator_combo.current()
        if visible_creator >= 0:
            self.creator_index = visible_creator
        profile = self.profile
        showcase_mode = not profile.get("rules", {}).get("promotion_allowed", True)
        if showcase_mode:
            self.post_type_var.set("Artwork / OC")
            self.include_price_var.set(False)
            self.title_tag_var.set(False)
            generated_titles, generated_bodies = self.showcase_options()
            title_choices = generated_titles
            body_choices = generated_bodies
        else:
            generated_titles, generated_bodies = self.category_options()
            title_choices = profile["titles"] + generated_titles
            # Communities with tailored templates use only those templates.
            # Other communities retain the editable category variations.
            body_choices = profile["bodies"] if profile["name"].lower() in COMMUNITY_BODY_TEMPLATES else profile["bodies"] + generated_bodies
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, self.apply_title_tag(self.render_template(random.choice(title_choices))))
        self.body_text.delete("1.0", "end")
        price_block = ""
        if not showcase_mode and self.include_price_var.get():
            price = self.creator.get("commercial_price", 0) if self.commercial_var.get() else self.creator.get("personal_price", 0)
            if self.profile["name"] == "LojaDeArte":
                price_block = f"Preço inicial: ${price:g} USD" if price else "Adicione seu preço inicial ou orçamento."
            else:
                price_block = f"Starting price: ${price:g} USD" if price else "Please add your starting price or budget."
        body = random.choice(body_choices)
        body = body.replace("{{price_block}}", price_block).replace("{price_block}", price_block)
        self.body_text.insert("1.0", self.render_template(body))
        paths = self.image_paths()
        if paths:
            unused = [path for path in paths if str(path) not in self.recently_used_images()]
            pool = unused or paths
            self.selected_images = random.sample(pool, k=min(self.image_limit(), len(pool)))
            try:
                self.image_list.selection_clear(0, "end")
                for path in self.selected_images:
                    image_index = paths.index(path)
                    self.image_list.selection_set(image_index)
                self.image_list.see(paths.index(self.selected_images[0]))
                self.show_image_preview(self.selected_images[0])
            except ValueError:
                pass
        else:
            self.selected_images = []
        self.update_status()
        self.validate()

    def next_allowed_time(self) -> datetime:
        last_post = self.last_posted_at(self.profile)
        earliest = self.now_for(self.profile) if last_post is None else last_post + timedelta(hours=self.repost_interval_hours(self.profile))
        allowed_days = self.allowed_days(self.profile)
        for offset in range(0, 8):
            candidate_day = (earliest + timedelta(days=offset)).date()
            weekday = DAYS[candidate_day.weekday()]
            if weekday not in allowed_days:
                continue
            time_values = self.parsed_times(self.profile, weekday)
            if not time_values:
                continue
            for hour, minute in time_values:
                candidate = datetime.combine(candidate_day, datetime.min.time()).replace(hour=hour, minute=minute)
                if candidate >= earliest:
                    return candidate
        return earliest

    def update_status(self) -> None:
        time_text = "now" if self.availability_rank(self.profile) == 0 else self.next_allowed_time().strftime("%d %b, %H:%M")
        image_text = f"{len(self.selected_images)} image(s) selected" if self.selected_images else "no image selected"
        self.status_var.set(f"{self.availability_text()}  |  Next allowed: {time_text}  |  {image_text}")

    def update_draft_counters(self) -> None:
        if not hasattr(self, "title_entry"):
            return
        title_length, remaining = title_character_count(self.title_entry.get().strip())
        self.title_count_var.set(f"{title_length} / {TITLE_CHARACTER_LIMIT}")
        self.title_count_label.configure(
            style="Counter.OverLimit.TLabel" if remaining < 0 else "Counter.TLabel"
        )
        body_length = len(self.body_text.get("1.0", "end").strip())
        unit = "caracteres" if self.ui_language == "pt" else "characters"
        self.body_count_var.set(f"{body_length} {unit}")

    def validate(self) -> None:
        profile = self.profile
        rules = profile["rules"]
        title = self.title_entry.get().strip()
        body = self.body_text.get("1.0", "end").strip()
        self.update_draft_counters()
        lowered_title = title.lower()
        lowered_body = body.lower()
        checks: list[tuple[str, str]] = []

        if not title:
            checks.append(("error", "Add a title."))
        elif len(title) > TITLE_CHARACTER_LIMIT:
            checks.append(("error", f"Title exceeds Reddit's {TITLE_CHARACTER_LIMIT}-character limit."))
        elif rules.get("require_handle") and "@" not in title:
            checks.append(("error", "Title needs an @handle for this community."))
        else:
            checks.append(("ok", "Title format is present."))

        for term in rules.get("banned_title_terms", []):
            if term.lower() in lowered_title:
                checks.append(("error", f"Title cannot include: {term}"))
        for term in rules.get("required_title_terms", []):
            if term.lower() not in lowered_title:
                checks.append(("error", f"Title needs: {term}"))
        any_terms = rules.get("required_title_any_terms", [])
        if any_terms and not any(term.lower() in lowered_title for term in any_terms):
            checks.append(("error", "Title needs one of: " + ", ".join(any_terms)))

        if self.post_type_var.get() == "For Hire" and not rules.get("promotion_allowed", True):
            checks.append(("error", "This community profile does not allow a commission advertisement. Use its community notes instead."))

        if self.post_type_var.get() in {"For Hire", "Hiring"} and rules.get("require_price"):
            prices = [float(value) for value in re.findall(r"(?:\$|USD\s*)(\d+(?:\.\d+)?)", body, re.IGNORECASE)]
            minimum = float(rules.get("minimum_commercial", 0) if self.commercial_var.get() else rules.get("minimum_personal", 0))
            if not prices:
                checks.append(("error", "Add a clear price or budget in USD."))
            elif minimum and max(prices) < minimum:
                kind = "commercial" if self.commercial_var.get() else "personal"
                checks.append(("error", f"{kind.title()} minimum is ${minimum:g} USD."))
            else:
                checks.append(("ok", "A price or budget was found."))

        if self.post_type_var.get() == "For Hire" and rules.get("require_portfolio"):
            portfolio_domains = ("vgen.co", "artstation.com", "cara.app", "behance.net")
            if not any(domain in lowered_body for domain in portfolio_domains) and "portfolio" not in lowered_body:
                checks.append(("error", "Add a direct public portfolio link."))
            else:
                checks.append(("ok", "Portfolio information was found."))

        if self.post_type_var.get() == "For Hire" and rules.get("require_social"):
            social_domains = ("instagram.com", "bsky.app", "bluesky", "x.com", "twitter.com")
            if not any(domain in lowered_body for domain in social_domains):
                checks.append(("error", "Add the required secondary social link."))
            else:
                checks.append(("ok", "Secondary social link was found."))

        for domain in rules.get("banned_domains", []):
            if domain.lower() in lowered_title or domain.lower() in lowered_body:
                checks.append(("error", f"This community does not allow {domain}."))
        for term in rules.get("required_body_terms", []):
            if term.lower() not in lowered_body:
                checks.append(("error", f"Post body needs: {term}"))

        if not self.selected_images:
            checks.append(("warning", "Select one or more images before you post."))
        elif any(str(path) in self.recently_used_images() for path in self.selected_images):
            checks.append(("warning", "At least one selected image was used in this community inside the configured interval."))
        else:
            checks.append(("ok", "Selected images were not used recently in this community."))

        allowed = self.next_allowed_time()
        lock_until = self.repost_lock_until(profile)
        if lock_until is not None:
            checks.append(("error", f"This community is locked until {lock_until.strftime('%d %b, %H:%M')} after the recorded post."))
        elif self.availability_rank(profile) == 0:
            checks.append(("ok", "The current suggested posting window is open."))
        elif allowed > self.now_for(self.profile):
            checks.append(("warning", f"Wait until {allowed.strftime('%d %b, %H:%M')} according to this profile."))
        else:
            checks.append(("ok", "The local interval allows a post now."))

        self.validation_text.config(state="normal")
        self.validation_text.delete("1.0", "end")
        for level, text in checks:
            prefix = {"ok": "✓", "error": "✕", "warning": "!"}[level]
            tag = {"ok": "good", "error": "bad", "warning": "warn"}[level]
            self.validation_text.insert("end", f"{prefix} {text}\n", tag)
        self.validation_text.tag_configure("good", foreground="#167a31")
        self.validation_text.tag_configure("bad", foreground="#b42318")
        self.validation_text.tag_configure("warn", foreground="#9a6700")
        self.validation_text.config(state="disabled")

    def copy_text(self, value: str, status: str) -> None:
        if not value:
            messagebox.showinfo("Nothing to copy", "Prepare or write a draft first.")
            return
        self.clipboard_clear()
        self.clipboard_append(value)
        self.status_var.set(status)

    def open_credits(self) -> None:
        """Open the project credit in the user's default browser."""
        webbrowser.open_new_tab(CREDITS_URL)

    def open_community(self) -> None:
        """Open the selected subreddit without signing in or publishing anything."""
        community = self.profile.get("name", "").strip()
        if not community:
            messagebox.showinfo("Community", "Choose a community first.", parent=self)
            return
        webbrowser.open_new_tab(f"https://www.reddit.com/r/{community}/")
        self.status_var.set(f"Opened r/{community} in your browser.")

    def open_folder(self) -> None:
        folder = Path(self.profile.get("folder", ""))
        if not folder.is_dir():
            messagebox.showinfo("Image folder", "Choose a valid image folder in Community settings.")
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except OSError as error:
            messagebox.showerror("Could not open folder", str(error), parent=self)

    def choose_image_folder(self) -> None:
        """Let the user choose a specific image folder from the main screen."""
        current = Path(self.profile.get("folder", ""))
        initial = current if current.is_dir() else application_dir()
        chosen = filedialog.askdirectory(
            parent=self,
            initialdir=str(initial),
            title=f"Choose the images for {self.profile['name']}",
        )
        if not chosen:
            return
        self.profile["folder"] = chosen
        self.save_data()
        self.load_profile(self.current_index)
        self.status_var.set("Image folder selected. Mark images in the list, then open the folder to copy or drag them.")

    def mark_posted(self) -> None:
        lock_until = self.repost_lock_until(self.profile)
        if lock_until is not None:
            messagebox.showinfo(
                "Repost locked",
                f"This community can be marked as posted again after {lock_until.strftime('%d %b, %H:%M')}.",
                parent=self,
            )
            return
        if not messagebox.askyesno(
            "Record post", "Record this as manually posted now? It will immediately place a local posting lock on this community."
        ):
            return
        self.data["history"].append(
            {
                "profile": self.profile["name"],
                "created_at": self.now_for(self.profile).isoformat(timespec="minutes"),
                "image": str(self.selected_images[0]) if self.selected_images else "",
                "images": [str(path) for path in self.selected_images],
                "title": self.title_entry.get().strip(),
            }
        )
        self.save_data()
        self.refresh_profiles()
        self.update_status()
        self.update_repost_controls()
        self.validate()
        until = self.repost_lock_until(self.profile)
        if until is not None:
            self.status_var.set(f"Post recorded locally. Do not publish in this community until {until.strftime('%d %b, %H:%M')}.")
        else:
            self.status_var.set("Post recorded locally. The local posting protection is active.")

    def add_profile(self) -> None:
        dialog = ProfileDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            self.data["profiles"].append(dialog.result)
            self.current_index = len(self.data["profiles"]) - 1
            self.refresh_profiles()
            self.load_profile(self.current_index)
            self.save_data()

    def edit_profile(self) -> None:
        dialog = ProfileDialog(self, self.profile)
        self.wait_window(dialog)
        if dialog.result:
            old_name = self.profile["name"]
            self.data["profiles"][self.current_index] = dialog.result
            if old_name != dialog.result["name"]:
                for entry in self.data["history"]:
                    if entry.get("profile") == old_name:
                        entry["profile"] = dialog.result["name"]
            self.refresh_profiles()
            self.load_profile(self.current_index)
            self.save_data()

    def remove_profile(self) -> None:
        if len(self.data["profiles"]) <= 1:
            messagebox.showinfo("Keep one community", "The planner needs at least one community profile.")
            return
        name = self.profile["name"]
        if not messagebox.askyesno("Remove community", f"Remove {name} from this local planner? Its post history will be kept."):
            return
        self.data["profiles"].pop(self.current_index)
        self.current_index = max(0, self.current_index - 1)
        self.refresh_profiles()
        self.load_profile(self.current_index)
        self.save_data()

    def export_profile(self) -> None:
        filename = filedialog.asksaveasfilename(
            title="Export community template", defaultextension=".json", filetypes=[("JSON template", "*.json")]
        )
        if not filename:
            return
        try:
            Path(filename).write_text(json.dumps(self.profile, ensure_ascii=False, indent=2), encoding="utf-8")
            self.status_var.set("Community template exported. It contains no images or post history.")
        except OSError as error:
            messagebox.showerror("Export failed", str(error))

    def import_profile(self) -> None:
        filename = filedialog.askopenfilename(title="Import community template", filetypes=[("JSON template", "*.json")])
        if not filename:
            return
        try:
            imported = json.loads(Path(filename).read_text(encoding="utf-8"))
            if not isinstance(imported, dict) or "name" not in imported or "rules" not in imported:
                raise ValueError("This is not a valid community template.")
            imported.setdefault("folder", "")
            imported.setdefault("min_interval_hours", 48)
            imported.setdefault("preferred_times", "")
            imported.setdefault("titles", [])
            imported.setdefault("bodies", [])
        except (OSError, ValueError, json.JSONDecodeError) as error:
            messagebox.showerror("Import failed", str(error))
            return
        existing = {profile["name"].lower() for profile in self.data["profiles"]}
        original = imported["name"]
        count = 2
        while imported["name"].lower() in existing:
            imported["name"] = f"{original} ({count})"
            count += 1
        self.data["profiles"].append(imported)
        self.current_index = len(self.data["profiles"]) - 1
        self.refresh_profiles()
        self.load_profile(self.current_index)
        self.save_data()

    def save_community_settings(self) -> None:
        self.save_data()
        self.status_var.set("Community settings saved locally.")

    def copy_community_settings(self) -> None:
        if len(self.data["profiles"]) < 2:
            messagebox.showinfo("Copy settings", "Add another community first.")
            return
        targets = [profile["name"] for index, profile in enumerate(self.data["profiles"]) if index != self.current_index]
        dialog = tk.Toplevel(self)
        dialog.title("Copy community settings")
        dialog.transient(self)
        dialog.grab_set()
        ttk.Label(dialog, text="Copy rules, timing and allowed-link order to:", padding=12).pack(anchor="w")
        picker = ttk.Combobox(dialog, values=targets, state="readonly")
        picker.pack(fill="x", padx=12)
        picker.current(0)
        def copy() -> None:
            target_name = picker.get()
            target_index = next(index for index, profile in enumerate(self.data["profiles"]) if profile["name"] == target_name)
            source = self.profile
            target = self.data["profiles"][target_index]
            for key in ("min_interval_hours", "preferred_times", "weekday_times", "preferred_days", "time_before_minutes", "time_after_minutes", "link_order", "rules"):
                target[key] = json.loads(json.dumps(source[key]))
            self.save_data()
            dialog.destroy()
            self.status_var.set(f"Settings copied to {target_name}. Its folder and draft library were kept unchanged.")
        buttons = ttk.Frame(dialog, padding=12)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Cancel", command=dialog.destroy).pack(side="right")
        ttk.Button(buttons, text="Copy", command=copy).pack(side="right", padx=(0, 8))

    def add_creator(self) -> None:
        dialog = CreatorDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            self.data["creator_profiles"].append(dialog.result)
            self.creator_index = len(self.data["creator_profiles"]) - 1
            self.refresh_creators()
            self.save_data()

    def edit_creator(self) -> None:
        dialog = CreatorDialog(self, self.creator)
        self.wait_window(dialog)
        if dialog.result:
            self.data["creator_profiles"][self.creator_index] = dialog.result
            self.refresh_creators()
            self.save_data()
            self.validate()

    def remove_creator(self) -> None:
        """Delete the selected creator profile only after explicit confirmation."""
        creator_name = self.creator.get("name") or "this profile"
        portuguese = self.ui_language == "pt"
        title = "Excluir perfil" if portuguese else "Remove profile"
        message = (
            f'Tem certeza de que deseja excluir o perfil "{creator_name}"?\n\n'
            "Essa ação remove os dados salvos desse perfil neste computador."
            if portuguese else
            f'Are you sure you want to remove the profile "{creator_name}"?\n\n'
            "This removes this profile’s saved data from this computer."
        )
        if not messagebox.askyesno(title, message, icon="warning", parent=self):
            return
        del self.data["creator_profiles"][self.creator_index]
        if not self.data["creator_profiles"]:
            # The app always keeps one usable blank profile for a new draft.
            self.data["creator_profiles"] = [default_data()["creator_profiles"][0]]
        self.creator_index = min(self.creator_index, len(self.data["creator_profiles"]) - 1)
        self.refresh_creators()
        self.save_data()
        self.validate()
        self.status_var.set("Profile removed. A blank profile is ready to edit." if not portuguese else "Perfil excluído. Um perfil em branco está pronto para editar.")

    def export_creator(self) -> None:
        filename = filedialog.asksaveasfilename(title="Export creator profile", defaultextension=".json", filetypes=[("JSON template", "*.json")])
        if not filename:
            return
        try:
            Path(filename).write_text(json.dumps(self.creator, ensure_ascii=False, indent=2), encoding="utf-8")
            self.status_var.set("Creator profile exported. It contains no artwork or posting history.")
        except OSError as error:
            messagebox.showerror("Export failed", str(error))

    def import_creator(self) -> None:
        filename = filedialog.askopenfilename(title="Import creator profile", filetypes=[("JSON template", "*.json")])
        if not filename:
            return
        try:
            creator = json.loads(Path(filename).read_text(encoding="utf-8"))
            if not isinstance(creator, dict) or not creator.get("name"):
                raise ValueError("This is not a valid creator profile.")
            creator.setdefault("handle", "")
            creator.setdefault("personal_price", 0)
            creator.setdefault("commercial_price", 0)
            creator.setdefault("use_emojis", False)
            creator.setdefault("links", {})
            creator.setdefault("platform_handles", {})
            creator.setdefault("link_display", {})
        except (OSError, ValueError, json.JSONDecodeError) as error:
            messagebox.showerror("Import failed", str(error))
            return
        self.data["creator_profiles"].append(creator)
        self.creator_index = len(self.data["creator_profiles"]) - 1
        self.refresh_creators()
        self.save_data()
        self.validate()


if __name__ == "__main__":
    PlannerApp().mainloop()
