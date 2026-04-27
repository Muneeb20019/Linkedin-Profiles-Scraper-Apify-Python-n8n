# LinkedIn Profiles Scraper & Enrichment for Event Exhibitors + Personalized Outreach Email Sender System using n8n and Apify

![n8n](https://img.shields.io/badge/Workflow-n8n-FF6C37?style=flat&logo=n8n&logoColor=white)
![Python](https://img.shields.io/badge/Logic-Python-3776AB?style=flat&logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Scraping-Playwright-2EAD33?style=flat&logo=playwright&logoColor=white)
![Gemini](https://img.shields.io/badge/AI-Gemini_1.5_Flash-4285F4?style=flat&logo=googlegemini&logoColor=white)
![Google Sheets](https://img.shields.io/badge/Database-Google_Sheets-34A853?style=flat&logo=googlesheets&logoColor=white)

---

## 📺 Project Demo
Experience the end-to-end automation from dynamic web scraping to AI-generated sales personalization.

https://www.loom.com/share/865d1da864014910bf7f1432fdd16de5

---

## 🚀 The Solution: Autonomous Intelligence
This system solves the problem of manual lead research and outreach at scale. It transforms raw, dynamic event data into a high-fidelity, outreach-ready database with zero manual intervention.

### 🛑 The Problem
*   **Manual Research Exhaustion:** Visiting individual company websites one-by-one to find data is a massive time-sink.
*   **Manual Copy-Paste:** Sales teams often spend hours manually copying and pasting LinkedIn URLs, emails, and phone numbers into spreadsheets.
*   **Data Fragmentation:** Important contact details are often buried deep in website footers, making them hard to find without automation.

### ✅ The Solution
This workflow functions as an **Autonomous Outreach Agent**. It eliminates manual research by:
1.  **Automated Extraction:** Using Python to navigate complex galleries and extract profile metadata automatically.
2.  **Database Creation:** Generating a structured database with LinkedIn URLs, verified company websites, phone numbers, and professional emails.
3.  **Intelligent Outreach:** Writing highly relevant outreach emails based on specific technical "signals" found during the scraping process.

---

## 🧠 Core Technical Pillars

### 1. 🕸️ Dynamic Extraction (Python + Playwright)
The system uses an asynchronous **Playwright** browser instance. This logic mimics human behavior—waiting for network idle states and rendering JavaScript—to successfully extract unique exhibitor IDs and profile data from the event portal.

**Scraper logic in action:**
![Apify Scraper Result](https://github.com/Muneeb20019/Linkedin-Profiles-Scraper-Apify-Python-n8n/blob/main/Phyton%20Apify.png?raw=true)

### 2. 🤖 Signal-Based Personalization (Gemini AI)
The workflow integrates **Gemini 1.5 Flash**. I engineered a prompt that extracts "Signals" from technical product categories to generate a 20-word curiosity-based "hook." This ensures the email feels like it was written by a human expert and is based specifically on the unique products the company is showcasing at the event.

### 3. 🧹 Clean Data for Database
To maintain a professional, production-ready database, I implemented a **Custom Code Node**. This serves as a data controller that:
*   Strips AI metadata (quotes, word counts, and formatting).
*   Corrects formatting issues in phone numbers and URLs.
*   Ensures 100% matching accuracy between company names and their enriched contact details before the data is saved.

---

## ✨ Final Result (Google Sheets)
The final output is a clean, actionable database showing Names, Websites, LinkedIn URLs, Phone Numbers, and high-quality Personalized First Lines ready for an automated email campaign.

![Final Google Sheet Result](https://github.com/Muneeb20019/Linkedin-Profiles-Scraper-Apify-Python-n8n/blob/main/Final%20Result.png?raw=true)

---

## 🛠️ Technical Stack
| Layer | Technology |
| :--- | :--- |
| **🔄 Automation** | n8n (Orchestration & Logic) |
| **🐍 Logic** | Python / Playwright (Deep Scraping) |
| **🧠 AI** | Google Gemini 1.5 Flash (Intelligence) |
| **☁️ Environment** | Apify (Cloud Execution) |
| **💾 Delivery** | Google Sheets (Final Dataset) |
| **📜 Scripting** | JavaScript / Python (Data Cleaning) |

---

## ✍️ Author
**Muneeb Ali Khan**
*   **GitHub:** [@Muneeb20019](https://github.com/Muneeb20019)
*   **LinkedIn:** [Muneeb Ali Khan](https://www.linkedin.com/in/muneeb-ali-khan-2a1675365)

---

## 📜 License
This project is licensed under the MIT License.
