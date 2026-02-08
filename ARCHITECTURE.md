# System Architecture - Database Entry Count Heatmap

## Overview

This project automatically fetches database entry data from a Notion database and generates an interactive heatmap visualization, deployed daily via GitHub Actions to GitHub Pages.

---

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SYSTEM ARCHITECTURE                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐                              ┌──────────────────────────┐
    │   USER INPUT     │                              │      OUTPUT              │
    │                  │                              │                          │
    │  Notion Database │                              │  GitHub Pages Website    │
    │  (Entry Data)    │                              │  (Interactive Heatmap)   │
    └────────┬─────────┘                              └──────────▲───────────────┘
             │                                                   │
             │ Notion API                                        │ Deploy
             │ (HTTPS)                                           │
             ▼                                                   │
┌────────────────────────────────────────────────────────────────┴─────────────────┐
│                                                                                   │
│                          GITHUB ACTIONS WORKFLOW                                  │
│                     (Runs Daily @ 9:00 AM UTC)                                    │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌────────────┐  │ │
│  │   │  Checkout   │───▶│Setup Python │───▶│  Install    │───▶│   Run      │  │ │
│  │   │   Repo      │    │    3.11     │    │   Deps      │    │  Script    │  │ │
│  │   └─────────────┘    └─────────────┘    └─────────────┘    └─────┬──────┘  │ │
│  │                                                                   │         │ │
│  │                                                                   ▼         │ │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌────────────┐  │ │
│  │   │  Deploy to  │◀───│   Copy to   │◀───│   Upload    │◀───│  Verify    │  │ │
│  │   │ GitHub Pages│    │ deploy/     │    │  Artifact   │    │  HTML      │  │ │
│  │   └─────────────┘    └─────────────┘    └─────────────┘    └────────────┘  │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW                                           │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐          ┌─────────────────────────────────────────────────────┐
│                 │          │          APPLICATION-TRACKER.PY                     │
│  NOTION         │          │                                                     │
│  DATABASE       │  Query   │  ┌─────────────────────────────────────────────┐   │
│                 │ ────────▶│  │         get_applications()                  │   │
│  ┌───────────┐  │ (Paginated)│  │                                            │   │
│  │ Entry 1   │  │          │  │  • POST to Notion API                       │   │
│  │ Entry 2   │  │          │  │  • Paginate (100 items/request)             │   │
│  │ Entry 3   │  │          │  │  • Return all records                       │   │
│  │   ...     │  │          │  └──────────────────┬──────────────────────────┘   │
│  │ Entry N   │  │          │                     │                               │
│  └───────────┘  │          │                     ▼ List[dict]                    │
│                 │          │  ┌─────────────────────────────────────────────┐   │
│  Fields:        │          │  │         count_per_day()                     │   │
│  - Date         │          │  │                                             │   │
│  - Name         │          │  │  • Extract date field                       │   │
│  - Status       │          │  │  • Parse ISO date format                    │   │
│  - etc...       │          │  │  • Count entries per day                    │   │
└─────────────────┘          │  └──────────────────┬──────────────────────────┘   │
                             │                     │                               │
                             │                     ▼ Dict{date: count}             │
                             │  ┌─────────────────────────────────────────────┐   │
                             │  │      draw_interactive_grid()                │   │
                             │  │                                             │   │
                             │  │  • Calculate 60-day window                  │   │
                             │  │  • Build 7×N grid (days × weeks)            │   │
                             │  │  • Apply color scale (gray→red→yellow→green)│   │
                             │  │  • Generate Plotly heatmap                  │   │
                             │  └──────────────────┬──────────────────────────┘   │
                             │                     │                               │
                             └─────────────────────┼───────────────────────────────┘
                                                   │
                                                   ▼
                             ┌─────────────────────────────────────────────────────┐
                             │           interactive_grid.html                     │
                             │                                                     │
                             │  • Standalone HTML file                             │
                             │  • Embedded Plotly visualization                    │
                             │  • Interactive hover tooltips                       │
                             │  • Transparent background                           │
                             └─────────────────────────────────────────────────────┘
```

---

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          COMPONENT ARCHITECTURE                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                            EXTERNAL SERVICES                                     │
├─────────────────────────────────┬───────────────────────────────────────────────┤
│         NOTION API              │              GITHUB SERVICES                   │
│  ┌───────────────────────────┐  │  ┌────────────────────────────────────────┐   │
│  │ api.notion.com/v1         │  │  │  GitHub Actions    │   GitHub Pages   │   │
│  │                           │  │  │  (CI/CD Runner)    │   (Static Host)  │   │
│  │ • Bearer Token Auth       │  │  │                    │                  │   │
│  │ • API Version: 2022-06-28 │  │  │  • Cron Schedule   │   • HTML Hosting │   │
│  │ • Database Query Endpoint │  │  │  • Python Runtime  │   • CDN Delivery │   │
│  └───────────────────────────┘  │  │  • Secrets Mgmt    │   • Custom Domain│   │
│                                 │  └────────────────────────────────────────┘   │
└─────────────────────────────────┴───────────────────────────────────────────────┘
                    │                                        ▲
                    │ HTTPS Requests                         │ Deploy
                    ▼                                        │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌────────────────────────────────────────────────────────────────────────┐    │
│   │                    application-tracker.py                               │    │
│   ├────────────────────────────────────────────────────────────────────────┤    │
│   │                                                                         │    │
│   │  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────────────┐ │    │
│   │  │ Data Fetching    │  │ Data Processing  │  │ Visualization         │ │    │
│   │  │                  │  │                  │  │                       │ │    │
│   │  │ get_applications │─▶│ count_per_day    │─▶│ draw_interactive_grid │ │    │
│   │  │                  │  │                  │  │                       │ │    │
│   │  │ • API calls      │  │ • Date parsing   │  │ • Plotly heatmap      │ │    │
│   │  │ • Pagination     │  │ • Aggregation    │  │ • Color mapping       │ │    │
│   │  │ • Error handling │  │ • Dict building  │  │ • HTML generation     │ │    │
│   │  └──────────────────┘  └──────────────────┘  └───────────────────────┘ │    │
│   │                                                                         │    │
│   └────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                    ▲
                    │ Load
                    │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          CONFIGURATION LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌─────────────────────────┐    ┌─────────────────────────────────────────┐    │
│   │        .env             │    │     GitHub Secrets                      │    │
│   │                         │    │                                         │    │
│   │  NOTION_TOKEN=ntn_xxx   │    │  NOTION_TOKEN      (encrypted)         │    │
│   │  NOTION_DATABASE_ID=xxx │    │  NOTION_DATABASE_ID (encrypted)        │    │
│   │                         │    │  GITHUB_TOKEN       (auto-provided)    │    │
│   │  (Local Development)    │    │  (Production/CI)                       │    │
│   └─────────────────────────┘    └─────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Heatmap Visualization Logic

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        HEATMAP GENERATION LOGIC                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

                          60-Day Lookback Window
    ◀──────────────────────────────────────────────────────────────────────▶

    Week 1    Week 2    Week 3    Week 4    Week 5    Week 6    Week 7    Week 8
    ┌────┐    ┌────┐    ┌────┐    ┌────┐    ┌────┐    ┌────┐    ┌────┐    ┌────┐
Mon │ 0  │    │ 2  │    │ 5  │    │ 0  │    │ 3  │    │ 10 │    │ 0  │    │ 1  │
    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤
Tue │ 1  │    │ 0  │    │ 3  │    │ 7  │    │ 0  │    │ 5  │    │ 2  │    │ 0  │
    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤
Wed │ 0  │    │ 4  │    │ 0  │    │ 12 │    │ 1  │    │ 0  │    │ 8  │    │ 3  │
    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤
Thu │ 2  │    │ 0  │    │ 6  │    │ 0  │    │ 15 │    │ 2  │    │ 0  │    │ 6  │
    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤
Fri │ 0  │    │ 8  │    │ 0  │    │ 4  │    │ 0  │    │ 25 │    │ 1  │    │ 0  │
    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤
Sat │ 0  │    │ 0  │    │ 1  │    │ 0  │    │ 2  │    │ 0  │    │ 0  │    │ 4  │
    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤    ├────┤
Sun │ 0  │    │ 0  │    │ 0  │    │ 0  │    │ 0  │    │ 0  │    │ 0  │    │ 0  │
    └────┘    └────┘    └────┘    └────┘    └────┘    └────┘    └────┘    └────┘

    COLOR SCALE (Entries per day)
    ┌────────────────────────────────────────────────────────────────────────────┐
    │                                                                            │
    │    ░░░░      ████      ████      ████      ████                           │
    │   Gray      Red     Orange    Yellow    Green                             │
    │   (0)      (1-5)    (6-12)   (13-20)   (21-25+)                           │
    │                                                                            │
    │    No      Low     Medium    High      Very                               │
    │  Activity Activity Activity Activity  Active                               │
    │                                                                            │
    └────────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
Database-Entry-Count-Heatmap/
│
├── .github/
│   └── workflows/
│       └── application_heatmap.yml    ← CI/CD Pipeline Definition
│
├── ApplicationHeatmap/
│   ├── application-tracker.py         ← Main Python Script
│   ├── .env                           ← Environment Variables (Local)
│   └── interactive_grid.html          ← Generated Output (Git Ignored)
│
├── deploy/                            ← GitHub Pages Deploy Folder
│   └── index.html                     ← Copy of interactive_grid.html
│
├── .gitignore                         ← Git Ignore Rules
└── ARCHITECTURE.md                    ← This Document
```

---

## Sequence Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SEQUENCE DIAGRAM                                       │
└─────────────────────────────────────────────────────────────────────────────────┘

    Cron/Manual      GitHub        Python         Notion         GitHub
      Trigger        Actions       Script          API           Pages
         │              │             │              │              │
         │──Trigger────▶│             │              │              │
         │              │             │              │              │
         │              │──Setup──────│              │              │
         │              │  Python     │              │              │
         │              │  & Deps     │              │              │
         │              │             │              │              │
         │              │──Execute───▶│              │              │
         │              │             │              │              │
         │              │             │──Query──────▶│              │
         │              │             │  (Page 1)    │              │
         │              │             │◀─Results─────│              │
         │              │             │              │              │
         │              │             │──Query──────▶│              │
         │              │             │  (Page N)    │              │
         │              │             │◀─Results─────│              │
         │              │             │              │              │
         │              │             │──Process     │              │
         │              │             │  Data        │              │
         │              │             │              │              │
         │              │             │──Generate    │              │
         │              │             │  HTML        │              │
         │              │             │              │              │
         │              │◀─Complete───│              │              │
         │              │             │              │              │
         │              │──Deploy────────────────────────────────▶│
         │              │  HTML       │              │              │
         │              │             │              │              │
         │              │◀─Success─────────────────────────────────│
         │              │             │              │              │
         │◀─Complete────│             │              │              │
         │              │             │              │              │
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Data Source** | Notion API | Database entries |
| **Runtime** | Python 3.11 | Script execution |
| **HTTP Client** | requests | API communication |
| **Visualization** | Plotly | Interactive heatmap |
| **Date Handling** | python-dateutil | ISO date parsing |
| **Config** | python-dotenv | Environment variables |
| **CI/CD** | GitHub Actions | Automated execution |
| **Hosting** | GitHub Pages | Static site hosting |

---

## Security Considerations

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         SECURITY ARCHITECTURE                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────┐         ┌───────────────────────────┐
│   LOCAL DEVELOPMENT       │         │   PRODUCTION (CI/CD)      │
├───────────────────────────┤         ├───────────────────────────┤
│                           │         │                           │
│  .env file (⚠️ CAUTION)   │         │  GitHub Secrets (✅ SAFE) │
│                           │         │                           │
│  • NOTION_TOKEN           │         │  • NOTION_TOKEN           │
│  • NOTION_DATABASE_ID     │         │  • NOTION_DATABASE_ID     │
│                           │         │  • GITHUB_TOKEN (auto)    │
│  Risk: File exposure      │         │  Encrypted at rest        │
│  Mitigation: .gitignore   │         │  Injected at runtime      │
│                           │         │                           │
└───────────────────────────┘         └───────────────────────────┘
```

---
