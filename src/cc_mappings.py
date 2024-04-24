from dataclasses import dataclass, field
from typing import List
from enum import Enum

class ControlChangeType(Enum):
  CONTINUOUS = "continuous"
  BOOLEAN = "boolean"
  CATEGORY = "category"

@dataclass
class CCOption:
  label: str
  value: int
  midi_value: int

@dataclass
class ControlChangeMapping:
  instrument: int
  number: int
  name: str
  type: ControlChangeType
  range: List[int] = field(default_factory=list)
  options: List[CCOption] = field(default_factory=list)

# Enums
class EQBand1CutoffFrequency(Enum):
  _16KHZ = 0
  _12KHZ = 42
  _8KHZ = 84
  
# Mappings
cc_mappings = [
  ControlChangeMapping(
    instrument=0,
    number=0,
    name="EQ Band 1 Cutoff Frequency",
    type=ControlChangeType.CATEGORY,
    options=[
      CCOption(label="16kHz",
               value=EQBand1CutoffFrequency._16KHZ,
               midi_value=EQBand1CutoffFrequency._16KHZ.value),
      CCOption(label="12kHz", 
               value=EQBand1CutoffFrequency._12KHZ,
               midi_value=EQBand1CutoffFrequency._12KHZ.value),
      CCOption(label="8kHz", 
               value=EQBand1CutoffFrequency._8KHZ,
               midi_value=EQBand1CutoffFrequency._8KHZ.value)
    ]
  ),
  ControlChangeMapping(
    instrument=0,
    number=1,
    name="EQ On/Off",
    type=ControlChangeType.BOOLEAN
  ),
  ControlChangeMapping(
    instrument=0,
    number=2,
    name="EQ Output volume",
    type=ControlChangeType.CONTINUOUS,
    range=[0, 127]
  )
  # Add more mappings as needed...
]
