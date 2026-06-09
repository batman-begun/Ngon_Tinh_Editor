from dataclasses import dataclass, field


@dataclass
class MemoryStore:
    names: dict[str, str] = field(default_factory=dict)
    pronouns: list[dict[str, str]] = field(default_factory=list)
    terms: dict[str, str] = field(default_factory=dict)
    social_titles: dict[str, str] = field(default_factory=dict)

    def to_prompt(self) -> str:
        return (
            f"Tên riêng: {self.names}\n"
            f"Xưng hô: {self.pronouns}\n"
            f"Thuật ngữ: {self.terms}\n"
            f"Chức vụ/vai vế: {self.social_titles}"
        )

    def to_dict(self) -> dict:
        return {
            "names": self.names,
            "pronouns": self.pronouns,
            "terms": self.terms,
            "social_titles": self.social_titles,
        }
