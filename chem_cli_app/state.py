import json
import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

@dataclass
class Step:
    command: str
    smiles_before: str
    smiles_after: str
    gatekeeper_log: List[str] = field(default_factory=list)
    quantities_snapshot: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class State:
    working_smiles: str = ""
    target_smiles: str = ""
    history: List[Step] = field(default_factory=list)
    redo_stack: List[Step] = field(default_factory=list)
    quantities: Dict = field(default_factory=dict)
    conditions: Dict = field(default_factory=lambda: {
        "temperature": None,
        "pH": None,
        "pressure": None,
        "solvent": None
    })
    session_file: Optional[str] = None

    def to_dict(self):
        data = asdict(self)
        # Handle the nested Step objects
        data['history'] = [step.to_dict() for step in self.history]
        data['redo_stack'] = [step.to_dict() for step in self.redo_stack]
        return data

    @classmethod
    def from_dict(cls, data):
        # Reconstruct the nested Step objects
        history = [Step.from_dict(step_data) for step_data in data.get('history', [])]
        redo_stack = [Step.from_dict(step_data) for step_data in data.get('redo_stack', [])]
        
        return cls(
            working_smiles=data.get('working_smiles', ""),
            target_smiles=data.get('target_smiles', ""),
            history=history,
            redo_stack=redo_stack,
            quantities=data.get('quantities', {}),
            conditions=data.get('conditions', {}),
            session_file=data.get('session_file')
        )

    def save_session(self, filename: Optional[str] = None) -> str:
        """Serializes the state to a JSON file."""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chem_session_{timestamp}.json"
        
        self.session_file = filename
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)
        return filename

    @classmethod
    def load_session(cls, filename: str):
        """Loads a session from a JSON file."""
        with open(filename, 'r') as f:
            data = json.load(f)
        state = cls.from_dict(data)
        state.session_file = filename
        return state