import tkinter as tk
from tkinter import messagebox, scrolledtext
from datetime import datetime, timedelta
import winsound
import pygetwindow as gw

# ================= CONFIG =================
FORBIDDEN = ["youtube", "instagram", "facebook", "whatsapp",
             "twitter", "netflix", "snapchat"]

# ✅ UPDATED EMPLOYEES & SHIFTS
EMPLOYEE_SHIFTS = {
    # Morning shift
    "alex": (6.0, 13.5),
    "sri": (6.0, 13.5),
    # Afternoon shift
    "smith": (14.0, 20.5),
    "divya": (14.0, 20.5),
    # Night shift
    "john": (21.0, 5.5),
    "mona": (21.0, 5.5)
}

CHECK_INTERVAL = 3000  # ms
THRESHOLDS = {
    "action_speed": 2,
    "service_diversity": 3,
    "behavioral_deviation": 3
}

# ================= HELPERS =================
def beep():
    try:
        winsound.Beep(1200, 600)
    except:
        pass

def get_login_hour_float():
    now = datetime.now()
    return now.hour + now.minute / 60.0

def get_active_forbidden_windows():
    active = []
    for title in gw.getAllTitles():
        title = title.strip().lower()
        if not title:
            continue
        for app in FORBIDDEN:
            if app in title:
                active.append(app.capitalize())
    return list(set(active))


# ================= MONITOR =================
class EmployeeMonitor:
    def __init__(self, emp):
        self.emp = emp
        self.login_times = []
        self.action_times = []
        self.used_apps = set()
        self.last_apps = set()

    def record(self, active_apps):
        now = datetime.now()
        if active_apps:
            if not self.login_times or (now - self.login_times[-1]) > timedelta(minutes=1):
                self.login_times.append(now)
            if set(active_apps) != self.last_apps:
                self.action_times.append(now)
            self.used_apps.update(active_apps)
            self.last_apps = set(active_apps)

    def metrics(self):
        freq = len(self.login_times)
        if len(self.action_times) >= 2:
            gaps = [(self.action_times[i] - self.action_times[i-1]).seconds
                    for i in range(1, len(self.action_times))]
            speed = round(sum(gaps) / len(gaps), 1)
        else:
            speed = 0

        diversity = len(self.used_apps)
        irregular = 0
        start, end = EMPLOYEE_SHIFTS[self.emp]
        for t in self.login_times:
            hr = t.hour + t.minute / 60
            if start < end:
                if hr < start or hr >= end:
                    irregular += 1
            else:
                if hr < start and hr >= end:
                    irregular += 1

        deviation = round(diversity + irregular * 0.5, 1)
        return freq, speed, diversity, irregular, deviation


# ================= IMPROVED GUI =================
class MonitorGUI:
    def __init__(self, root):
        self.root = root
        root.title("Employee Monitoring Dashboard")
        root.geometry("920x820")
        root.configure(bg="#0f172a")  # Dark modern background

        self.emp_var = tk.StringVar()
        self.monitor = None
        self.alerting = False

        # ================= TITLE =================
        title = tk.Label(root, text="EMPLOYEE MONITORING DASHBOARD",
                         font=("Helvetica", 20, "bold"),
                         fg="#60a5fa", bg="#0f172a")
        title.pack(pady=15)

        # ================= EMPLOYEE INPUT =================
        input_frame = tk.Frame(root, bg="#0f172a")
        input_frame.pack(pady=8)

        tk.Label(input_frame, text="Employee Name:",
                 font=("Arial", 11), fg="#cbd5e1", bg="#0f172a").pack(side="left", padx=5)

        self.emp_entry = tk.Entry(input_frame, textvariable=self.emp_var,
                                  font=("Arial", 11), width=25, bg="#1e2937", fg="white",
                                  insertbackground="white", relief="flat", bd=5)
        self.emp_entry.pack(side="left", padx=5)

        tk.Button(input_frame, text="Start Monitoring", bg="#22c55e", fg="black",
                  font=("Arial", 10, "bold"), relief="flat", padx=15, pady=6,
                  command=self.start).pack(side="left", padx=15)

        # ================= ALERT LABEL =================
        self.alert = tk.Label(root, text="", fg="#ef4444",
                              font=("Helvetica", 28, "bold"), bg="#0f172a", height=2)
        self.alert.pack(pady=10)

        # ================= METRICS FRAME =================
        metrics_frame = tk.LabelFrame(root, text=" Monitoring Metrics ",
                                      font=("Arial", 12, "bold"),
                                      fg="#94a3b8", bg="#0f172a",
                                      labelanchor="n", padx=15, pady=10)
        metrics_frame.pack(fill="both", padx=25, pady=10)

        self.labels = {}
        fields = [
            "Login Hour", "Shift Hours", "Active Forbidden Services",
            "Status", "Login Frequency", "Action Speed",
            "Service Diversity", "Session Irregularity",
            "Behavioral Deviation"
        ]

        for i, f in enumerate(fields):
            row = tk.Frame(metrics_frame, bg="#0f172a")
            row.pack(fill="x", pady=4)

            lbl_title = tk.Label(row, text=f"{f}:", width=22, anchor="w",
                                 font=("Arial", 10, "bold"),
                                 fg="#94a3b8", bg="#0f172a")
            lbl_title.pack(side="left")

            lbl_value = tk.Label(row, text="--", anchor="w",
                                 font=("Arial", 10),
                                 fg="#e2e8f0", bg="#0f172a")
            lbl_value.pack(side="left", padx=10, fill="x")
            self.labels[f] = lbl_value

        # ================= REVIEW BOX =================
        tk.Label(root, text="Review / Reason for Alert",
                 font=("Arial", 12, "bold"), fg="#f1f5f9", bg="#0f172a").pack(pady=(15, 5))

        self.review_box = scrolledtext.ScrolledText(
            root, height=11, font=("Consolas", 10),
            bg="#1e2937", fg="#e0f2fe", relief="flat", bd=5
        )
        self.review_box.pack(fill="both", padx=25, pady=5)

        # Footer
        footer = tk.Label(root, text="Real-time Employee Behavior Monitoring System",
                          font=("Arial", 9), fg="#64748b", bg="#0f172a")
        footer.pack(side="bottom", pady=10)

    def start(self):
        emp = self.emp_var.get().lower().strip()
        if emp not in EMPLOYEE_SHIFTS:
            messagebox.showerror("Error", "Employee not recognized.\nUse: alex, sri, smith, divya, john, mona")
            return

        self.monitor = EmployeeMonitor(emp)
        self.review_box.delete("1.0", tk.END)
        self.loop()

    def blink(self):
        if not self.alerting:
            return
        current_text = self.alert.cget("text")
        self.alert.config(text="" if current_text else "SUSPICIOUS ACTIVITY DETECTED ❌")
        self.root.after(600, self.blink)

    def loop(self):
        login_hr = get_login_hour_float()
        start, end = EMPLOYEE_SHIFTS[self.monitor.emp]
        forbidden = get_active_forbidden_windows()

        self.monitor.record(forbidden)
        freq, speed, div, irr, dev = self.monitor.metrics()

        review = []

        # ===== STATUS LOGIC (unchanged) =====
        if forbidden:
            status = "Suspicious ❌"
            review.append("🚨 FORBIDDEN APPLICATION USAGE DETECTED")
            review.append(f"• Detected: {', '.join(forbidden)}")
            review.append("Real-time policy violation - Immediate attention required.")
            if not self.alerting:
                self.alerting = True
                beep()
                self.blink()
        else:
            self.alerting = False
            self.alert.config(text="")
            review.append("Action Speed:")
            review.append(f"• Measured: {speed}s | Threshold: ≥ {THRESHOLDS['action_speed']}s")
            review.append("\nService Diversity:")
            review.append(f"• Used: {div} | Allowed: ≤ {THRESHOLDS['service_diversity']}")
            review.append("\nSession Irregularity:")
            review.append(f"• Irregular logins: {irr}")
            review.append("\nBehavioral Deviation:")
            review.append(f"• Value: {dev} | Allowed: ≤ {THRESHOLDS['behavioral_deviation']}")

            if speed < THRESHOLDS["action_speed"] or \
               div > THRESHOLDS["service_diversity"] or \
               dev > THRESHOLDS["behavioral_deviation"]:
                status = "Warning ⚠️"
            else:
                status = "Normal ✅"
                review = []

        # ===== UPDATE UI WITH BETTER COLORS =====
        self.labels["Login Hour"].config(
            text=f"{int(login_hr)}:{int((login_hr % 1) * 60):02d}",
            fg="#60a5fa"
        )
        self.labels["Shift Hours"].config(
            text=f"{int(start):02d}:00 → {int(end):02d}:00",
            fg="#94a3b8"
        )
        self.labels["Active Forbidden Services"].config(
            text=f"{', '.join(forbidden) or 'None'}",
            fg="#ef4444" if forbidden else "#4ade80"
        )
        self.labels["Status"].config(
            text=status,
            fg="#ef4444" if "Suspicious" in status else
               "#eab308" if "Warning" in status else "#4ade80"
        )
        self.labels["Login Frequency"].config(text=str(freq), fg="#c4d0e1")
        self.labels["Action Speed"].config(text=f"{speed}s", fg="#c4d0e1")
        self.labels["Service Diversity"].config(text=str(div), fg="#c4d0e1")
        self.labels["Session Irregularity"].config(text=str(irr), fg="#c4d0e1")
        self.labels["Behavioral Deviation"].config(text=str(dev), fg="#c4d0e1")

        # Update Review Box
        self.review_box.delete("1.0", tk.END)
        if review:
            self.review_box.insert(tk.END, "\n".join(review))

        self.root.after(CHECK_INTERVAL, self.loop)


# ================= RUN =================
if __name__ == "__main__":
    root = tk.Tk()
    MonitorGUI(root)
    root.mainloop()