from dataclasses import dataclass

@dataclass 
class GeheimDienstAkte: 
    name: str
    dob: str 
    crimes: list[str]
    background: str
    employers: list[str]
    connections: list[str]
    genetic_augmentations: list[str]
    computer_brain_interfaces: list[str]
    illnesses: list[str]
    violence_potential: int
    estimated_wealth: int
    notes: str
