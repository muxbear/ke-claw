from pathlib import Path
from typing import TypedDict

import yaml


class Skill(TypedDict):
    name: str
    description: str
    content: str


SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"


def get_all_skills() -> list[Skill]:
    """Load all skills from the skills directory.
    
    Each skill is a directory containing a SKILL.md file with YAML frontmatter.
    """
    skills: list[Skill] = []
    
    if not SKILLS_DIR.exists():
        return skills
    
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        
        try:
            content = skill_md.read_text(encoding="utf-8")
            
            # Parse YAML frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    body = parts[2].strip()
                    
                    skill: Skill = {
                        "name": frontmatter.get("name", skill_dir.name),
                        "description": frontmatter.get("description", ""),
                        "content": body,
                    }
                    skills.append(skill)
        except Exception:
            continue
    
    return skills


# Pre-load skills at module import
SKILLS: list[Skill] = get_all_skills()
