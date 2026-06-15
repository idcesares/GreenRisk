"""GreenRisk fuzzy linguistic variables.

Five variables: four inputs on [0, 1] (specificity, commitment,
sentiment_asymmetry, netzero) plus the risk output on [0, 100].
Breakpoints follow a theory-driven design, symmetric around the models'
0.5 calibration midpoint.

Importing this module constructs the variables but has NO side effects
(no plots, no prints). Visualization lives in a separate script.
"""

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# --- Universes of discourse ------------------------------------------------
universe_input = np.arange(0, 1.01, 0.01)    # the four inputs
universe_output = np.arange(0, 100.1, 0.1)   # risk

# --- Input antecedents -----------------------------------------------------
specificity         = ctrl.Antecedent(universe_input, "specificity")
commitment          = ctrl.Antecedent(universe_input, "commitment")
sentiment_asymmetry = ctrl.Antecedent(universe_input, "sentiment_asymmetry")
netzero             = ctrl.Antecedent(universe_input, "netzero")

INPUTS = [specificity, commitment, sentiment_asymmetry, netzero]

# --- Output consequent -----------------------------------------------------
risk = ctrl.Consequent(universe_output, "risk")

# --- Triangular membership functions for the inputs ------------------------
# All four inputs share identical MF geometry:
#   Low    shoulder anchored at the left edge   (0,   0,   0.4)
#   Medium standard triangle centered at 0.5    (0.2, 0.5, 0.8)
#   High   shoulder anchored at the right edge  (0.6, 1,   1)
for var in INPUTS:
    var["Low"]    = fuzz.trimf(var.universe, [0,   0,   0.4])
    var["Medium"] = fuzz.trimf(var.universe, [0.2, 0.5, 0.8])
    var["High"]   = fuzz.trimf(var.universe, [0.6, 1,   1])

# --- Triangular membership functions for the output ------------------------
# Four terms for extra resolution at the output.
risk["Low"]      = fuzz.trimf(risk.universe, [0,   0,   30])
risk["Moderate"] = fuzz.trimf(risk.universe, [15,  35,  55])
risk["Elevated"] = fuzz.trimf(risk.universe, [45,  65,  85])
risk["High"]     = fuzz.trimf(risk.universe, [70,  100, 100])

# --- Trapezoidal variant of specificity ------------------------------------
# Isolated from the main pipeline; swapped in only for a triangular-vs-
# trapezoidal comparison. The Low MF gains a plateau on [0, 0.15] --
# "everything from 0 to 0.15 is unambiguously Low". Medium and High keep
# their triangular shapes, so only the Low MF varies.
specificity_trap = ctrl.Antecedent(universe_input, "specificity_trap")
specificity_trap["Low"]    = fuzz.trapmf(specificity_trap.universe, [0, 0, 0.15, 0.4])
specificity_trap["Medium"] = fuzz.trimf(specificity_trap.universe, [0.2, 0.5, 0.8])
specificity_trap["High"]   = fuzz.trimf(specificity_trap.universe, [0.6, 1, 1])