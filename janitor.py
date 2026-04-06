import os
import time
import shutil
import pandas as pd
from sklearn.ensemble import IsolationForest
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Define all our folders (The "Inboxes")
DROP_ZONE = "./drop_zone"
CLEAN_DIR = "./clean_data"
ANOMALY_DIR = "./anomalies"
DIRTY_DIR = "./dirty_data"
ARCHIVE_DIR = "./raw_archive" # Safety vault for the original file

def process_file(filepath):
    filename = os.path.basename(filepath)
    print(f"\n[+] Detected new file: {filename}")
    
    try:
        # ==========================================
        # STAGE 0: LOAD THE DATA
        # ==========================================
        df = pd.read_csv(filepath)
        original_row_count = len(df)
        print(f"[*] Loaded {original_row_count} rows. Starting Triage...")
        
        # ==========================================
        # STAGE 1: THE AUTO-FIX (No Humans Needed)
        # ==========================================
        print("[*] Auto-fixing duplicates, spaces, and cases...")
        
        # Drop exact duplicate rows
        df = df.drop_duplicates()
        
        # Clean up text: lowercasing and stripping whitespace
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip().str.lower()
            df[col] = df[col].replace('', pd.NA) # Turn empty spaces into recognizable Nulls

        # Coerce valid numbers hiding as text back into numbers
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='ignore')

        # ==========================================
        # STAGE 2: DIRTY DATA QUARANTINE (For Data Engineers)
        # ==========================================
        print("[*] Routing broken/missing data to quarantine...")
        
        # Identify rows with Nulls/NaNs (Unfixable by AI)
        dirty_mask = df.isnull().any(axis=1)
        dirty_data = df[dirty_mask]
        
        # Isolate the clean data to move forward
        clean_format_data = df.dropna()
        
        # Route broken data to its specific inbox
        if not dirty_data.empty:
            dirty_data.to_csv(os.path.join(DIRTY_DIR, f"dirty_{filename}"), index=False)
            print(f"[!] Routed {len(dirty_data)} broken rows to dirty_data folder.")
        
        if clean_format_data.empty:
            print("[-] All data was broken. Nothing left for AI to analyze.")
            shutil.move(filepath, os.path.join(ARCHIVE_DIR, f"original_{filename}"))
            return

        # ==========================================
        # STAGE 3: AI ANOMALY DETECTION (For Fraud Analysts)
        # ==========================================
        print("[*] AI scanning clean data for mathematical outliers...")
        
        numeric_df = clean_format_data.select_dtypes(include=['number'])
        
        if not numeric_df.empty:
            # AI isolates the weird math
            model = IsolationForest(contamination=0.04, random_state=42)
            clean_format_data = clean_format_data.copy()
            clean_format_data['Anomaly_Score'] = model.fit_predict(numeric_df)
            
            # Split the final results
            final_clean = clean_format_data[clean_format_data['Anomaly_Score'] == 1].drop(columns=['Anomaly_Score'])
            anomalies = clean_format_data[clean_format_data['Anomaly_Score'] == -1].drop(columns=['Anomaly_Score'])
            
            # Route perfect data and anomalies to their inboxes
            final_clean.to_csv(os.path.join(CLEAN_DIR, f"clean_{filename}"), index=False)
            anomalies.to_csv(os.path.join(ANOMALY_DIR, f"weird_{filename}"), index=False)
            
            print(f"[+] SUCCESS: Routed {len(final_clean)} perfect rows to clean_data.")
            print(f"[!] WARNING: Routed {len(anomalies)} anomalies to anomalies folder.")
        else:
            print("[-] No numeric columns found for AI to scan.")
        
        # ==========================================
        # STAGE 4: ARCHIVE THE ORIGINAL
        # ==========================================
        archive_path = os.path.join(ARCHIVE_DIR, f"original_{filename}")
        shutil.move(filepath, archive_path)
        print(f"[*] Pipeline complete. Original file safely stored in raw_archive.")
        
    except Exception as e:
        print(f"[-] Error processing file: {e}")

# The Watchdog logic
class Watcher(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.csv'):
            time.sleep(1)
            process_file(event.src_path)

if __name__ == "__main__":
    print(" detection processis online...")
    print("Press Ctrl+C to stop the script.")
    
    # Safety check: Auto-creates all 5 folders if they don't exist yet
    for folder in [DROP_ZONE, CLEAN_DIR, ANOMALY_DIR, DIRTY_DIR, ARCHIVE_DIR]:
        os.makedirs(folder, exist_ok=True)
    
    observer = Observer()
    observer.schedule(Watcher(), DROP_ZONE, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nShutting down system.")
    observer.join()