# Giorgos (Georgios) Traskas — LinkedIn Profile

**Headline:** Data Scientist & AI/ML Engineer | Python • LLMs • RAG • Agentic AI (CrewAI, LangGraph, MCP) | AWS Cloud Engineer | Production ML Pipelines
**Location:** Thessaloniki Metropolitan Area, Greece
**Profile:** [linkedin.com/in/george-traskas](https://www.linkedin.com/in/george-traskas)
**Open to work:** Artificial Intelligence Engineer, Machine Learning Engineer, Data Scientist and Python Developer roles
**Network:** 466+ connections, 484 followers

## About

I am a production-focused Data Scientist and ML Engineer with 8 years of experience building and deploying machine learning systems. My background is built on real-world execution, including 4 years scaling data workflows at Predictive Fitness and delivering 90+ successful global client projects. I specialize in the entire deployment and reliability layer: AWS data pipelines (Lambda, ECS Fargate, Athena, S3), engineering predictive models (time series, classification, causal inference), and maintaining production stability with Grafana and Sentry.

Most recently I designed and shipped MolekitChen, a food science AI assistant for iOS that answers cooking questions using peer-reviewed research from PubMed and USDA. Every answer is grounded and sourced. The backend runs Python FastAPI + LangChain + Supabase pgvector with Row-Level Security.

Open to Data Science and AI/LLM/ML roles focused on real-world deployment, where engineering scalable workflows and system reliability matter just as much as model metrics.

## Top Skills

Retrieval-Augmented Generation (RAG) • Large Language Models (LLM) • Python • AI/ML • Data Science

## Featured

- **MolekitChen — AI Food Science App, now on the App Store.** Native iOS app built in SwiftUI with a Python FastAPI backend. Answers cooking and nutrition questions using peer-reviewed research from PubMed and USDA, with citations and evidence grades on every answer. Production-hardened RAG architecture using Gemini, LangChain, and Supabase pgvector with HNSW indexing.
- **Certification: Vibe Coding** (Lovable)
- **Certification: Claude 101** (Anthropic)

## Experience

### Data Scientist (Independent Contractor) — Predictive Fitness (Contract)
**May 2022 - Present · 4+ yrs | Southlake, TX, USA · Remote**

Working with Predictive Fitness, a US-based fitness technology company focused on optimizing athlete training outcomes, as an independent contractor data scientist and Python developer.

- Designed and deployed production-grade data pipelines and predictive models supporting athlete performance and training analytics.
- Built and operated cloud workflows on AWS (S3, Lambda, ECS Fargate, Athena, RDS, CloudWatch).
- Ingested and processed large datasets from wearables, smartwatches, and internal systems via GraphQL APIs.
- Implemented data cleaning, feature engineering, model training, evaluation, and deployment workflows in Python (OOP).
- Set up monitoring, alerting, and reliability tracking using Sentry and Grafana.
- Collaborated with remote, cross-functional teams using Jira and Microsoft Teams.
- Translated raw data into clear, actionable business insights to support product and decision-making.

### Founder and Owner — Data Science Solutions
**Mar 2024 - Present | Thessaloniki, Greece**

Services: Data Engineering (robust data pipelines), Business Intelligence (reporting and visualization), Machine Learning and AI (predictive models and automation), Data Strategy Consulting, Advanced Analytics (statistical forecasting).

### Data Scientist — Upwork (Freelance)
**Jul 2020 - Present | Remote**

- Among the top 3% of performers on Upwork, providing data science and consulting services.
- Clients include investment firms, medical and healthcare groups, energy companies, and more.
- Delivered quality data science solutions and consulting to over 85 clients (100% Job Success Score).

### Analytical Chemist — Chemical Process & Energy Resources Institute (CERTH)
**Dec 2007 - Jul 2024 · 16 yrs 8 mos | Greece**

- Conferred with engineers on research projects, interpreted results, developed analytical methods.
- Operated and maintained laboratory instruments; troubleshot malfunctions.
- Automated repetitive tasks, increasing sample throughput by 80% and reducing delivery times by 50%.

### Analytical Chemist — Hellenic Army
**Dec 2005 - Nov 2006 | Greece**

- Analysed wheat flours (rheological properties) and wear metals in lubricants for military engines.
- Received Corporal promotion for exceptional work.

### Research Chemist — Research Committee (Full-time)
**Feb 2003 - Oct 2005 | Greece**

- Water and wastewater treatment projects: bench and full-scale pilot experiments.
- Collaborated on a novel water treatment process that increased water production of Thessaloniki city by 10%.
- Published 4 peer-reviewed articles; received EUR 150K funding for 3 research projects; trained 3 PhD candidates.

## Education

- **Machine Learning Engineer Nanodegree** — Udacity (2020)
- **Data Analyst Nanodegree** — Udacity (2017)
- **Master's Degree, Chemical Technology** — Aristotle University of Thessaloniki (2002-2004), Grade 9.25/10.
  Thesis: "Comparable evaluation of various aluminium based coagulants for the treatment of surface water and urban wastewater".
- **Bachelor's Degree, Chemistry** — Aristotle University of Thessaloniki (1996-2002), Grade 7.2/10.
  Thesis: "Removal of phosphorus and chromium ions from aqueous solutions by adsorption onto akaganeite".

## Licenses & Certifications (11)

- **AI Engineer Core Track: LLM Engineering, RAG, QLoRA, Agents** — Udemy (Jul 2026)
- **Claude 101** — Anthropic (Apr 2026)
- **Vibe Coding** — Lovable (2026)
- **Analyze Datasets and Train ML Models using AutoML** — Coursera (May 2022)
- **AWS Cloud Technical Essentials** — Coursera (Mar 2022)
- **Sequences, Time Series and Prediction** — Coursera (Apr 2021)
- **Google Cloud Big Data and Machine Learning Fundamentals** — Coursera (Dec 2019)
- **Introduction to TensorFlow for AI, ML, and Deep Learning** — Coursera (May 2019)
- **Neural Networks and Deep Learning** — Coursera (Apr 2019)
- **Data Science, Deep Learning, & Machine Learning with Python** — Udemy (Dec 2017)
- **Introduction to Water Treatment** — edX Honor Code Certificate

## Projects

### MolekitChen — AI Food Science App, live on the App Store (2026 - Present)

[Landing page](https://molekitchen-landing.pages.dev) | [App Store](https://apps.apple.com/us/app/molekitchen/id6773031788)

Designed and shipped a full-stack iOS application as a solo project from architecture to App Store. MolekitChen answers cooking and nutrition questions using peer-reviewed research from PubMed Central and USDA, with citations and an evidence grade on every answer.

- **RAG pipeline:** Gemini embeddings + pgvector HNSW over ~1,600 food-science papers; hybrid vector + BM25 retrieval merged with Reciprocal Rank Fusion; reranking pass; 50-token sentence-boundary chunk overlap; lost-in-the-middle mitigation; few-shot prompt; Pydantic schema validation with automatic retry.
- **Frontend:** Swift/SwiftUI, Apple Sign-In and Google Sign-In (OAuth2/JWT).
- **Backend:** Python FastAPI async, LangChain orchestration, Docker on Render, GitHub Actions CI/CD.
- **Database:** Supabase PostgreSQL + pgvector + HNSW + Row-Level Security binding JWT tokens to every vector query.
- **Security:** five-layer input guardrail stack (Unicode normalization, language detection, gibberish filtering, medical/off-topic blocking, prompt-injection pattern matching); SlowAPI tiered rate limiting.
- **Data integrity:** deny-by-default ingestion, only CC0/CC-BY sources, per-chunk license metadata.

### Wine Value Hunter (wine-vfm) — Agentic AI bargain hunter, live web app (2026)

[Code](https://github.com/gtraskas/wine-vfm) | Live demo on Modal

Agentic AI system that finds underpriced wines in a real online shop:

- An LLM planner uses other agents as tools in an agentic loop.
- Llama 3.2 3B fine-tuned with QLoRA (4-bit, rank-256) on 88K curated wine reviews, served on a Modal GPU.
- RAG pipeline grounding a frontier model with similar wines from a ChromaDB vector store.
- Neural network plus an ensemble with regression-fitted weights (no hand-picked blending).
- Live e-commerce ingestion with structured outputs and a deterministic value-for-money metric.
- Deployed end-to-end on a Modal web app; the GPU wakes only on demand.

### Quidnet Energy — Automation Tasks (Sep 2020 - Jul 2022)

- Python automation to join, clean, and transform large datasets beyond Excel's limits; complex formulas and interactive visualisations.
- Greatly assisted the analytics team exploring energy-storage data. The project was supported by Bill Gates.

## Recent Activity (LinkedIn posts)

**On shipping Wine Value Hunter (Jul 2026):** "I have successfully shipped my capstone project, extending it into my own domain: wine. Wine Value Hunter is an agentic AI system designed to find underpriced wines in a real online shop. With just one button press, you can watch it work live: an LLM planner utilizes other agents as tools in an agentic loop; a Llama 3.2 3B model fine-tuned with QLoRA (4-bit, rank-256) on 88K curated wine reviews, served on a Modal GPU; a RAG pipeline grounds a frontier model with similar wines from a ChromaDB vector store; a neural network combined with an ensemble featuring regression-fitted weights (no hand-picked blending); live e-commerce ingestion with structured outputs and a deterministic value-for-money metric; deployed end-to-end on a Modal web app, with the GPU waking only on demand. My own contributions include my own dataset and target metric, a value-ranked scanner over a live shop, regression-learned ensemble weights, and the autonomous LLM planner running in production." (308 impressions)

**On launching MolekitChen (Jun 2026):** "I am excited to announce the launch of MolekitChen on the App Store, a food science assistant designed to answer cooking questions using peer-reviewed research rather than guesswork. If you ask, 'Should garlic rest after chopping before cooking?' the app vectorizes your question, searches ~1,600 peer-reviewed papers from PubMed Central and USDA using HNSW indexing, reranks the results, assembles a structured prompt with few-shot examples, calls Gemini, validates the output, and returns a cited answer with an evidence grade. All in one query." (516 impressions)

## Volunteering

**First aid — Red Cross Youth** (Oct 2012 - May 2013): served at hospital Accident & Emergency departments.

## Publications (4)

- "Comparison of Efficiency between Poly-aluminium Chloride and Aluminium Sulphate Coagulants during Full-scale Experiments in a Drinking Water Treatment Plant." *Separation Science and Technology*, 43: 1507-1519.
- "Comparable Evaluation of Iron-based Coagulants for the Treatment of Surface Water and of Contaminated Tap Water." *Separation Science and Technology*, 42: 803-817.
- Plus 2 more peer-reviewed publications in water treatment.

## Skills (62 total — highlights)

Python • Machine Learning • Data Science • Data Analysis (23 endorsements, endorsed by colleagues as highly skilled) • Retrieval-Augmented Generation (RAG) • Large Language Models (LLM) • NLP • LangChain • Google Gemini • Vector Databases • FastAPI • Swift • GraphQL • ETL • Data Pipelines • AWS • Sentry • Grafana • Jira • AI/ML

LinkedIn Skill Assessments passed: **Python**, **Machine Learning**.

## Courses

- Laboratory Accreditation to ISO/IEC 17025

## Languages

- English (professional working proficiency)
- Greek (native)

## Interests

Follows Andrew Ng (DeepLearning.AI, AI Fund, AI Aspire) among AI/ML top voices.
