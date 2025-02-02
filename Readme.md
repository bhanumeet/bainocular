# bAInoculars

**bAInoculars** is an interactive Python application that leverages computer vision to identify bird species in real-time using your webcam. It provides **two core modes**—**Explore** and **Arcade**—each designed to foster engagement and learning about the amazing world of birds. The project also includes placeholders for **Star Gazing** modes, opening the door to future functionality around astronomy.

---

## About the Project

Our goal is to make **bAInoculars** a fun and educational tool:
- **Nature Exploration**: Use technology to deepen your understanding of local wildlife.
- **Real-Time Learning**: See instant AI-driven results about what bird might be in front of your camera.
- **Classroom Engagement**: Teachers and students can use this as a hands-on learning experience, reinforcing scientific observation and data analysis in a modern, approachable way.

While the core focus is currently on bird identification, the framework is flexible enough to extend into other domains, such as star gazing or additional wildlife models. By blending **education** and **entertainment**, bAInoculars aims to spark curiosity and excitement about the natural world.

---

## Features

1. **Birds Explore Mode**  
   - **Real-time** bird identification from your webcam feed.  
   - Overlays classification labels on video.  
   - Automatically **saves** snapshots when a bird is detected.  
   - Ideal for education, personal projects, or simply satisfying your curiosity about feathered friends visiting your area.

2. **Birds Arcade Mode**  
   - A **timed challenge** (default 60 seconds) to identify as many **distinct** birds as possible.  
   - Each new bird species detected boosts your score.  
   - Concludes with a **score summary** pop-up—great for friendly competitions or classroom exercises.

3. **(Optional) Star Gazing Explore & Arcade**  
   - Currently **placeholders**, showing how you can adapt the same concept to **astronomy**.  
   - Potential for future development to identify constellations, planets, or other celestial objects.

---

## Installation

1. **Clone or Download** this repository:
   ```bash
   git clone https://github.com/bhanumeet/bAInoculars.git
   cd bAInoculars


## Usage
Run the main script:

bash
Copy
Edit
python bird_app.py
A Tkinter menu will appear with four buttons:

# Birds Explore Mode
# Birds Arcade Mode

Select a Mode to open the corresponding OpenCV window:

Birds Explore Mode: An ongoing bird identification feed. Press q or close the window to exit.
Birds Arcade Mode: You have 60 seconds to identify as many distinct birds as possible. The session ends automatically, or press q to quit early.
Educational Use Case:

In a classroom setting, students can learn about AI and machine learning while directly observing real-time classification.
Arcade Mode can be turned into a fun group activity—who can identify the most birds in a minute?
Encourages inquiry-based learning, teamwork, and excitement about biodiversity and technology.
Notes
This app uses chriamue/bird-species-classifier from Hugging Face for bird recognition.
Ensure your webcam is accessible. If you have multiple cameras, change the index in cv2.VideoCapture(0) to another number.
If you run into font errors, replace "arial.ttf" with a local TrueType font path or remove it to rely on the default Pillow font.
Star Gazing modes are placeholders. You can build upon them for celestial object classification.


## Contributing
Fork this repository.
Create a feature branch:
bash
Copy
Edit
git checkout -b feature/new-feature
Commit your changes:
bash
Copy
Edit
git commit -am "Add new-feature"
Push to the branch:
bash
Copy
Edit
git push origin feature/new-feature
Open a pull request to merge your changes.