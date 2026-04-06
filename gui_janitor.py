import os
import shutil
import pandas as pd
from sklearn.ensemble import IsolationForest
import tkinter as tk
from tkinter import filedialog, messagebox
import platform
import subprocess

# Define all our folders
DROP_ZONE = "./drop_zone"
CLEAN_DIR = "./clean_data"
ANOMALY_DIR = "./anomalies"
DIRTY_DIR = "./dirty_data"
ARCHIVE_DIR = "./raw_archive"

# Ensure folders exist
for folder in [DROP_ZONE, CLEAN_DIR, ANOMALY_DIR, DIRTY_DIR, ARCHIVE_DIR]:
    os.makedirs(folder, exist_ok=True)

# ==========================================
# SYSTEM FUNCTION: Open Files Natively
# ==========================================
def open_file_natively(filepath):
    if not filepath or not os.path.exists(filepath):
        messagebox.showerror("Error", "File does not exist or wasn't generated.")
        return
        
    try:
        # Cross-platform way to open a file in the user's default app (like Excel)
        if platform.system() == 'Windows':
            os.startfile(filepath)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.call(('open', filepath))
        else:  # Linux
            subprocess.call(('xdg-open', filepath))
    except Exception as e:
        messagebox.showerror("Error", f"Could not open file: {e}")

# ==========================================
# THE PIPELINE
# ==========================================
def process_file(filepath):
    filename = os.path.basename(filepath)
    clean_path = weird_path = dirty_path = None
    
    try:
        df = pd.read_csv(filepath)
        total_rows = len(df)
        
        # STAGE 1: AUTO-FIX
        df = df.drop_duplicates()
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip().str.lower()
            df[col] = df[col].replace('', pd.NA)
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='ignore')

        # STAGE 2: DIRTY DATA
        dirty_mask = df.isnull().any(axis=1)
        dirty_data = df[dirty_mask]
        clean_format_data = df.dropna()
        
        if not dirty_data.empty:
            dirty_path = os.path.join(DIRTY_DIR, f"dirty_{filename}")
            dirty_data.to_csv(dirty_path, index=False)
        
        # STAGE 3: AI BOUNCER
        if clean_format_data.empty:
            shutil.move(filepath, os.path.join(ARCHIVE_DIR, f"original_{filename}"))
            return total_rows, len(dirty_data), 0, 0, None, None, dirty_path
            
        numeric_df = clean_format_data.select_dtypes(include=['number'])
        
        if not numeric_df.empty:
            model = IsolationForest(contamination=0.04, random_state=42)
            clean_format_data = clean_format_data.copy()
            clean_format_data['Anomaly_Score'] = model.fit_predict(numeric_df)
            
            final_clean = clean_format_data[clean_format_data['Anomaly_Score'] == 1].drop(columns=['Anomaly_Score'])
            anomalies = clean_format_data[clean_format_data['Anomaly_Score'] == -1].drop(columns=['Anomaly_Score'])
            
            clean_path = os.path.join(CLEAN_DIR, f"clean_{filename}")
            weird_path = os.path.join(ANOMALY_DIR, f"weird_{filename}")
            
            final_clean.to_csv(clean_path, index=False)
            anomalies.to_csv(weird_path, index=False)
            
            clean_count = len(final_clean)
            weird_count = len(anomalies)
        else:
            clean_count = weird_count = 0

        # STAGE 4: ARCHIVE
        shutil.move(filepath, os.path.join(ARCHIVE_DIR, f"original_{filename}"))
        
        # Return the stats AND the file paths
        return total_rows, len(dirty_data), clean_count, weird_count, clean_path, weird_path, dirty_path
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to process file:\n{e}")
        return 0, 0, 0, 0, None, None, None

# ==========================================
# GUI ARCHITECTURE (Tkinter)
# ==========================================
def upload_file():
    # Hide old buttons if running a new file
    for widget in action_frame.winfo_children():
        widget.destroy()

    filepath = filedialog.askopenfilename(
        title="Select a CSV File",
        filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
    )
    
    if not filepath:
        return 

    filename = os.path.basename(filepath)
    drop_zone_path = os.path.join(DROP_ZONE, filename)
    shutil.copy(filepath, drop_zone_path)
    
    status_label.config(text=f"⚙️ Processing {filename}...", fg="blue")
    app.update()
    
    # Run pipeline and catch the returned paths
    total, dirty, clean, weird, c_path, w_path, d_path = process_file(drop_zone_path)
    
    if total > 0:
        status_label.config(text="✅ Pipeline Complete!", fg="green")
        result_text = (
            f"📊 RESULTS FOR: {filename}\n\n"
            f"Total Rows Scanned: {total}\n"
            f"-----------------------------------\n"
            f"🧹 Auto-Fixed & Cleaned: {clean} rows\n"
            f"🚨 AI Anomalies Found: {weird} rows\n"
            f"🗑️ Broken/Dirty Data: {dirty} rows"
        )
        results_label.config(text=result_text)

        # Generate the dynamic buttons based on what data was created
        if c_path:
            tk.Button(action_frame, text="👁️ View Clean Data", bg="#4CAF50", fg="white", 
                      command=lambda: open_file_natively(c_path)).pack(side=tk.LEFT, padx=5)
        if w_path:
            tk.Button(action_frame, text="🚨 View Anomalies", bg="#F44336", fg="white", 
                      command=lambda: open_file_natively(w_path)).pack(side=tk.LEFT, padx=5)
        if d_path:
            tk.Button(action_frame, text="🗑️ View Dirty Data", bg="#FF9800", fg="white", 
                      command=lambda: open_file_natively(d_path)).pack(side=tk.LEFT, padx=5)

# Build the Main Window
app = tk.Tk()
app.title("Enterprise AI Data Janitor")
app.geometry("500x480")
app.configure(bg="#f4f4f9")

# Header
header = tk.Label(app, text="🤖 AI Data Triage System", font=("Arial", 16, "bold"), bg="#f4f4f9")
header.pack(pady=20)

# Upload Button
upload_btn = tk.Button(app, text="📁 Select Data File (CSV)", font=("Arial", 12), bg="#2196F3", fg="white", padx=20, pady=10, command=upload_file)
upload_btn.pack(pady=10)

status_label = tk.Label(app, text="Waiting for file...", font=("Arial", 10, "italic"), bg="#f4f4f9", fg="gray")
status_label.pack(pady=5)

# Results Dashboard Frame
result_frame = tk.Frame(app, bg="white", bd=2, relief="groove")
result_frame.pack(pady=10, padx=30, fill="both", expand=True)

results_label = tk.Label(result_frame, text="Results will appear here.", font=("Arial", 11), bg="white", justify="left")
results_label.pack(pady=20, padx=20)

# Action Buttons Frame (This is where the dynamic buttons will spawn)
action_frame = tk.Frame(app, bg="#f4f4f9")
action_frame.pack(pady=10)

# Run the App
app.mainloop()