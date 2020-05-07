import glob
import os

import yaml

STATE_DATA = {}

for fname in glob.glob("absentee/templates/pdf/states/*.yml"):
    state, _ = os.path.splitext(os.path.basename(fname))
    with open(fname) as f:
        STATE_DATA[state.upper()] = yaml.safe_load(f)
