 AI Data Triage System 

An end-to-end Machine Learning ETL pipeline designed to automatically clean messy datasets, route broken data to quarantine, and utilize unsupervised AI to detect mathematical anomalies (fraud). 

This project features **Dual-Mode Execution**: run it as a continuous background Watchdog service for automated server environments, or use the interactive Desktop GUI for manual triage.

 # Key Features

* **The Data Quality Gate:** Automatically detects Nulls (`NaN`) and data-type mismatches, routing them to a `dirty_data` folder before they can crash the pipeline.
* **The Auto-Fixer:** Silently standardizes text (lowercasing, stripping whitespaces) and removes exact duplicate rows in memory.
* **AI Anomaly Detection:** Utilizes `IsolationForest` (Scikit-Learn) tuned to a specific contamination rate to hunt down zero-day mathematical outliers and fraud.
* **Data Routing Architecture:** Automatically sorts processed data into specific human "inboxes" (`clean_data`, `dirty_data`, `anomalies`).
* **Safe Archiving:** Original raw files are never deleted or modified; they are safely moved to a `raw_archive` vault.
* **Dual Execution Modes:** 
  1. **CLI / Watchdog:** Runs continuously in the background, auto-detecting files dropped into the `drop_zone`.
  2. **Desktop GUI:** A Tkinter-based interface with native OS integration to process files and instantly view results.

# Architecture

When the script runs, it automatically generates this routing system:
```text
📦 AI_Data_triage
 ┣ 📂 anomalies      # AI-flagged mathematical outliers (For Fraud Analysts)
 ┣ 📂 clean_data     # Gold-standard, auto-fixed data (For Business Analysts)
 ┣ 📂 dirty_data     # Broken formats and missing nulls (For Data Engineers)
 ┣ 📂 drop_zone      # Input folder for the Watchdog CLI script
 ┗ 📂 raw_archive    # Safe vault for untouched original files
