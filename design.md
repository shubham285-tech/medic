# UI/UX Design System Specification
## Medical Expiry Tracker – 3D Modern Medical Inventory & Expiry Management System

---

### 1. Design Philosophy: Modern Healthcare SaaS
The visual identity of **Medical Expiry Tracker** synthesizes four cutting-edge design paradigms:
1. **Modern Healthcare SaaS**: Precision, clarity, sterile cleanliness, and high trust.
2. **3D Dashboard Depth**: Layered z-depth, CSS 3D perspectives, floating medicine capsules, and tactile interactive elements.
3. **Glassmorphism**: Translucent frosted panels, subtle specular borders, and blurred backdrops (`backdrop-filter: blur(16px)`).
4. **Minimal Premium UI**: High scannability, generous breathing room, intentional typographic scale, and zero visual clutter.

---

### 2. Color Palette & Design Tokens

```css
:root {
  /* Brand Primary & Accents */
  --primary: #2563eb;          /* Electric Royal Blue */
  --primary-glow: rgba(37, 99, 235, 0.35);
  --primary-hover: #1d4ed8;
  --secondary: #06b6d4;        /* Cyan Medical Teal */
  --secondary-glow: rgba(6, 182, 212, 0.3);

  /* Status Colors */
  --status-safe: #10b981;      /* Emerald Green (SAFE) */
  --status-safe-bg: rgba(16, 185, 129, 0.12);
  --status-safe-border: rgba(16, 185, 129, 0.3);

  --status-warning: #f59e0b;   /* Amber Gold (EXPIRING SOON) */
  --status-warning-bg: rgba(245, 158, 11, 0.12);
  --status-warning-border: rgba(245, 158, 11, 0.35);

  --status-danger: #ef4444;    /* Crimson Red (EXPIRED) */
  --status-danger-bg: rgba(239, 68, 68, 0.12);
  --status-danger-border: rgba(239, 68, 68, 0.35);

  --status-lowstock: #f97316;  /* Vibrant Coral Orange (LOW STOCK) */
  --status-lowstock-bg: rgba(249, 115, 22, 0.12);
  --status-lowstock-border: rgba(249, 115, 22, 0.35);

  /* Backgrounds & Glass Surfaces */
  --bg-dark: #0a0f1d;          /* Deep Medical Slate Navy */
  --bg-card: rgba(18, 24, 38, 0.72);
  --bg-card-hover: rgba(24, 32, 51, 0.82);
  --bg-glass-modal: rgba(15, 23, 42, 0.88);
  --border-glass: rgba(255, 255, 255, 0.08);
  --border-glass-bright: rgba(255, 255, 255, 0.18);

  /* Typography Colors */
  --text-main: #f8fafc;
  --text-muted: #94a3b8;
  --text-dim: #64748b;

  /* Elevation Shadows */
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.25);
  --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.35);
  --shadow-lg: 0 16px 40px rgba(0, 0, 0, 0.45);
  --shadow-3d: 0 20px 50px rgba(0, 0, 0, 0.5), 0 0 25px var(--primary-glow);
}
```

---

### 3. Exact Visual Status Behaviors

| Status | Condition | Background / Border | Icon / Badge Style | User Action / Indicator |
| :--- | :--- | :--- | :--- | :--- |
| **SAFE** | Expiry $> 30$ days | Emerald tint / Subtle border | Shield Checkmark `✓` | Tranquil green glow; medicine is approved for routine dispensing. |
| **EXPIRING SOON** | $0 < \text{Days} \le 30$ | Amber tint / Pulsing border | Clock `⏳` + "X days left" | Amber pulse; priority queue for FIFO dispensing or distributor return. |
| **EXPIRED** | Expiry Date $\le$ Today | Crimson tint / Red glow | Alert Octagon `⛔` + "Expired X days ago" | High-urgency red flash; quarantine immediately to prevent dispensing. |
| **LOW STOCK** | Quantity $\le$ Min Stock | Vibrant Orange tint | Box / Cube `📦` + "Low: X units" | Orange warning callout; reorder trigger sent to procurement. |

---

### 4. Typography & Hierarchy
- **Font Family**: Primary: `'Outfit'`, `'Inter'`, system sans-serif.
- **Scale**:
  - `Display / Hero Title`: $32\text{px} - 38\text{px}$ (Font weight 700 / 800)
  - `Page Heading (H1)`: $24\text{px} - 28\text{px}$ (Font weight 700)
  - `Section Heading (H2)`: $20\text{px} - 22\text{px}$ (Font weight 600)
  - `Card Header / KPI Value`: $28\text{px} - 32\text{px}$ (Font weight 700)
  - `Body Copy`: $14\text{px} - 15\text{px}$ (Font weight 400 / 500)
  - `Metadata / Badges / Captions`: $11\text{px} - 12\text{px}$ (Font weight 600, uppercase tracked $+0.05\text{em}$)

---

### 5. 3D Elements & Hero Visual Architecture

#### 5.1 Interactive 3D Medicine Capsule Motif (Login & Hero)
- Built with CSS 3D transforms (`perspective: 1200px`, `transform-style: preserve-3d`).
- Composed of:
  1. **Dual-tone 3D Pill Capsule**: Gradient cylinder with specular reflection highlights rotating in slow orbital 3D space (`@keyframes floatPill`).
  2. **Floating Orbit Rings**: Translucent cyan and royal blue orbital halos with medical icons (Medical Shield, Expiry Calendar, Alert Bell, Medical Cross, Inventory Box).
  3. **Atmospheric Lighting**: Radial volumetric light source casting a gentle glow behind the container.
- Tagline: *"Never miss a medicine expiry."*

#### 5.2 3D Metric Stat Cards (Dashboard)
- Cards utilize real-time CSS 3D tilt tracking cursor coordinates (`transform: perspective(1000px) rotateX(...) rotateY(...) scale3d(1.02, 1.02, 1.02)`).
- Glowing top-right badge highlighting rate of change or urgency.
- Gradient icon medallions with embedded 3D drop-shadows.

---

### 6. Component Design Specifications

#### 6.1 Buttons
- **Primary 3D Button**: Linear gradient `#2563eb` $\to$ `#1d4ed8`, soft inset specular line (`box-shadow: inset 0 1px 0 rgba(255,255,255,0.2), 0 4px 14px var(--primary-glow)`).
- **Secondary Glass Button**: Translucent background (`rgba(255,255,255,0.06)`), 1px glass border, smooth hover brightening.
- **Danger Action Button**: Soft crimson glass gradient with red focus ring.

#### 6.2 Data Tables & Mobile Responsive Transformation
- **Desktop Grid**: Frosted glass container (`.glass-card`), sticky table header with subtle border divider, clean vertical alignment, and hover row spotlight.
- **Mobile Transformation**: At viewports $< 768\text{px}$, tabular rows seamlessly transform into stacked 3D cards with clear key-value metadata pairings and full-width action buttons.

#### 6.3 Form Controls & Validation States
- Modern floating/crisp labels, dark input surface (`rgba(255,255,255,0.04)`), and focus glow in cyan/blue.
- Real-time inline feedback: red border + helper icon for invalid dates/quantities; green checkmark when valid.

#### 6.4 Modals & Flyouts
- Centered glassmorphic dialogue box with frosted backdrop blur (`rgba(0,0,0,0.6)` backdrop with `blur(8px)`).
- Spring entrance animation (`transform: scale(0.95)` to `scale(1)` with cubic-bezier easing).

#### 6.5 Charts (Chart.js Configuration)
- Tailored dark mode canvas rendering:
  - Custom HTML tooltips with glassmorphic styling.
  - Smooth 800ms easeOutQuart entry animations.
  - Colors matching brand design tokens (`--primary`, `--secondary`, `--status-safe`, `--status-warning`, `--status-danger`).

---

### 7. Empty & Loading States
- **Empty Inventory State**: 3D illustrated medical storage box icon with message: *"No medicines registered yet. Start tracking your inventory."* and a prominent "+ Add Medicine" button.
- **Empty Alerts State**: Glowing green shield icon with message: *"All clear! No medicines are currently expired or expiring soon."*
- **Skeleton Loaders**: Shimmering gradient bars for asynchronous data fetching transitions.
- **Toast Notifications**: Floating glassmorphic toast cards in bottom-right corner with auto-dismiss timer.
