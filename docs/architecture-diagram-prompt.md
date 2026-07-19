# Architecture diagram — generation prompt

Paste the prompt below into Google **Gemini** (image generation) to produce the
architecture diagram, then save the result as `docs/images/architecture.png`.

> Tip: image models approximate branded icons. For a pixel-accurate result, take
> the generated layout and rebuild it in **draw.io / Excalidraw** using the
> official **Azure Architecture Icons** pack (aka.ms/azureicons). Ask for a 16:9,
> high-resolution PNG.

---

## Prompt

Create a clean, professional software **architecture diagram** — flat 2D,
landscape 16:9, high resolution, white background — for an application called
**"AI Exam Assistant"**. Use the **official Microsoft Azure architecture icon
set** (the flat, multi-colour Azure service icons) and the official **GitHub
Actions** icon. Azure-blue (#0078D4) accents, light-gray rounded container boxes,
clear directional arrows, and legible sans-serif labels. Title it
**"AI Exam Assistant — Architecture"**. Spell every label exactly as written.

Lay it out in grouped layers, top to bottom:

1. **Client (top):** a web-browser window labelled
   *"React 19 + Vite + TypeScript — Chat · Exam · Concept Map · Dashboard"*.
   A downward arrow labelled **"REST + SSE"** to layer 2.

2. **API:** a box *"FastAPI backend"* running on **Azure Container Apps**
   (use the Azure Container Apps icon).

3. **Orchestration** — a large rounded container titled
   **"Microsoft Agent Framework 1.11"** containing a **"Coordinator"** agent at
   the entry that branches with arrows to three agents: **"Tutor"**, **"Exam"**,
   **"Analytics"**. From **"Exam"**, a sequential arrow to
   **"Question Generator"** and then to **"Validator"**. Draw each agent as a
   small robot/agent chip.

4. **Knowledge** — two parallel boxes feeding the agents:
   (a) **"Foundry IQ — agentic retrieval"** wired to the **Azure AI Search** icon;
   (b) **"GraphRAG — concept map + global search"**.

5. **Azure AI Foundry** — a container with the **Azure AI Foundry** icon holding
   model chips: **"GPT-5.4-mini"**, **"GPT-5-nano"**, **"GPT-5.5"**,
   **"text-embedding-3-large"**. An arrow from the Agent Framework into it.

**Right-side vertical column — cross-cutting Azure services** (official icons +
labels): **"Microsoft Entra ID (managed identity)"**, **"Azure Key Vault"**,
**"Azure AI Content Safety"**, **"Azure Monitor / Application Insights
(OpenTelemetry)"**.

**Bottom lane — CI/CD quality gate:** the **GitHub Actions** icon next to a box
**"Agent evaluation — groundedness · sources · Azure AI Evaluation"**, with a
dashed arrow pointing back at the agents (it evaluates them).

Show the main data flow with arrows:
Browser → FastAPI → Coordinator → (Tutor / Exam / Analytics) → Knowledge
(Foundry IQ / GraphRAG) → Azure AI Foundry models, and results returning to the
browser. Keep it uncluttered, balanced and presentation-quality.
