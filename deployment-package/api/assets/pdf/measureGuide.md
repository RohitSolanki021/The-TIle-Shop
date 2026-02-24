# PRO Invoice Engine - Measurement Guide

## Page Dimensions
- Width: 595.5 pts (A4)
- Height: 842.25 pts (A4)
- Coordinate system: ReportLab (y=0 at bottom, y=842.25 at top)

## Template Text Positions (from pdfplumber analysis)

### Section Header Row ("MAIN FLOOR")
- Text at: x=266.2-326.8, y_rl=588.9
- Box to cover: x=250, y=586, w=95, h=14

### Section Total Row ("MAIN FLOOR's Total Amount")  
- Label at: x=414.4-519.6, y_rl=498.2
- Label box: x=400, y=498, w=125, h=12
- Value box: x=527, y=498, w=45, h=12

### Table Column Boundaries
| Column    | x0    | x1    | Width | Align  |
|-----------|-------|-------|-------|--------|
| SR NO     | 28    | 52    | 24    | center |
| NAME      | 52    | 99    | 47    | left   |
| IMAGE     | 99    | 169   | 70    | center |
| SIZE      | 169   | 382   | 213   | center |
| RATE/BOX  | 382   | 414   | 32    | right  |
| RATE/SQFT | 414   | 442   | 28    | right  |
| QUANTITY  | 442   | 487   | 45    | center |
| DISC      | 487   | 527   | 40    | center |
| AMOUNT    | 527   | 566   | 39    | right  |

### Row Heights
- Standard row: 18 pts
- Row with image: 40 pts

### Safe Areas (Page 1)
- startY: 570 (below table headers)
- endY: 510 (above section total row)
- safeBottomY: 80 (absolute minimum)

### Safe Areas (Continuation)
- startY: 730
- safeBottomY: 80

## Conversion Formulas
- pdfplumber y_top to ReportLab y: `y_rl = 842.25 - y_top - height`
- Box placement: always use ReportLab y (from bottom)
