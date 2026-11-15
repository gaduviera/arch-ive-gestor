# Arch-Ive Phase 1 — Reports + Glassmorphism UI
## Design Specification

**Date:** 2025-04-15  
**Version:** 1.0  
**Status:** Approved for Implementation  
**Duration:** 4 weeks (Weeks 1-4)  
**Team Approach:** Codex (dense code) + GLM 5.1 (dense code) + Gemini (creative architecture)

---

## Executive Summary

Arch-Ive Phase 1 transforms the backup tool from a basic utility into an **analytics platform** with modern glassmorphism UI. We deliver:

1. **2 MVP Reports** (Weeks 3-4):
   - Daily Change Heatmap (file type × days matrix)
   - Backup Comparison Dashboard (side-by-side backup deltas)

2. **Glassmorphism UI System** (Weeks 1-2):
   - Frosted glass cards with simulated blur (PIL-based)
   - Premium buttons, inputs, charts with gradient + glow
   - Mesh/grain texture overlay (PNG asset, 15% opacity)
   - Expanded SYMETRA palette (carbon #111111 + gold #C6A85E + grays + success/warning)

3. **Export Formats**: PDF (visual), CSV (tabular), JSON (machine-readable)

---

## 1. Architecture

### 1.1 Directory Structure

```
arch-ive-gestor/
├── main.py                 # Entry point (unchanged)
├── ui.py                   # REFACTORED — Glassmorphism base
├── backup_engine.py        # Unchanged
├── duplicate_finder.py     # Unchanged
├── duplicates_tab.py       # Unchanged
├── config.py               # EXPANDED — report history path
│
├── NEW: reports_engine.py  # Data aggregation & calculations
├── NEW: reports_ui.py      # Heatmap + Comparison rendering
├── NEW: reports_tab.py     # Reports tab widget
│
├── NEW: theme.py           # Glassmorphism palette & utilities
├── NEW: components/        # Reusable UI components
│   ├── __init__.py
│   ├── frost_card.py       # FrostCard with PIL blur
│   ├── glass_button.py     # Glassmorphic buttons
│   ├── glass_input.py      # Glassmorphic input fields
│   └── chart_canvas.py     # Premium chart rendering
│
├── assets/
│   ├── mesh_grain.png      # Mesh texture (512x512, 15% opacity PNG)
│   └── icons.json          # Unicode icons + styling metadata
│
├── .claude/
│   └── launch.json         # Dev server config
│
└── docs/superpowers/specs/
    └── 2025-04-15-phase1-reports-ui-design.md (this file)
```

### 1.2 Module Responsibilities

| Module | Responsibility |
|--------|-----------------|
| `theme.py` | Color palette, texture loading, style utilities |
| `components/frost_card.py` | Canvas-based frosted card rendering |
| `components/glass_button.py` | Gradient buttons with hover/click states |
| `components/glass_input.py` | Input fields with glassmorphic borders |
| `components/chart_canvas.py` | Bar/line charts with premium styling |
| `reports_engine.py` | Data aggregation from backup history |
| `reports_ui.py` | Heatmap matrix + Comparison table rendering |
| `reports_tab.py` | Tab widget housing both reports |

---

## 2. Data Schema

### 2.1 Backup History Format

Each completed backup is logged to `config/backup_history.json` (append-only):

```json
{
  "backup_id": "bkp_20250415_143022",
  "date_created": "2025-04-15T14:30:22Z",
  "source_path": "C:\\Users\\Documents",
  "destination_path": "D:\\Backups",
  "total_files": 5200,
  "total_size_mb": 2500.5,
  "new_files": 150,
  "modified_files": 80,
  "deleted_files": 10,
  "duplicates_found": 250,
  "duplicates_size_mb": 150.3,
  "backup_duration_seconds": 3600,
  "status": "completed",
  "file_type_distribution": {
    ".doc": {"count": 1200, "size_mb": 800.2},
    ".iso": {"count": 50, "size_mb": 1000.5},
    ".jpg": {"count": 2000, "size_mb": 500.1},
    ".exe": {"count": 100, "size_mb": 150.0},
    ".other": {"count": 1850, "size_mb": 49.7}
  },
  "changes_by_date": {
    "2025-04-15": {
      ".doc": {"new": 10, "modified": 5, "deleted": 0, "size_delta_mb": 15.2},
      ".iso": {"new": 0, "modified": 1, "deleted": 0, "size_delta_mb": 2.1},
      ".jpg": {"new": 50, "modified": 10, "deleted": 2, "size_delta_mb": 25.0}
    }
  }
}
```

### 2.2 Aggregated Report Data (In-Memory Cache)

`reports_engine.py` computes and caches:

```python
{
  "date_range": ("2025-03-16", "2025-04-15"),  # Last 30 days
  "total_backups": 8,
  "heatmap_data": {
    # file_type -> [day1_count, day2_count, ...]
    ".doc": [15, 20, 18, 22, ...],
    ".iso": [2, 1, 3, 1, ...],
    ...
  },
  "comparison": {
    "backup_a_id": "bkp_20250401_120000",
    "backup_b_id": "bkp_20250415_143022",
    "metrics": {
      "total_files": {"a": 5000, "b": 5200, "delta": 200},
      "total_size_mb": {"a": 2300, "b": 2500.5, "delta": 200.5},
      "new_files": {"a": 140, "b": 150, "delta": 10},
      ...
    }
  }
}
```

---

## 3. Feature Specifications

### 3.1 Daily Change Heatmap

**Purpose:** Visual summary of file type changes over time.

**Data Input:**
- Last 30 days of backup history
- Aggregated by file type + date

**Rendering:**
- **Matrix Layout:** Y-axis = file types (up to 10 most common), X-axis = last 30 days
- **Cell Color:** Gradient from gold (#C6A85E) for high intensity → dark (#111111) for zero
- **Intensity Metric:** Sum of (new_files + modified_files) for that file type on that day
- **Cell Size:** ~40px × 40px each
- **Interactivity:** Hover → tooltip showing exact counts

**Tooltip Format:**
```
.doc | 2025-04-15
• New: 10 files
• Modified: 5 files
• Size delta: +15.2 MB
```

**Canvas Rendering (pseudo-code):**
```python
class HeatmapCanvas(tk.Canvas):
  def draw_heatmap(self, heatmap_data, file_types, dates):
    for i, file_type in enumerate(file_types):
      for j, date in enumerate(dates):
        intensity = heatmap_data[file_type][j]
        color = interpolate_color(gold, dark, intensity)
        self.create_rectangle(
          x + j*40, y + i*40, 
          x + (j+1)*40, y + (i+1)*40,
          fill=color, outline="#333333"
        )
        # Bind hover event for tooltip
```

**Export Formats:**
- **PDF:** Heatmap image + summary table below (top 5 file types)
- **CSV:** date | file_type | new_count | modified_count | size_delta_mb
- **JSON:** Structured heatmap_data + metadata

### 3.2 Backup Comparison Dashboard

**Purpose:** Side-by-side analysis of two backups to understand growth/changes.

**Inputs:**
- Backup A (date picker)
- Backup B (date picker, defaults to latest)

**Metrics Compared:**
1. Total Files (count)
2. Total Size (MB)
3. New Files (A → B)
4. Modified Files (A → B)
5. Deleted Files (A → B)
6. Duplicates Found (size MB)

**Visualization:**
- **Table Layout:** 3-column table
  - Column 1: "Backup A" (values)
  - Column 2: "Backup B" (values)
  - Column 3: "Δ (Delta)" (A - B, color-coded)
  
- **Color Coding:**
  - Positive delta (growth): gold (#C6A85E)
  - Negative delta (shrink): dark red (#8B0000)
  - Zero: gray (#555555)

- **Companion Chart:** Dual-bar chart below table
  - Bar 1: Total size of Backup A
  - Bar 2: Total size of Backup B
  - Difference highlighted in gold

**Table Example:**
```
Metric               | Backup A      | Backup B      | Δ
Total Files          | 5,000         | 5,200         | +200 (gold)
Total Size (MB)      | 2,300.0       | 2,500.5       | +200.5 (gold)
New Files            | -             | -             | +150 (gold)
Modified Files       | -             | -             | +80 (gold)
Deleted Files        | -             | -             | +10 (gold)
Duplicates (MB)      | 140.0         | 150.3         | +10.3 (gold)
```

**Export Formats:**
- **PDF:** 2 tables (A & B with metrics) + delta summary + dual-bar chart
- **CSV:** backup_name | metric | value_a | value_b | delta
- **JSON:** Nested structure with both backups + computed deltas

---

## 4. Glassmorphism UI System

### 4.1 Theme & Palette

**Primary Colors (SYMETRA):**
- Carbon Base: `#111111` (backgrounds)
- Carbon Elevated: `#1A1A1A` (cards, panels)
- Carbon Hover: `#222222` (hover states)
- Gold Primary: `#C6A85E` (accents, active borders)
- Gold Muted: `#8A6E35` (secondary states)
- Gold Subtle: `#C6A85E1A` (glassmorphism fills, ~10% opacity)

**Extended Palette:**
- Platinum: `#F5F5F5` (primary text)
- Silver: `#AAAAAA` (secondary text)
- Smoke: `#555555` (placeholders, disabled)
- Success: `#4CAF7D` (OK, positive trends)
- Warning: `#E8A838` (changes, alerts)
- Error: `#E57373` (failures, critical)
- Border Idle: `#333333` (neutral borders)
- Border Active: `#C6A85E` (focused/hover borders)

### 4.2 Component Library

#### 4.2.1 FrostCard
**Purpose:** Base container with frosted glass effect.

**Implementation:**
- Use PIL `ImageFilter.GaussianBlur(radius=15)` to blur background
- Overlay with `#1A1A1A` at 60% opacity
- Border: 1px `#C6A85E` at 40% opacity
- Rounded corners using Canvas arcs

**Code Structure:**
```python
class FrostCard(tk.Canvas):
  def __init__(self, parent, width, height, content_widget):
    super().__init__(parent, width=width, height=height, bg="#0D0D0D", highlightthickness=0)
    # Render blur background with PIL
    # Create content_widget inside
    # Bind geometry events to redraw
```

#### 4.2.2 Glass Button
**Purpose:** Glassmorphic buttons for primary/secondary actions.

**Styling:**
- Background: `#C6A85E` at 20% opacity
- Border: `#C6A85E` at 70% opacity (2px)
- Gradient fill: Two polygons from `#C6A85E1A` to `#C6A85E33`
- Text: `#F5F5F5` (medium weight)
- Hover: Border opacity → 100%, add outer halo 1px `#C6A85E`
- Click: Background → solid `#C6A85E` for 120ms, then revert

#### 4.2.3 Glass Input
**Purpose:** Text input fields with glassmorphism.

**Styling:**
- Background: `#1C1C1C`
- Text color: `#F5F5F5`
- Insert cursor: `#C6A85E`
- Border (idle): Canvas wrapper with `#C6A85E` at 30% opacity
- Border (focus): Canvas wrapper with `#C6A85E` at 80% opacity
- Placeholder: Custom class, text `#555555`, clears on focus

#### 4.2.4 Chart Canvas
**Purpose:** Premium charts for reports.

**Bar Chart Styling:**
- Background: `#0D0D0D`
- Grid lines: `#FFFFFF` at 5% opacity
- Bars: Gradient vertical (multiple 1px rectangles)
  - Top: `#C6A85E`
  - Bottom: `#6B5320`
- Bar shadow: `#C6A85E` at low alpha, 2px offset down
- Axis labels: `#AAAAAA`, font 10px

**Line Chart Styling:**
- Background: `#0D0D0D`
- Grid: `#FFFFFF` at 5% opacity
- Line: `#C6A85E`, width 2px, `smooth=True`
- Data points: 4px circles `#C6A85E` with 2px outer border `#111111`
- Tooltip: Canvas rect + text, appears on hover

### 4.3 Mesh/Grain Texture

**Asset:** `assets/mesh_grain.png` (512×512 PNG)
- Gaussian noise pattern rendered with PIL
- Opacity: 15% (alpha channel)
- Tiling: Repeat across canvas/window via Label overlay
- Placement: `place(x=0, y=0, relwidth=1, relheight=1)`, lowest layer

**Rendering:**
```python
# In ui.py main window init
texture_img = tk.PhotoImage(file="assets/mesh_grain.png")
texture_label = tk.Label(main_window, image=texture_img, bg="#111111")
texture_label.place(x=0, y=0, relwidth=1, relheight=1)
main_window.lower(texture_label)  # Send to background
```

---

## 5. Implementation Phases

### Phase 1A: UI Foundation (Weeks 1-2)

**Deliverables:**
1. `theme.py` — Complete palette + utilities
2. `components/frost_card.py` — FrostCard class
3. `components/glass_button.py` — Glass button class
4. `components/glass_input.py` — Glass input class
5. `components/chart_canvas.py` — Chart rendering utilities
6. Refactored `ui.py` — Apply glassmorphism theme to existing UI
7. `assets/mesh_grain.png` — Texture asset

**Acceptance Criteria:**
- All components render with glassmorphism styling
- Hover/focus states work (color changes, no animations needed)
- Mesh texture visible on background
- No UI regressions from original app

### Phase 1B: Reports Engine (Weeks 3-4)

**Deliverables:**
1. `reports_engine.py` — Backup history aggregation + data calculations
2. `reports_ui.py` — Heatmap + Comparison rendering
3. `reports_tab.py` — Reports tab widget
4. Export utilities — PDF, CSV, JSON generation
5. Integration — Hook reports_tab into main.py tabs

**Acceptance Criteria:**
- Heatmap renders correctly with color gradients
- Comparison dashboard shows accurate deltas
- Export generates valid PDF/CSV/JSON
- No performance regressions (< 2s to load reports)

---

## 6. Testing Strategy

### 6.1 Unit Tests

**`test_reports_engine.py`:**
- Aggregation logic (file type distribution, daily changes)
- Delta calculations (Backup A vs B)
- Edge cases (zero files, no changes, single backup)

**`test_theme.py`:**
- Color interpolation (gold → dark gradient)
- Palette defaults

### 6.2 Visual Tests

**`test_components_visual.py`:**
- Screenshot FrostCard (compare to golden image)
- Screenshot Glass Button (idle, hover, click states)
- Screenshot Heatmap (sample data)
- Screenshot Comparison Dashboard (sample backups)

### 6.3 Integration Tests

- Backup completion → history saved → reports load correctly
- Export formats generate valid files
- UI doesn't freeze during report rendering

**No tests needed for:**
- Robocopy integration (already tested in backup_engine)
- Tkinter event handling (framework responsibility)

---

## 7. Export Formats Specification

### 7.1 PDF Export

**Library:** `reportlab` (lightweight)

**Content:**
1. Header: "Arch-Ive Report" + date range
2. Heatmap visualization (PNG embedded)
3. Summary table (top 5 file types by size)
4. Page break
5. Comparison table (side-by-side)
6. Dual-bar chart

**Page Layout:** A4, margins 20mm

### 7.2 CSV Export

**Heatmap CSV:**
```
date,file_type,new_files,modified_files,deleted_files,size_delta_mb
2025-04-15,.doc,10,5,0,15.2
2025-04-15,.iso,0,1,0,2.1
...
```

**Comparison CSV:**
```
metric,backup_a_value,backup_b_value,delta
total_files,5000,5200,200
total_size_mb,2300.0,2500.5,200.5
...
```

### 7.3 JSON Export

```json
{
  "export_type": "heatmap",
  "date_range": ["2025-03-16", "2025-04-15"],
  "file_types": [".doc", ".iso", ".jpg", ...],
  "dates": ["2025-03-16", ..., "2025-04-15"],
  "heatmap_data": {
    ".doc": [15, 20, 18, ...],
    ".iso": [2, 1, 3, ...],
    ...
  },
  "summary": {
    "total_new_files": 4500,
    "total_modified_files": 2100,
    "largest_file_type_by_size": ".iso"
  }
}
```

---

## 8. Success Criteria

**Week 2 Checkpoint:**
- ✅ Glassmorphism components implemented + visually approved
- ✅ Main UI refactored (no regressions)
- ✅ Mesh texture visible

**Week 4 Deliverable:**
- ✅ Heatmap renders and matches spec
- ✅ Comparison dashboard shows accurate data
- ✅ All 3 export formats generate valid files
- ✅ Zero UI freezes during report generation
- ✅ Code is dense, well-commented (Codex/GLM style)

---

## 9. Technical Debt & Future

**Phase 2 Improvements (Not in Scope):**
- Timeline Navigator (calendar + slider)
- File Type Distribution (pie chart)
- Anomaly Detection (statistical)
- Custom Report Builder (wizard)

**Known Limitations (Phase 1):**
- No animations (tkinter limitations)
- Charts use Canvas (not matplotlib embedded — lighter)
- No real-time live updates
- Texture asset bundled (not procedural)

---

**END OF SPECIFICATION**

Status: Ready for implementation with Codex + GLM 5.1 + Gemini
