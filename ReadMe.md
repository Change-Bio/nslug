# nslug

Module for automating and simplifying cell transformation for bioreactor inoculation.

## Directories

- [slug_electroporator/](slug_electroporator/) — SolidWorks designs for the electroporator module (work in progress)
  - [sla_tests/](slug_electroporator/sla_tests/) — automated Python and PowerShell scripts for `.STL` generation from `.SLDPRT`
- [slug_pump_control/](slug_pump_control/) — Web-based peristaltic pump control system with live WebRTC video streaming (Raspberry Pi, React + Flask)
- [vision/](vision/) — Computer vision pipeline for slug detection using background subtraction and Kalman filtering
- [src/](src/) — Shared utilities (SolidWorks STL export scripts)