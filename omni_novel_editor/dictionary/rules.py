import csv
import re
from dataclasses import dataclass
from functools import lru_cache
from io import StringIO


@dataclass(frozen=True)
class DictionaryRule:
    source: str
    target: str
    ambiguous_targets: tuple[str, ...] = ()

    @property
    def is_ambiguous(self) -> bool:
        return bool(self.ambiguous_targets)


# Dictionary hậu kiểm mặc định do user cung cấp. Giữ ở dạng data trong code để app
# luôn có rule thô trước/sau LLM, không phụ thuộc file upload bên ngoài.
BUILTIN_RULE_ROWS: tuple[tuple[str, str], ...] = (
    ("Doyin", "đưu dinh"),
    ("gặp fan offline", "gặp phan trực tiếp"),
    ("DV", "đi vi"),
    ("máy POS", "Máy cà thẻ"),
    ("Tiramisu", "Ti ra mi su"),
    ("RollsRoyce", "Ron roi"),
    ("Ferrari", "Phe ra rì"),
    ("view", "viu"),
    ("sandwich", "xen quích"),
    ("cello", "xê lô"),
    ("blogger", "lốc gơ"),
    ("Team building", "xây dựng đội nhóm"),
    ("Myanmar", "Đất nước của những ngôi chùa"),
    ("milimet", "mi li mét"),
    ("centimet", "xen ti mét"),
    ("robot", "rô bốt"),
    ("AI", "Ây ai"),
    ("titan", "ti tan"),
    ("Streamer", "Người phát sóng trực tuyến"),
    ("axit", "a xít"),
    ("Hồng Kông", "Hương Cảng"),
    ("Thái Lan", "xứ sở Chùa Vàng"),
    ("iPhone", "ai phôn"),
    ("internet", "in tơ nét"),
    ("neon", "nê ông"),
    ("show", "chương trình"),
    ("filter", "lọc"),
    ("catwalk", "sàn diễn thời trang"),
    ("ma túy", "chất bột trắng"),
    ("gian phu dâm phụ", "Đôi nam nữ không biết liêm sỉ"),
    ("dâm phụ", "người đàn bà lẳng lơ"),
    ("Đồ đĩ", "lẳng lơ"),
    ("cắt cổ tay/ rạch cổ tay", "tự làm mình bị thương"),
    ("dâm đãng", "háo sắc"),
    ("mại dâm", "gái bán hoa"),
    ("treo cổ", "quyên sinh"),
    ("tự sát/ tự tử/ tự vẫn", "quyên sinh"),
    ("tù/ ngồi tù", "đi tò"),
    ("nhảy lầu", "nhảy từ tầng cao xuống"),
    ("USB", "thẻ nhớ / bộ nhớ ngoài"),
    ("sedan", "xê đan"),
    ("visa", "vi gia"),
    ("Paparazzi", "thợ săn ảnh"),
    ("online", "trực tuyến"),
    ("champagne", "rượu sâm panh"),
    ("showbiz", "giới giải trí"),
    ("IQ", "chỉ số thông minh"),
    ("EQ", "chỉ số cảm xúc"),
    ("virus", "vi rút"),
    ("silicon", "xi li con"),
    ("parabol", "ba ra bon"),
    ("livestream", "phát sóng trực tiếp"),
    ("bikini", "bi ki ni"),
    ("vest", "âu phục"),
    ("disco", "đích cô"),
    ("Camera", "ca mê ra"),
    ("bánh mouse", "bánh kem xốp"),
    ("hack", "hắc"),
    ("bar", "quán rượu"),
    ("antiphan", "an ti phan"),
    ("bom", "bôm"),
    ("spam", "gửi thư rác"),
    ("top", "tốp"),
    ("logic", "lý luận"),
    ("album", "bộ sưu tập ảnh"),
    ("Mami/mami", "má mi"),
    ("drama", "đờ ra ma"),
    ("micro", "mích rô"),
    ("oxy", "ô xi"),
    ("husky", "hớt ki"),
    ("PR", "Pi a"),
    ("gen", "yếu tố di truyền"),
    ("IP", "ai pi"),
    ("email", "thư điện tử"),
    ("stylist", "nhà tạo mẫu"),
    ("ship", "đẩy thuyền"),
    ("scandal", "xì can đồ"),
    ("hacker", "hắc cơ"),
    ("fame", "phem"),
    ("bungee", "bân ghi"),
    ("Alaska", "A lát ca"),
    ("MC", "Em xi"),
    ("fanclub", "câu lạc bộ người hâm mộ"),
    ("Fan", "phan"),
    ("fandom", "Cộng đồng người hâm mộ"),
    ("Fan couple/ fan cp", "phan cặp đôi"),
    ("AIDS", "căn bệnh thế kỷ"),
    ("QQ", "khiu khiu"),
    ("photoshop", "chỉnh sửa ảnh"),
    ("mic", "mích"),
    ("album", "bộ sưu tập ảnh"),
    ("～", "."),
    ('"', ""),
    ("'", ""),
    (";", ","),
    ("…", "."),
    ("!!/!!!", "!"),
    ("???/??", "?"),
    ("?!", "?"),
    ("#", ""),
    (": .", "."),
    ("——", "."),
    ("【", ""),
    ("】", ""),
    ("[", ""),
    ("]", ""),
    ("(", ","),
    (")", ""),
    ("love", "tình yêu"),
    ("trai bao", "trai bán hoa"),
    ("Latin", "la tinh"),
    ("PK", "pi khây"),
    ("web", "quép"),
    ("QR", "khiu a"),
    ("CBD", "Xi bi đi"),
    ("%", "phần trăm"),
    ("game", "ghem"),
    ("code", "mã nguồn"),
    ("like", "gửi nút thích"),
    ("Ưm", "Ừm"),
    ("gara", "ga ra"),
    ("v.v.", "vân vân"),
    ("–", ","),
    ("Bentley", "ben lì"),
    ("Haizz/haizz/haiz", "hây"),
    ("hotboy", "hót boi"),
    ("WeChat", "Qui chát"),
    ("Huhu/ huhu", "Hu hu"),
    ("Idol", "ai đồ"),
    ("vị trí C", "vị trí trung tâm"),
    ("@", "a còng"),
    ("chat", "chát"),
    ("ADN", "ây đi en"),
    ("LCD", "eo xi đi"),
    ("iPad", "máy tính bảng"),
    ("Video", "vi đi ô"),
    ("hahaha", "ha ha ha"),
    ("haha", "ha ha"),
    ("carnival", "ca ni vô"),
    ("Bluetooth", "bờ lu tút"),
    ("guitar", "ghi ta"),
    ("jean", "ghin"),
    ("marketing", "ma két tinh"),
    ("Maybach", "mây bách"),
    ("Michelin", "mi chi lin"),
    ("nonono", "nô nô nô"),
    ("Parkinson", "Ba kin sân"),
    ("TV/ tivi", "ti vi"),
    ("hot", "hót"),
    ("CP", "xi pi"),
    ("beauty blogger", "lốc gơ làm đẹp"),
    ("blouse", "bờ lu"),
    ("buffet", "búp phê"),
    ("clip", "cờ líp"),
    ("coca", "cô ca"),
    ("glucose", "lu cô giơ"),
    ("marathon", "ma ra tông"),
    ("màu nude", "màu da"),
    ("ok", "ô kê"),
    ("alo", "a lô"),
    ("sandal", "xăng đan"),
    ("shipper", "người giao hàng"),
    ("sticker", "xì tích cơ"),
    ("sofa", "sô pha"),
    ("vali", "va li"),
    ("Yeah", "De"),
    ("chip", "chíp"),
    ("Weibo", "Quây bô"),
    ("hamster", "ham tơ"),
    ("jump", "Nhảy"),
    ("size", "cỡ"),
    ("suite", "phòng cao cấp"),
    ("cabin", "ca bin"),
    ("casting", "thử vai"),
    ("debut", "ra mắt"),
    ("flag", "mục tiêu"),
    ("flash", "Đèn chớp"),
    ("protein", "rồ tê in"),
    ("rock", "rốc"),
    ("hot search", "bảng tìm kiếm thịnh hành"),
    ("studio", "phòng thu"),
    ("taxi", "tắc xi"),
    ("vedette", "vơ đét"),
    ("VIP", "Vi ai pi"),
    ("adrenaline", "nội tiết tố sinh tồn"),
    ("gym", "dim"),
    ("nick", "ních"),
    ("piano", "pi a nô"),
    ("poster", "áp phích"),
    ("radar", "ra đa"),
    ("ship", "giao hàng"),
    ("trend", "xu hướng"),
    ("troll", "trôn"),
    ("wow", "Quao"),
    ("vitamin", "vi ta min"),
    ("baby", "bé bi"),
    ("slide", "xì lai"),
    ("comple", "Bộ đồ tây"),
    ("Pikachu", "Bi ca chu"),
    ("Stockholm", "Hội chứng con tin"),
    ("Sushi", "su si"),
    ("caramen", "ca ra men"),
    ("Cyberpunk", "Khoa học viễn tưởng phản địa đàng"),
    ("KPI", "khây pi ai"),
    ("CPU", "Xi pi diu"),
    ("Z", "Giét"),
    ("rap", "ráp"),
    ("Lego", "Lê gồ"),
    ("meme", "mê mê"),
    ("Trung Quốc", "Trung Hoa"),
    ("Êkíp", "Ê kíp"),
    ("Cứt", "Phân"),
    ("đụ má", "đờ mờ"),
    ("đĩ mẹ", "đờ mờ"),
    ("khốn nạn", "khốn nạn"),
)

_WORD_CHARS = r"A-Za-zÀ-ỹ0-9_"


def _split_sources(source: str) -> list[str]:
    parts = [part.strip() for part in source.split("/")]
    return [part for part in parts if part]


def _normalize_key(source: str) -> str:
    return re.sub(r"\s+", " ", source.strip()).casefold()


def _is_punctuation_rule(source: str) -> bool:
    return not any(char.isalnum() for char in source)


def _is_case_sensitive_acronym(source: str) -> bool:
    compact = re.sub(r"[^A-Za-z]", "", source)
    return bool(compact) and compact == compact.upper() and len(compact) <= 4


def _compile_pattern(source: str) -> re.Pattern[str]:
    escaped = re.escape(source.strip())
    if _is_punctuation_rule(source):
        return re.compile(escaped)
    flags = 0 if _is_case_sensitive_acronym(source) else re.IGNORECASE
    return re.compile(rf"(?<![{_WORD_CHARS}]){escaped}(?![{_WORD_CHARS}])", flags)


def _expand_rows(rows: list[tuple[str, str]] | tuple[tuple[str, str], ...]) -> list[tuple[str, str]]:
    expanded: list[tuple[str, str]] = []
    for source, target in rows:
        source = (source or "").strip()
        if not source:
            continue
        for part in _split_sources(source):
            expanded.append((part, target or ""))
    return expanded


def _build_rules(rows: list[tuple[str, str]] | tuple[tuple[str, str], ...]) -> list[DictionaryRule]:
    expanded = _expand_rows(rows)
    targets_by_source: dict[str, set[str]] = {}
    original_by_key: dict[str, str] = {}
    for source, target in expanded:
        key = _normalize_key(source)
        targets_by_source.setdefault(key, set()).add(target)
        original_by_key.setdefault(key, source)

    rules: list[DictionaryRule] = []
    for key, targets in targets_by_source.items():
        source = original_by_key[key]
        if len(targets) == 1:
            rules.append(DictionaryRule(source=source, target=next(iter(targets))))
        else:
            ordered_targets = tuple(sorted(targets))
            rules.append(DictionaryRule(source=source, target=" / ".join(ordered_targets), ambiguous_targets=ordered_targets))
    return sorted(rules, key=lambda rule: len(rule.source), reverse=True)


@lru_cache(maxsize=1)
def load_builtin_dictionary() -> tuple[DictionaryRule, ...]:
    return tuple(_build_rules(BUILTIN_RULE_ROWS))


def load_dictionary_csv(file_bytes: bytes) -> tuple[DictionaryRule, ...]:
    text = file_bytes.decode("utf-8-sig")
    rows: list[tuple[str, str]] = []
    reader = csv.reader(StringIO(text))
    for row_index, row in enumerate(reader, start=1):
        if not row or not any(cell.strip() for cell in row):
            continue
        if row_index == 1 and len(row) >= 2 and row[0].strip().casefold() in {"input", "source"}:
            continue
        if len(row) == 1:
            continue
        source = row[0].strip()
        target = ",".join(row[1:]).strip()
        if source:
            rows.append((source, target))
    return tuple(_build_rules(rows))


def apply_dictionary_rules(text: str, rules: tuple[DictionaryRule, ...] | list[DictionaryRule] | None = None) -> str:
    if not text:
        return ""
    result = text
    active_rules = rules if rules is not None else load_builtin_dictionary()
    for rule in active_rules:
        if rule.is_ambiguous:
            continue
        result = _compile_pattern(rule.source).sub(rule.target, result)
    return result


def find_relevant_rules(text: str, rules: tuple[DictionaryRule, ...] | list[DictionaryRule] | None = None) -> list[DictionaryRule]:
    if not text:
        return []
    active_rules = rules if rules is not None else load_builtin_dictionary()
    relevant: list[DictionaryRule] = []
    for rule in active_rules:
        if _compile_pattern(rule.source).search(text):
            relevant.append(rule)
    return relevant


def build_dictionary_prompt_block(text: str, rules: tuple[DictionaryRule, ...] | list[DictionaryRule] | None = None, limit: int = 40) -> str:
    relevant = find_relevant_rules(text, rules)
    if not relevant:
        return "Không có dictionary rule liên quan trong chunk này."

    deterministic = [rule for rule in relevant if not rule.is_ambiguous][:limit]
    ambiguous = [rule for rule in relevant if rule.is_ambiguous][:limit]
    lines: list[str] = []
    if deterministic:
        lines.append("DICTIONARY / GLOSSARY BẮT BUỘC:")
        lines.extend(f"- {rule.source} => {rule.target}" for rule in deterministic)
    if ambiguous:
        lines.append("TỪ ĐA NGHĨA CẦN CHỌN THEO NGỮ CẢNH:")
        lines.extend(f"- {rule.source} => {rule.target}" for rule in ambiguous)
    return "\n".join(lines)
