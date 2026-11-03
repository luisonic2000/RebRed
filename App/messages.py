"""Portuguese translations for live draft checks and workspace controls."""
import re

PT = {
    "Manage communities": "Gerenciar comunidades",
    "Prepare your next post": "Prepare sua próxima publicação",
    "Your draft": "Seu rascunho",
    "Choose images": "Escolher imagens",
    "Drag to reorder or send files": "Arraste para organizar ou enviar arquivos",
    "View details": "Ver detalhes",
    "Choose a folder and prepare a draft to select images.": "Escolha uma pasta e prepare um rascunho para selecionar imagens.",
    "Title copied.": "Título copiado.",
    "Body copied.": "Texto copiado.",
    "Do not put contact details or links in this title.": "Não inclua contatos ou links neste título.",
    "Paid offers are only allowed on weekends in this community.": "Ofertas pagas só são permitidas nos fins de semana nesta comunidade.",
    "DnD Thursdays are text-only using Eastern US timing. Confirm image posting is open.": "Às quintas, o DnD aceita apenas texto, seguindo o horário do leste dos EUA. Confira se imagens estão liberadas.",
    "Undo last publication": "Desfazer última publicação",
    "Restore layout": "Restaurar layout",
    "Customize draft": "Personalizar rascunho",
    "Official rules URL": "Endereço das regras oficiais",
    "Verification status": "Estado da verificação",
    "Add a title.": "Adicione um título.",
    "Title needs an @handle for this community.": "O título precisa do seu @arroba nesta comunidade.",
    "Title format is present.": "O título foi preenchido.",
    "Add a clear price or budget in USD.": "Informe um preço ou orçamento claro em USD.",
    "A price or budget was found.": "Preço ou orçamento encontrado.",
    "Add a direct public portfolio link.": "Adicione um link direto de portfólio público.",
    "Portfolio information was found.": "Informações de portfólio encontradas.",
    "Add the required secondary social link.": "Adicione o link de rede social secundária exigido.",
    "Secondary social link was found.": "Link de rede social secundária encontrado.",
    "Select one or more images before you post.": "Selecione uma ou mais imagens antes de publicar.",
    "Community rules need review. Check the official rules before posting.": "As regras precisam de revisão. Confira a fonte oficial antes de publicar.",
    "The current suggested posting window is open.": "Você está na janela de horário recomendada.",
    "The local interval allows a post now.": "O intervalo local já permite publicar.",
    "Selected images were not used recently in this community.": "As imagens selecionadas não foram usadas recentemente nesta comunidade.",
    "At least one selected image was used in this community inside the configured interval.": "Uma das imagens foi usada nesta comunidade dentro do intervalo configurado.",
    "This community profile does not allow a commission advertisement. Use its community notes instead.": "Este perfil não permite anúncio de commissions. Consulte as notas da comunidade.",
}
PREFIXES = {
    "Fill template fields: ": "Preencha os campos do modelo: ",
    "Title cannot include: ": "O título não pode conter: ",
    "Title needs: ": "O título precisa conter: ",
    "Title needs one of: ": "O título precisa de uma das opções: ",
    "Post body needs: ": "O corpo precisa conter: ",
}


def translate_check(text, language):
    if language != "pt":
        return text
    if text in PT:
        return PT[text]
    patterns = [
        (r"Body needs at least (\d+) characters describing your artwork\.", r"O corpo precisa de pelo menos \1 caracteres descrevendo sua arte."),
        (r"Title exceeds Reddit's (\d+)-character limit\.", r"O título ultrapassa o limite de \1 caracteres do Reddit."),
        (r"Personal minimum is \$(.+) USD\.", r"O preço pessoal mínimo é US$ \1."),
        (r"Commercial minimum is \$(.+) USD\.", r"O preço comercial mínimo é US$ \1."),
        (r"This community does not allow (.+)\.", r"Esta comunidade não permite \1."),
        (r"This community is locked until (.+) after the recorded post\.", r"Esta comunidade está bloqueada até \1 após a publicação registrada."),
        (r"Wait until (.+) according to this profile\.", r"Próximo horário estimado: \1. Isso não é um bloqueio obrigatório."),
    ]
    for pattern, replacement in patterns:
        if re.fullmatch(pattern, text):
            return re.sub(pattern, replacement, text)
    for prefix, translated in PREFIXES.items():
        if text.startswith(prefix):
            return translated + text[len(prefix):]
    return text
