# Synthetic Crystal Plasticity Reading Note

This demo note is intentionally synthetic. It exists only to make the first
PaperLattice checkout runnable without distributing copyrighted papers.

The paper card describes a BCC ferritic steel study using crystal plasticity
finite element modeling to connect microstructure, slip resistance, and
macroscopic stress-strain response. The model family is a dislocation-density
based constitutive law. The key parameters include initial slip resistance,
forest hardening coefficient, recovery coefficient, and strain-rate sensitivity.

The validation target is a uniaxial tensile stress-strain curve combined with
texture evolution from EBSD. The main claim is that calibrated hardening
parameters can reproduce the early yield point and the subsequent work-hardening
slope when grain orientation statistics are represented by a realistic
polycrystal aggregate.

Important limitations are the simplified treatment of grain-boundary effects,
the absence of explicit damage evolution, and the risk that one calibrated
parameter set may not transfer across strain rates or heat treatments.

For a literature review, compare this model against phenomenological power-law
crystal plasticity and viscoplastic self-consistent approaches. Track which
papers report equations, parameter units, calibration targets, and validation
metrics. Mark claims as strong only when the evidence includes both global
stress-strain curves and local microstructure-sensitive validation.
