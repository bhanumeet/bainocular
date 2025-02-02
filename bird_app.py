import tkinter as tk
import cv2
import time
import threading
from transformers import pipeline
from PIL import Image, ImageTk
from datetime import datetime
import os
import RPi.GPIO as GPIO

# -----------------------------
# GPIO SETUP
# -----------------------------
BUTTON_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# -----------------------------
# BIRD CLASSIFIER SETUP
# -----------------------------
print("Loading bird classification model...")
classifier = pipeline("image-classification", model="chriamue/bird-species-classifier")
print("Model loaded.")

# -----------------------------
# Create Output Folders
# -----------------------------
os.makedirs("captured_birds", exist_ok=True)
os.makedirs("arcade_birds", exist_ok=True)

# -----------------------------
# Global Variables for Camera Stream
# -----------------------------
global_frame = None
frame_lock = threading.Lock()

# -----------------------------
# CAMERA THREAD CLASS
# -----------------------------
class CameraThread(threading.Thread):
    def __init__(self, src=0, width=640, height=480):
        super().__init__()
        self.cap = cv2.VideoCapture(src, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        ret, frame = self.cap.read()
        with frame_lock:
            global global_frame
            global_frame = frame.copy() if ret else None
        self.stopped = False

    def run(self):
        global global_frame
        while not self.stopped:
            ret, frame = self.cap.read()
            if ret:
                with frame_lock:
                    global_frame = frame.copy()
            # Adjust sleep for ~30fps (33ms delay)
            time.sleep(0.033)

    def stop(self):
        self.stopped = True
        self.cap.release()

# Start the camera thread
camera_thread = CameraThread(src=0, width=640, height=480)
camera_thread.start()

# -----------------------------
# CAPTURE & IDENTIFY FUNCTION
# -----------------------------
def capture_and_identify(mode="explore"):
    """
    Uses the latest frame from the camera thread, saves it, and runs classification.
    Returns (bird_name, confidence, frame).
    """
    global global_frame
    with frame_lock:
        if global_frame is None:
            return "Unknown", 0, None
        frame = global_frame.copy()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_path = f"{mode}_birds/bird_{timestamp}.jpg"
    cv2.imwrite(raw_path, frame)
    pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    predictions = classifier(pil_image)
    bird_name = "Unknown"
    confidence = 0
    if predictions:
        top_pred = predictions[0]
        label = top_pred["label"]
        conf = top_pred["score"] * 100
        if conf >= 50 and "looney" not in label.lower():
            bird_name = label
            confidence = conf
        else:
            bird_name = "Unknown"
            confidence = conf
    safe_label = bird_name.replace(" ", "_")
    final_path = f"{mode}_birds/{safe_label}_{timestamp}.jpg"
    os.rename(raw_path, final_path)
    return bird_name, confidence, frame

# -----------------------------
# OVERLAY TEXT ON FRAME
# -----------------------------
def overlay_text_on_frame(frame, text):
    """
    Overlays the provided text on the given BGR frame.
    The text is drawn in bold white with a pink outline.
    Returns the result as a PIL Image.
    """
    annotated = frame.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.5
    thickness_outline = 3
    thickness_text = 2
    position = (50, 100)
    cv2.putText(annotated, text, position, font, font_scale, (180,105,255), thickness_outline, cv2.LINE_AA)
    cv2.putText(annotated, text, position, font, font_scale, (255,255,255), thickness_text, cv2.LINE_AA)
    annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
    return Image.fromarray(annotated_rgb)

# -----------------------------
# FINAL POPUP (Arcade Mode Final Alert)
# -----------------------------
def show_final_popup(parent, text, duration=2000, geometry="600x200+100+100"):
    popup = tk.Toplevel(parent)
    popup.overrideredirect(True)
    popup.geometry(geometry)
    popup.configure(bg="black")
    label = tk.Label(popup, text=text, fg="white", bg="black", font=("Arial", 24, "bold"))
    label.pack(expand=True)
    popup.after(duration, popup.destroy)

# -----------------------------
# MAIN APPLICATION CLASS
# -----------------------------
class BAIApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("bAInoculars")
        # Always run full-screen
        self.attributes("-fullscreen", True)
        self.config(cursor="none")
        self.configure(bg="#2B0042")

        # Frames for menu, Explore mode, and Arcade mode
        self.menu_frame = None
        self.explore_frame = None
        self.arcade_frame = None

        # Explore mode flag (pauses live feed while snapshot is displayed)
        self.freeze_explore = False

        # Arcade mode variables
        self.arcade_total = 60         # Total countdown time in seconds
        self.arcade_running = False    # Overall arcade mode state
        self.freeze_arcade = False     # True when a snapshot is being displayed
        self.arcade_start_time = None  # The (adjusted) start time for the countdown
        self.pause_start_time = None   # Time when snapshot display begins
        self.arcade_score = 0
        self.arcade_birds = set()

        self.create_menu_frame()
        self.create_explore_frame()
        self.create_arcade_frame()
        self.show_frame(self.menu_frame)

        # Bind Escape key to quit the application
        self.bind("<Escape>", lambda e: self.on_quit())

    # -------------------------
    # FRAME CREATION
    # -------------------------
    def create_menu_frame(self):
        frame = tk.Frame(self, bg="#2B0042")
        title_label = tk.Label(frame, text="bAInoculars", bg="#2B0042", fg="yellow",
                                font=("Impact", 40, "bold"), pady=20)
        title_label.pack()
        btn_style = {"fg": "white", "bg": "#FF4500", "activebackground": "#FF6347",
                     "font": ("Arial", 24, "bold"), "width": 25, "height": 2}
        btn_explore = tk.Button(frame, text="Explore Mode", command=self.start_explore, **btn_style)
        btn_explore.pack(pady=20)
        btn_arcade = tk.Button(frame, text="Arcade Mode", command=self.start_arcade, **btn_style)
        btn_arcade.pack(pady=20)
        btn_quit = tk.Button(frame, text="Quit", command=self.on_quit,
                             fg="white", bg="#FF0000", activebackground="#AA0000",
                             font=("Arial", 24, "bold"), width=25, height=2)
        btn_quit.pack(pady=20)
        self.menu_frame = frame

    def create_explore_frame(self):
        frame = tk.Frame(self, bg="black")
        self.explore_label = tk.Label(frame, bg="black")
        self.explore_label.pack(fill="both", expand=True)
        self.explore_label.bind("<Button-1>", self.on_explore_capture)
        back_btn = tk.Button(frame, text="Back", command=self.back_to_menu,
                             fg="white", bg="#444", font=("Arial", 20, "bold"))
        back_btn.pack(side="bottom", pady=20)
        self.explore_frame = frame

    def create_arcade_frame(self):
        frame = tk.Frame(self, bg="black")
        self.arcade_label = tk.Label(frame, bg="black")
        self.arcade_label.pack(fill="both", expand=True)
        self.arcade_label.bind("<Button-1>", self.on_arcade_capture)
        self.arcade_info_label = tk.Label(frame, text="", fg="white", bg="black",
                                          font=("Arial", 24, "bold"))
        self.arcade_info_label.pack(side="top", pady=20)
        back_btn = tk.Button(frame, text="Back", command=self.end_arcade_early,
                             fg="white", bg="#444", font=("Arial", 24, "bold"))
        back_btn.pack(side="bottom", pady=20)
        self.arcade_frame = frame

    # -------------------------
    # NAVIGATION
    # -------------------------
    def show_frame(self, frame):
        for f in (self.menu_frame, self.explore_frame, self.arcade_frame):
            if f is not None:
                f.pack_forget()
        frame.pack(fill="both", expand=True)

    def back_to_menu(self):
        self.arcade_running = False
        self.show_frame(self.menu_frame)

    # -------------------------
    # MENU ACTIONS
    # -------------------------
    def start_explore(self):
        self.show_frame(self.explore_frame)
        self.freeze_explore = False
        self.update_explore_frame()
        self.poll_button_explore()

    def start_arcade(self):
        self.arcade_score = 0
        self.arcade_birds = set()
        self.arcade_running = True
        self.freeze_arcade = False
        self.arcade_start_time = time.time()
        self.show_frame(self.arcade_frame)
        self.update_arcade_frame()
        self.poll_button_arcade()

    # -------------------------
    # EXPLORE MODE METHODS
    # -------------------------
    def on_explore_capture(self, event=None):
        if self.freeze_explore:
            return
        self.freeze_explore = True
        bird_name, conf, captured_frame = capture_and_identify("captured")
        if captured_frame is None:
            self.freeze_explore = False
            return
        display_text = (f"Identified: {bird_name} ({conf:.0f}%)" 
                        if bird_name != "Unknown" else "No bird identified")
        annotated_img = overlay_text_on_frame(captured_frame, display_text)
        imgtk = ImageTk.PhotoImage(annotated_img)
        self.explore_label.imgtk = imgtk
        self.explore_label.configure(image=imgtk)
        self.explore_frame.after(2000, self.resume_explore)

    def resume_explore(self):
        self.freeze_explore = False

    def update_explore_frame(self):
        if self.explore_frame.winfo_manager() == "":
            return
        if not self.freeze_explore:
            with frame_lock:
                frame = global_frame.copy() if global_frame is not None else None
            if frame is not None:
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(cv2image)
                imgtk = ImageTk.PhotoImage(pil_img)
                self.explore_label.imgtk = imgtk
                self.explore_label.configure(image=imgtk)
        self.explore_frame.after(33, self.update_explore_frame)  # ~30 fps

    def poll_button_explore(self):
        if self.explore_frame.winfo_manager() == "":
            self.after(100, self.poll_button_explore)
            return
        if GPIO.input(BUTTON_PIN) == GPIO.LOW and not self.freeze_explore:
            self.on_explore_capture()
            self.after(300, self.poll_button_explore)
        else:
            self.after(100, self.poll_button_explore)

    # -------------------------
    # ARCADE MODE METHODS
    # -------------------------
    def on_arcade_capture(self, event=None):
        if not self.arcade_running or self.freeze_arcade:
            return
        self.freeze_arcade = True
        self.pause_start_time = time.time()
        bird_name, conf, captured_frame = capture_and_identify("arcade")
        if captured_frame is None:
            self.freeze_arcade = False
            return
        if bird_name != "Unknown" and conf >= 50:
            if bird_name not in self.arcade_birds:
                self.arcade_birds.add(bird_name)
                self.arcade_score += 1
            display_text = f"Identified: {bird_name} ({conf:.0f}%)"
        else:
            display_text = "No bird identified"
        annotated_img = overlay_text_on_frame(captured_frame, display_text)
        imgtk = ImageTk.PhotoImage(annotated_img)
        self.arcade_label.imgtk = imgtk
        self.arcade_label.configure(image=imgtk)
        self.arcade_frame.after(2000, self.resume_arcade_update)

    def resume_arcade_update(self):
        pause_duration = time.time() - self.pause_start_time
        self.arcade_start_time += pause_duration
        self.freeze_arcade = False

    def poll_button_arcade(self):
        if not self.arcade_running or self.arcade_frame.winfo_manager() == "":
            self.after(100, self.poll_button_arcade)
            return
        if GPIO.input(BUTTON_PIN) == GPIO.LOW and not self.freeze_arcade:
            self.on_arcade_capture()
            self.after(300, self.poll_button_arcade)
        else:
            self.after(100, self.poll_button_arcade)

    def update_arcade_frame(self):
        if not self.arcade_running or self.arcade_frame.winfo_manager() == "":
            return
        if not self.freeze_arcade:
            elapsed = time.time() - self.arcade_start_time
            remaining = self.arcade_total - elapsed
            if remaining <= 0:
                self.arcade_running = False
                self.show_arcade_final()
                return
            with frame_lock:
                frame = global_frame.copy() if global_frame is not None else None
            if frame is not None:
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(cv2image)
                imgtk = ImageTk.PhotoImage(pil_img)
                self.arcade_label.imgtk = imgtk
                self.arcade_label.configure(image=imgtk)
            self.arcade_info_label.configure(
                text=f"Time Left: {int(remaining)}s   Score: {self.arcade_score}"
            )
        self.arcade_frame.after(33, self.update_arcade_frame)  # ~30 fps

    def show_arcade_final(self):
        with frame_lock:
            frame = global_frame.copy() if global_frame is not None else None
        if frame is not None:
            final_text = f"Time's Up! Final Score: {self.arcade_score}"
            final_img = overlay_text_on_frame(frame, final_text)
            imgtk = ImageTk.PhotoImage(final_img)
            self.arcade_label.imgtk = imgtk
            self.arcade_label.configure(image=imgtk)
        self.arcade_frame.after(2000, self.back_to_menu)

    def end_arcade_early(self):
        if self.arcade_running:
            self.arcade_running = False
            self.show_arcade_final()
        else:
            self.back_to_menu()

    # -------------------------
    # CLEANUP
    # -------------------------
    def on_quit(self):
        camera_thread.stop()
        GPIO.cleanup()
        self.destroy()

# -----------------------------
# MAIN ENTRY POINT
# -----------------------------
if __name__ == "__main__":
    try:
        app = BAIApp()
        app.protocol("WM_DELETE_WINDOW", app.on_quit)
        app.mainloop()
    except KeyboardInterrupt:
        GPIO.cleanup()
        camera_thread.stop()
        print("Interrupted by user.")
    except Exception as e:
        GPIO.cleanup()
        camera_thread.stop()
        print("Error:", e)
