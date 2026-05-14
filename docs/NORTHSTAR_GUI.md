# ParakaleoMMC — North-Star GUI Design

A reference for the UI direction of ParakaleoMMC. Aspirational but achievable in Streamlit. Synthesizes BackpackEMR's "human-centered, low-clicks" philosophy, modern EMR usability research, iPad/tablet touch standards, and the user's explicit preference: **less blocky, less colorful, more professional**.

This is a design contract, not a code task list. Implementation phases at the bottom.

---

## 1. Core Design Principles

Three principles. Every design decision should be traceable to one of them.

### 1.1 Quiet by default
A clinic iPad isn't a marketing landing page. Whites, near-blacks, and a single accent color carry the load. Color is reserved for **clinical state** — urgent, waiting, ready, done — not decoration. The current app uses gradients, colored card backgrounds, and emoji-prefixed labels to signal importance; in a stressed clinical setting that becomes noise. Modern EMR research (Epic's philosophy, MEDITECH Expanse) converges on minimal chrome + clear data.

### 1.2 One screen, one patient
Mixing patient data is a clinical safety hazard, not an inconvenience. Best-practice EMR research is explicit: *put all information about a specific patient on one screen*. Patient name + ID is **always visible** in the chrome whenever the user is inside a patient. Switching patients is a deliberate act, never an accident.

### 1.3 Cut every tap that doesn't save a life
If a clinician does the same thing 99% of the time, that's the default. Don't ask. Pre-filled values are dangerous (e.g. defaulting vitals to "normal" — a clinical bug, not a UX one), but smart defaults (today's date, current clinic, the role you logged in as) are reductive in the right way. Confirmation dialogs only for **irreversible or cross-role** actions (graduate-from-family, delete patient, mark prescription dispensed). One percentage-point gain in EMR usability reduces physician burnout by 3% per the research.

---

## 2. Visual Language

### Typography

```
System font stack:
-apple-system, "SF Pro Text", "Segoe UI", Inter, system-ui, sans-serif
```

- Works **fully offline** (no Google Fonts CDN dependency).
- Native rendering on iPad Safari.
- Base **16 px**, line-height **1.5**.

| Use | Size | Weight |
|---|---|---|
| Display (page title) | 24 px | 600 |
| Heading | 20 px | 600 |
| Body | 16 px | 400 |
| Label | 14 px | 500 |
| Metadata | 14 px | 400, muted |
| Caption | 12 px | 400, muted |

No more than four sizes on any one screen. No italics. No underlines except hyperlinks (and there shouldn't be any of those in a working clinic page).

### Color palette

Five functional colors plus three neutrals. **That's it.**

| Token | Hex | Use |
|---|---|---|
| `surface` | `#FFFFFF` | Page background |
| `surface-2` | `#F9FAFB` | Subtle card background |
| `border` | `#E5E7EB` | Hairlines, dividers, input borders |
| `text` | `#111827` | Primary text |
| `text-muted` | `#6B7280` | Metadata, captions, disabled |
| `accent` | `#0F766E` | Brand, primary actions (deep teal — clinical, calm) |
| `urgent` | `#DC2626` | Critical / red flag |
| `waiting` | `#D97706` | In-progress, queued |
| `ready` | `#059669` | Completed, ready to advance |
| `idle` | `#9CA3AF` | Inactive, no-status |

**No gradients.** Not on cards, not on headers, not anywhere. Gradients read as decorative; this app isn't decorative.

**One shadow.** `0 1px 2px rgba(0,0,0,0.04)` on raised surfaces (modals, sticky bars). That's the entire shadow vocabulary.

### Spacing scale

Multiples of 4 px. Pick one for each gap; don't invent new ones.

```
4   8   12   16   24   32   48   64
```

Vertical rhythm between form fields: **24 px**. Between sections: **48 px**. Between rows in a list: **16 px**.

### Touch targets

- Minimum **56 px tall** for any tappable element (taller than Apple's 44 — tired clinic users + iPads in cases).
- Minimum **12 px gap** between adjacent buttons (touch research: <10 pt spacing increases errors by ~40%).
- Primary buttons span full content width on iPad portrait; pinned to content-width with min 200 px on landscape.

### Iconography

- **One icon set.** [Lucide](https://lucide.dev) (open source, ~1000 icons, single SVG file, ~70 KB total, works offline). Alternative: [Heroicons](https://heroicons.com).
- 20 px standard. 16 px in metadata. 24 px for prominent actions only.
- **Emoji is only allowed as a status indicator** (🔴 🟡 🟢) where the color *is* the meaning. No emoji in field labels, button text, or page titles. The current app's `👤 Name`, `🎂 Age`, `📱 Phone` pattern goes away.

---

## 3. Component Patterns

### 3.1 Patient row (the queue item)

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│ ▌ Carlos Martinez                                              │
│   DR00003  ·  42M  ·  Registered 2 min ago         [ Start → ] │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

- Hairline divider between rows; no card background, no shadow.
- Left edge: a **4 px vertical bar** in the row's status color (red for urgent, amber for waiting, green for returning-from-lab, gray for normal). This is the *only* color on the row.
- Single line of primary text: **name only**.
- Single line of metadata, dot-separated: `ID · age/sex · time | family`.
- **One** action button, right-aligned, outlined-style (not filled — filled buttons everywhere is a Streamlit-default footgun).
- Whole row is the tap target if the action is unambiguous.

### 3.2 Status pill

```
●  Urgent       ●  Waiting       ●  Ready       ●  Idle
```

- 8 px dot + label.
- **No filled background.** Filled "badges" are the source of half the app's blocky feel.
- 14 px text.

### 3.3 Form field

```
Blood pressure
[ 128 ]  /  [ 82 ]    ○ N/A           mmHg

Heart rate
[ 76 ]                ○ N/A           bpm
```

- Label above input (not inline) — touch ergonomics + accessibility.
- Unit on the right, muted.
- N/A is an explicit radio toggle next to the field, **not** "type N/A in the field" as the current app instructs.
- No placeholder text in the input itself once the user has focused once. Placeholders disappear when typing, so they can't be relied on as labels.

### 3.4 Section divider (instead of card)

```
Vitals
──────────────────────────────────────────────────────
```

- Section heading at 20 px / 600.
- Hairline rule below.
- 48 px below before content.

This replaces the current "colored gradient header bar + rounded box around the section" pattern. Same information hierarchy, a tenth of the visual noise.

### 3.5 Persistent top bar

```
─────────────────────────────────────────────────────────────────────
 🩺 ParakaleoMed  ·  San Pedro              Maria G. · Triage  EN  ● Sync  ⚙
─────────────────────────────────────────────────────────────────────
```

- 56 px tall, hairline border-bottom.
- Brand + current clinic on the left.
- Current user + current role + language + sync indicator + settings on the right.
- Always present once authenticated. We already have a v0 of this (`render_app_header`) — the real version replaces text "Change Role" with the gear icon and consolidates the language toggle.

### 3.6 Patient context strip (always-on when inside a patient)

```
─────────────────────────────────────────────────────────────────────
 ←  Carlos Martinez  ·  DR00003  ·  42M  ·  Family: Martinez
─────────────────────────────────────────────────────────────────────
```

- Sits directly below the top bar.
- Back chevron on the far left — **always clickable**, always returns to the queue you came from.
- Name + ID + brief demographics + family pill (if applicable).
- This is the answer to "one screen, one patient" — the user can never accidentally lose track of which patient they're charting.

### 3.7 Tab navigation (inside a patient detail)

```
   Demographics    Vitals    Labs    Meds    History
   ──────────                                          (underline = active)
```

- Text-only, no buttons-with-borders.
- Active = bold + bottom-border accent.
- Spaced 32 px apart.
- Horizontal scroll on portrait if it overflows; never wrap.

---

## 4. Page Layouts (ASCII mockups)

### 4.1 Triage Queue (the most-used screen)

```
═══════════════════════════════════════════════════════════════════════════════
 🩺 ParakaleoMed · San Pedro            Maria G. · Triage  EN  ● Sync  ⚙
═══════════════════════════════════════════════════════════════════════════════

 In clinic now   ● Dr. Ri (idle)        ● Dr. Si (with Carlos Martinez)

 Triage Queue                                  New Patient  ·  Search Patient
 ───────────────────────────────────────────────────────────────────────────

 8 patients waiting


 ▌ Carlos Martinez
   DR00003  ·  42M  ·  Registered 2 min ago               [ Start → ]

 ▌ Maria Martinez
   DR00004  ·  39F  ·  Family: Martinez                   [ Start → ]

 ▌ Diego Martinez
   DR00005  ·  8M   ·  Family: Martinez                   [ Start → ]

 ▌ Sofia Martinez
   DR00006  ·  14F  ·  Family: Martinez                   [ Start → ]

 ─── 4 more ───

═══════════════════════════════════════════════════════════════════════════════
```

### 4.2 Vitals entry

```
═══════════════════════════════════════════════════════════════════════════════
 🩺 ParakaleoMed · San Pedro            Maria G. · Triage  EN  ● Sync  ⚙
═══════════════════════════════════════════════════════════════════════════════
 ←  Carlos Martinez  ·  DR00003  ·  42M
─────────────────────────────────────────────────────────────────────────────

  Vital signs

  Blood pressure
  [ 128 ] / [ 82 ]              ○ N/A                              mmHg

  Heart rate
  [ 76 ]                        ○ N/A                              bpm

  Temperature
  [ 36.9 ]                      ○ N/A                              °C

  SpO₂
  [ 97 ]                        ○ N/A                              %

  Weight                                                Height
  [ 78 ]   kg                                           [ 175 ]   cm

                                              [ Save and continue → ]

═══════════════════════════════════════════════════════════════════════════════
```

Notes:
- No section headers within a single-purpose form. The page title is the section.
- Inputs are wide and obvious, not crammed into 4 narrow columns.
- N/A is an option, not a typed sentinel.
- One primary action, bottom-right, **after** all fields. (Streamlit-default `st.form_submit_button` is fine if styled.)
- No pre-filled normal values. Empty inputs.

### 4.3 Doctor consultation

```
═══════════════════════════════════════════════════════════════════════════════
 🩺 ParakaleoMed · San Pedro                Dr. Ri · Provider  EN  ● Sync  ⚙
═══════════════════════════════════════════════════════════════════════════════
 ←  Carlos Martinez  ·  DR00003  ·  42M  ·  Family: Martinez
─────────────────────────────────────────────────────────────────────────────

 Vitals at 09:42         BP 128/82      HR 76      Temp 36.9°C     SpO₂ 97%

   Visit · History · Family
 ───

 Chief complaint
 [_________________________________________________________________________]

 HPI
 [                                                                          ]
 [                                                                          ]

 Diagnosis                                                       [ + Add ]
 ▌ A09  Infectious gastroenteritis and colitis                          ✕

 Lab orders                                                      [ + Order ]
 ▌ Urinalysis                                                            ✕
 ▌ Glucose                                                               ✕

 Prescriptions                                                   [ + Add ]
 ▌ Amoxicillin 500 mg × 7 d                          ● Ready to dispense
 ▌ Metformin 500 mg BID                              ● Awaiting lab results

 ───────────────────────────────────────────────────────────────────────────

                          [ Send to lab ]   [ Send to pharmacy ]   [ Complete ]

═══════════════════════════════════════════════════════════════════════════════
```

Notes:
- Vitals shown as a single horizontal strip at the top (read-only) — no need to dig.
- Tabs (Visit · History · Family) let the doctor pivot to past visits and family context without leaving the patient.
- Diagnosis / Lab orders / Prescriptions are **flat lists with inline add**, not modals.
- The three terminal actions are visible from anywhere on the page (sticky if needed). The previously-removed "✍️ Consultation Sign-Off" framing is gone, but the actions remain — exactly as the user requested.

### 4.4 Patient history (longitudinal view)

```
═══════════════════════════════════════════════════════════════════════════════
 🩺 ParakaleoMed · San Pedro                Dr. Ri · Provider  EN  ● Sync  ⚙
═══════════════════════════════════════════════════════════════════════════════
 ←  Carlos Martinez  ·  DR00003  ·  42M  ·  Family: Martinez
─────────────────────────────────────────────────────────────────────────────

   Visit · History · Family
        ─────

 Visit timeline (6 visits across 3 clinics)

 ─── 2026-05-14 ─── San Pedro ─── Dr. Ri ────────────────────────────
   Diagnosis    Infectious gastroenteritis  (A09)
   Meds         Amoxicillin 500 mg × 7 d
   Labs         Urinalysis (neg)

 ─── 2025-11-12 ─── Santiago ─── Dr. Brown ──────────────────────────
   Diagnosis    Tension headache  (G44.2)
   Meds         Ibuprofen 400 mg PRN

 ─── 2025-03-08 ─── Santiago ─── Dr. Smith ──────────────────────────
   Diagnosis    Annual wellness — no acute findings


 Trends

 BP        125/80 ─ 128/82 ─ 130/85 ─ 128/82          [graph]
 Weight    75 kg ─ 76 kg ─ 78 kg ─ 78 kg              [graph]

═══════════════════════════════════════════════════════════════════════════════
```

Notes:
- Reverse chronological. Most recent visit at top.
- Each visit is one collapsible (?) block, expanded by default — but never an `<expander>` that hides the patient's whole life behind a chevron.
- Trends shown inline at the bottom: BP and weight at minimum. Other parameters add over time.

### 4.5 Login

```
═══════════════════════════════════════════════════════════════════════════════
                                                      EN  ·  Kreyòl  ·  Español
═══════════════════════════════════════════════════════════════════════════════



                          🩺  ParakaleoMed

                          Sign in to your clinic



                          Enter your name or PIN
                          ┌──────────────────────────┐
                          │                          │
                          └──────────────────────────┘

                          PIN
                          ┌──────────────────────────┐
                          │  • • • •                 │
                          └──────────────────────────┘

                          [        Sign in        ]


                          Administrator login →

═══════════════════════════════════════════════════════════════════════════════
```

Notes:
- Language picker top-right (already implemented).
- Generous vertical whitespace. Login is one of two screens a clinic volunteer sees most often (the other is the queue); it needs to be calming, not gradient-y.
- Admin login is a quiet text link, not an expander or gradient banner.
- Numeric PIN ideally pops the iPad numeric keypad (today's `type="password"` does not — separate fix).

---

## 5. What goes away

From the current app, removed in the north-star:

- All gradient banners (`linear-gradient(135deg, ...)`).
- Colored card backgrounds (light green `#f0fdf4`, light blue `#e0f2fe`, light orange `#fff3e0`).
- Box shadows on every card (`0 8px 32px rgba(...)`) — replaced with a single hairline border.
- 12 px / 15 px border radii — replaced with 4 px for inputs, 8 px for buttons, **never on whole-card surfaces**.
- Emoji prefix in labels (`👤 Name`, `🎂 Age`, `⚧ Gender`, `📱 Phone`).
- Hover transforms (`translateY(-2px)`) — invisible on touch, masks tap-and-hold.
- `time.sleep(2)` after success toasts — replaced with non-blocking toast that auto-dismisses.
- Streamlit sidebar as a primary navigation surface — replaced with the persistent top header.
- `st.expander` for primary content (default-collapsed expanders are landmines).
- Pre-filled "normal" vital signs (clinical safety issue, not just a UX one).
- The decorative ChatGPT-generated logo. A simple wordmark + stethoscope icon is plenty.

## 6. What stays / gets emphasized

- The patient queue as the central abstraction (BackpackEMR's strongest pattern — keep it).
- Role-based interfaces (intake / triage / provider / pharmacy / lab) — each tablet logged in as one role.
- Family grouping as a first-class concept (it's the operational reality of mobile clinics).
- Longitudinal patient records across clinics. The numbering system (country-prefix + sequence) supports this and stays.
- Lab-dependent prescription holding (`awaiting_lab` flag visible to pharmacy) — clinically critical, keep.
- Offline-first architecture. Nothing in this design depends on the network being up.

---

## 7. Implementation roll-out

Three phases, each independently shippable. **Each phase should be field-testable before starting the next.**

### Phase 1 — Design system foundation (1 day)

Goal: establish the visual vocabulary without redesigning a single page.

- Define design tokens as Python constants at the top of `app.py` (colors, spacing scale, typography).
- Create a single shared `<style>` block with the new CSS variables and a "reset" that overrides Streamlit defaults: remove default shadows, set border-radius, set base font.
- Replace the existing scattered inline `style="..."` attributes incrementally with utility classes that reference the tokens.
- Implement `status_pill(state, label)`, `patient_row(patient)`, `section_header(title)` helper functions.
- Strip the gradient banner CSS at app.py:4197+ and the per-section colored card CSS. Keep the markup, swap the styles.

**Acceptance:** the login page and the triage queue look quiet and consistent. No page has been "redesigned" yet; only the chrome and base styles have changed.

### Phase 2 — High-traffic pages (4 days, one per role)

Goal: redesign each role's primary screen using the components from Phase 1. Each day is independent and shippable.

1. **Day 1 — Triage queue + vitals entry.** Rebuild `triage_interface()` and `vital_signs_form()` against the new patterns. Strip pre-filled vitals.
2. **Day 2 — Doctor queue + consultation.** Rebuild `doctor_interface()`, `consultation_interface()`. Convert the "Real-Time Doctor Status" expander into a header strip. Sticky bottom action bar for the three terminal actions.
3. **Day 3 — Pharmacy queue + dispense.** Merge the 5 tabs of `pharmacy_interface()` into a dashboard with status counts. One unified queue with status pills instead of separate "Ready / Awaiting Lab / Awaiting Teaching" tabs.
4. **Day 4 — Lab queue + result entry.** Convert urinalysis from 11 dropdowns to a single segmented-button grid (Neg / Trace / 1+ / 2+ / 3+ / 4+) per analyte.

**Acceptance:** clinic-day rehearsal — a volunteer should be able to complete a full patient flow (intake → triage → provider → lab → pharmacy → discharge) without instruction beyond pointing at the iPad.

### Phase 3 — Long-tail pages (2 days total)

- Patient history detail view (the longitudinal timeline mockup above).
- Family registration single-screen redesign (already on the task list).
- Admin / settings pages.
- Organization dashboard / clinic selection.

**Acceptance:** no remaining page has gradient banners, colored card backgrounds, or default-collapsed expanders containing primary content.

---

## 8. References

- [BackpackEMR — Homepage](https://www.backpackemr.com/) — "human-centered design," low-clicks, queue-based flow.
- [BackpackEMR — Clinic Management](https://www.backpackemr.com/clinic-management/) — patient queue visualization.
- [Binariks — 14 EMR Interface Principles](https://binariks.com/blog/emr-interface-design-techniques/) — reducing clicks, alerts, navigation time.
- [Stfalcon — EHR UI Principles](https://stfalcon.com/en/blog/post/ehr-user-interface-design-principles) — patient-centric layouts, plain language.
- [Phenomenon Studio — EHR System Design](https://phenomenonstudio.com/ehr-system-design/) — modern EHR aesthetics.
- [MEDITECH Expanse](https://digitalsoftwarereviews.com/2026/03/23/best-emr-systems/) — mobile-first, web-native reference.
- [Bahmni](https://www.bahmni.org/) — open-source EMR adopted in 50+ low-resource countries.
- [Lucide icon set](https://lucide.dev) — recommended icon library (offline-friendly).
- [Apple HIG — iPad layout guidelines](https://developer.apple.com/design/human-interface-guidelines/) — touch sizing (44 pt min; we use 56 px).
- [Tablet UI design — touch targets and spacing](https://www.koombea.com/blog/tablet-ui/) — 10 pt min gap, 16 px min font.

---

*Document version: 2026-05-14. Author: josiahfalde + Claude. Subject to revision after Phase 1 field test.*
