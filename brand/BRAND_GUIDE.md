# Dr. Denise Turley: Brand Guide

Version 1, October 20, 2026. Built from the October 20 strategy summary.

This is the working reference for the website, LinkedIn, speaking, and anything else with Denise's name on it. When something new gets made, it should pass the checks at the end of this file.

---

## 1. The foundation

**Core belief**
Technology should expand what's possible for people.

**Value proposition**
I bring ideas and technology to life in ways that help people create opportunities, make choices, and pursue the lives they envision.

**Role of AI**
AI is the technology Denise is applying today. It supports the philosophy and never replaces it. Content about AI should always connect back to what it makes possible for people.

**Closing conviction (from the bio)**
Progress is meaningful when it improves people's lives and gives them more options for their future.

---

## 2. Brand architecture

```
Dr. Denise Turley                      the brand is the person
└── Technology should expand           core belief (established)
    what's possible for people.
    └── More Possible                  signature series (recommended, open)
        ├── The Power of Options       signature keynote (recommended)
        └── Three content pillars
            ├── Possibility in Practice
            ├── Opportunity and Choice
            └── Leadership and Human Impact
```

### Signature name: recommendation

The strategy summary calls this open. Here's how the candidates score against the three jobs a signature idea has to do: website headline, keynote theme, and a thread through the content.

| Candidate | Headline | Keynote | Content thread | Notes |
|---|---|---|---|---|
| **More Possible** | Strong | Good | Strong | Lifts straight from the core belief. Covers all three pillars. Works as a phrase in a sentence ("this makes more possible"). |
| The Power of Options | Good | Strong | Medium | Concrete and warm. Fits careers, money, and choice well. "The Power of X" is a common title formula, so it's harder to own as an umbrella. Weaker for demo content. |
| What If, Made Real | Medium | Good | Good | Captures curiosity plus execution. Slightly clever for a headline. |
| Room to Choose | Medium | Medium | Medium | Human and gentle. Too narrow for leadership content. |

**Recommendation:** use **More Possible** as the signature series and keep **The Power of Options** as the title of the signature keynote. That keeps the concept already in development, gives it a specific home, and lets the umbrella name stay as broad as the philosophy.

Both names live in one place on the website (`src/data/site.js`), so changing the decision is a one-line edit.

---

## 3. Audience

Lead audience (preliminary): **established professionals, particularly women navigating career growth and change.** Write so this person feels the content was made for her, without excluding anyone else.

| Audience | What they need | What Denise offers |
|---|---|---|
| Established professionals | Career resilience, growth, financial flexibility | How to create options and stay adaptable |
| Graduates and early career | Skills, confidence, employment | How to use technology to become more capable and employable |
| Business leaders | Responsible adoption, organizational change, value | How to make technology work for organizations and their people |
| People pursuing personal goals | Time, creativity, learning, better decisions | Practical ways technology supports a fuller life |

This hasn't been validated with keyword or audience-performance data. Revisit after 90 days of LinkedIn analytics (see the LinkedIn kit for what to track).

---

## 4. Content pillars

| Pillar | What it covers | Typical formats |
|---|---|---|
| **Possibility in Practice** | Demonstrations, experiments, creative projects, practical builds | Short video, screen recordings, before/after, "I tried this" posts |
| **Opportunity and Choice** | Career resilience, skills, entrepreneurship, financial decisions, agency | Text posts, frameworks, carousels, newsletter essays |
| **Leadership and Human Impact** | Leading change, hard decisions, organizational redesign, consequences for people | Reflective posts, talks, panels, long-form essays |

Family, creative interests, and personal experience belong in the content when they genuinely illustrate the idea. They establish credibility and relatability. They should never read as a display of wealth or accomplishment.

---

## 5. Messaging

### Bios

**Full (approved October 2026)**

> Dr. Denise Turley believes technology should expand what's possible for people. For more than 20 years, she has turned curiosity into action, bringing new ideas and technologies to life in ways that create meaningful opportunities. Her work is driven by a belief that innovation should empower people to make choices, pursue their ambitions, and shape the futures they envision for themselves.
>
> A senior executive, educator, and author, Denise has spent her career anticipating change and translating possibilities into practical impact. Today, she brings that same perspective to artificial intelligence, helping people and organizations harness its potential to rethink how they work, live, and pursue success on their own terms.
>
> Her experience spans executive leadership, entrepreneurship, and higher education. She has developed educational content for CNBC and LinkedIn Learning, appeared on PBS, and teaches graduate-level business and technology courses.
>
> At the heart of her work is a simple conviction: Progress is meaningful when it improves people's lives and gives them more options for their future.

**Medium (event programs, ~85 words)**

> Dr. Denise Turley is a senior executive, educator, and author who believes technology should expand what's possible for people. For more than 20 years she has led business and technology transformation, turning new ideas into practical results. Today she applies that experience to AI, helping people and organizations use it to create opportunities and more choice in how they work and live. She has developed educational content for CNBC and LinkedIn Learning, appeared on PBS, and teaches graduate-level business and technology courses.

**Short (introductions, ~30 words)**

> Dr. Denise Turley is an executive, educator, and author who helps people and organizations use technology, today AI, to create more options in work and life.

**One line (social bios, email signature)**

> Executive, educator, author. Technology should expand what's possible for people.

### Factual guardrails

- CNBC and LinkedIn Learning are **past** engagements. Use past tense: "developed educational content for." Never "a CNBC contributor" or "LinkedIn Learning instructor" in present tense.
- PBS: "appeared on PBS."
- Teaching is current: "teaches graduate-level business and technology courses."
- Never name a past or current client organization. Results can be cited unattributed ("at one organization I supported").
- No numbers about her own results unless they're documented.

### What the brand does not do

- No courses, paid communities, or memberships. Calls to action are to **follow, read, watch, or invite to speak.**
- No wealth display. Personal success shows up as evidence of choices made possible, never as the point.
- No AI hype. The brand outlasts any one technology.

---

## 6. Voice

Grounded, practical, human. Confident without being loud. Speaks from having done the work.

**Do**
- Use contractions.
- Lead with the point. Short sentences, varied rhythm.
- Use specific examples and real numbers when they exist.
- Acknowledge what's working before naming a concern.
- Use "I" on the website and LinkedIn. Use third person in bios and media kits.

**Don't**
- Em dashes. Use periods or colons.
- "It's not X, it's Y" or "Not because X. Because Y."
- Rhetorical questions that lead the reader to an answer she already holds.
- Hype words: game-changing, transformative, revolutionary, shocking.
- Filler: "here's what I learned," "here's the thing," "at the end of the day," "nobody's talking about this."

**Sounds like her**
> Good technology gives people more room to choose. That's the test I apply to every new tool, including AI.

**Doesn't**
> AI is a game-changer that will transform everything you know about work.

---

## 7. Visual identity

### The mark
One starting point opening into three paths. It's the visual form of "more options" and works at favicon size. File: `src/components/Mark.js` and `static/favicon.svg`.

### Color

| Token | Hex | Use |
|---|---|---|
| Ink | `#1C2433` | Primary text, dark sections, buttons |
| Paper | `#F7F3EC` | Main background |
| Sand | `#EBE3D5` | Alternate section background |
| Clay | `#A8462A` | Accent: emphasis, eyebrows, links, the mark |
| Clay soft | `#F1DDD2` | Accent on dark backgrounds |
| Sage | `#4F6B5A` | Secondary accent, sparingly (charts, tags) |

Warm neutrals with one confident accent. The palette avoids the blue-and-purple gradient look common to tech brands, which keeps the focus on people.

Contrast: Ink on Paper and Clay on Paper both pass WCAG AA for body text.

### Type
- **Fraunces** (serif) for headlines and pull quotes. Warm, a little literary, educator energy.
- **Inter** (sans) for body and interface. Clear and practical.
- Both are free on Google Fonts and available in Canva.

### Photography
- Natural light, real settings: teaching, speaking, working, building, family moments she chooses to share.
- Warm tones that sit well on Paper and Sand.
- Avoid: glowing brains, robots, blue circuit boards, stock handshakes.
- Needed now: one professional headshot (portrait crop) and two or three candid working shots.

---

## 8. Signature keynote concept

**The Power of Options: Building choice for people and organizations in the age of AI**

The room arrives worried about AI and their work. It leaves with agency. Three movements, one per pillar:

1. **See what's possible.** Live demonstrations on real tasks. (Possibility in Practice)
2. **Build your options.** Skills, resilience, financial flexibility, personal agency. (Opportunity and Choice)
3. **Lead so others have options.** What leaders owe the people going through change. (Leadership and Human Impact)

Close on the conviction: progress is meaningful when it gives people more options for their future.

To develop next: the opening story `[DT: a real moment that shows technology creating a choice for someone]`, the two or three live demos, and one framework the audience can take home.

---

## 9. Channel map

| Channel | Role | Cadence |
|---|---|---|
| LinkedIn | Primary audience growth and conversation | 3 posts a week |
| LinkedIn newsletter: *More Possible* | Long-form essays, the signature thread | Twice a month |
| Website | Home for ideas, speaking, media kit | Updated as work publishes |
| Video (LinkedIn native first, YouTube optional) | Possibility in Practice demos | 2 a month |
| Speaking | Credibility and reach | Pursue actively once keynote is ready |

---

## 10. Open items (need Denise)

- [ ] Final call on signature name (recommendation above)
- [ ] Professional headshot and 2 to 3 candid photos
- [ ] Domain name and Netlify account for the site
- [ ] LinkedIn profile URL
- [ ] Book or publication title(s) behind "author"
- [ ] PBS segment name, date, link
- [ ] CNBC and LinkedIn Learning titles and links (past)
- [ ] Public contact email, or use the site form only
- [ ] Opening story for the keynote

---

## 11. Before anything goes out

1. Does it connect to the core belief?
2. Is every fact about Denise something she's confirmed?
3. Are CNBC and LinkedIn Learning in past tense?
4. No client names?
5. No em dashes, no "it's not X, it's Y," no hype words?
6. Is the call to action follow, read, watch, or invite? Nothing for sale.
