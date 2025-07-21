# 🚀 Tracktive – AI Competitor Tracker for Product Managers

![Tracktive Logo](https://img.shields.io/badge/Built%20By-Ayush-blueviolet?style=flat-square)

**Tracktive** is a smart, lightweight AI-powered dashboard that keeps Product Managers up to date on competitors' subtle product changes — so you never miss a feature drop, price tweak, or UI update again.

Developed by **Ayush** for the **Product Space AI Hackathon 2025**, Tracktive combines real-time web scraping, AI summarization (via LLaMA 3), and a clean frontend UI to deliver competitor intelligence automatically.

---

## 🧠 The Problem

Modern PMs manage too much:

* Dozens of competitors
* Scattered changelogs & blog posts
* UI changes with zero announcements

Staying ahead manually? It just doesn’t scale. That’s where Tracktive steps in.

---

## 💡 The Solution – Tracktive

Tracktive is your AI agent that:

* 🕵️‍♀️ Monitors changelogs, blogs, and update feeds
* 🔍 Detects what changed since the last version
* 🧠 Uses LLaMA 3 to explain the impact of those changes
* 🏷️ Tags updates by type (feature, price, docs, UI)
* 📈 Scores importance based on keywords & context
* 📊 Shows a filtered summary in a fast, interactive dashboard
* 📨 Simulates delivery via Slack/Notion reports

---

## 🛠️ Architecture Overview (Text Summary)

1. **Input URLs** – The user adds competitor URLs or changelog links.
2. **Scraping Engine** – Runs at intervals to fetch updated page content.
3. **Change Detector** – Compares current content with last version.
4. **AI Summarizer** – Generates brief summaries using LLaMA 3 via Ollama.
5. **Scoring Engine** – Assigns relevance scores using keyword context.
6. **Flask Backend** – Connects frontend to logic.
7. **Frontend UI** – Shows summaries and filters with clean UX.
8. **Report Generator** – Option to download as PDF or simulate Slack/Notion delivery.

---

## 🌟 Key Features at a Glance

| 🔧 Feature               | 💬 Description                                       |
| ------------------------ | ---------------------------------------------------- |
| Competitor Tracker       | Monitor any public changelog, blog, or update page   |
| AI Summaries             | LLaMA 3 generates clean summaries with meaning       |
| Relevance Scoring        | Uses keyword matching and frequency to score updates |
| Change Categorization    | Tags like `Pricing`, `Feature`, `Docs`, `UI`         |
| Clean UI                 | Easy-to-use dashboard with filters and sorting       |
| Weekly Digest Simulation | Bundles updates into shareable reports               |
| Slack/Notion Integration | Simulated delivery endpoints via webhook             |

---

## 🧰 Tech Stack

| Layer        | Tools / Libraries       |
| ------------ | ----------------------- |
| Backend      | Python + Flask          |
| Scraping     | BeautifulSoup, Requests |
| AI Inference | Ollama (LLaMA 3)        |
| Frontend     | HTML + CSS + JS         |
| Storage      | SQLite DB               |
| Automation   | `schedule`, `datetime`  |
| Export       | ReportLab (PDF)         |

---

## 🔌 Integrations (Simulated)

* 🟣 **Slack Webhooks** — Update pushes to channels
* 🟡 **Notion Sync** — Link-only preview (prototype)

Real-time, authenticated delivery is on the roadmap.

---

## 🔮 Roadmap (Post-Hackathon)

* Real Slack & Notion integrations
* User login & competitor personalization
* Chrome extension for live UI monitoring
* Alerting system for major changes
* Dark mode dashboard

---

## 👤 About the Builder

**Ayush**
AI Builder | Python + Product Nerd | Loves solving PM painpoints
📎 [LinkedIn](https://www.linkedin.com/in/ayush-kaushik10604/)

---

## 🏁 Submission Info

* **Event**: Product Space AI Agent Hackathon 2025
* **Track**: Competitor Feature Tracker for PMs
* **Status**: ✅ Submitted with working prototype

---

## 📄 License

MIT License — Use for learning, hacking, and building!
Reach out on LinkedIn for ideas or collaboration.
