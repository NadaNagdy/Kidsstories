import hashlib
import json


class CharacterProfile:
    """
    Stores permanent character DNA extracted from photo analysis
    Ensures 100% visual consistency across pages
    """

    def __init__(self, name, gender, vision_description):
        self.name = name
        self.gender = gender
        self.vision_description = vision_description.strip()

        # Unique character ID (used for locking identity)
        self.character_id = self._generate_id()

    def _generate_id(self):
        base = f"{self.name}-{self.gender}-{self.vision_description}"
        return hashlib.md5(base.encode()).hexdigest()[:10]

    def get_locked_description(self):
        """
        Returns a STRICT locked character description
        """

        return f"""
CHARACTER ID: {self.character_id}

This is the SAME child in every page.

{self.vision_description}

CRITICAL CONSISTENCY RULES:
- Face shape must remain IDENTICAL
- Eye size and shape must remain IDENTICAL
- Hair color and texture must remain IDENTICAL
- Skin tone must remain IDENTICAL
- Do NOT modify facial structure
- Do NOT randomize features
- Do NOT change ethnicity
"""
