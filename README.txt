RAGASENSE - BEGINNER SETUP GUIDE
================================

WHAT THIS PROJECT DOES
- Participant registration and login
- Participant profile fields from the assignment
- Raga list and audio player
- Counts listening time while the audio is playing
- Unlocks emotion ratings after 60 seconds of recorded listening
- Stores nine Navarasa ratings (0 to 4) in SQLite
- Admin dashboard for participants and annotations
- CSV export
- Admin can add raga records and upload audio

IMPORTANT
This is a learning / prototype implementation. Test the system thoroughly before real research use.
The browser timer is suitable for a classroom prototype, not tamper-proof research-grade timing.
Use consent approved by your institution before collecting real participant data.
Change the admin password and SECRET_KEY before deployment.
Do not deploy Flask's debug server publicly.

STEP 1 - INSTALL
1. Install Python 3 from https://www.python.org/downloads/
2. During Windows installation, tick "Add Python to PATH".
3. Install VS Code from https://code.visualstudio.com/
4. Extract this ZIP file to a folder you can find, e.g. Desktop\Raga_Emotion_Annotation.

STEP 2 - OPEN THE PROJECT
1. Open VS Code.
2. Click File > Open Folder.
3. Choose the extracted Raga_Emotion_Annotation folder.
4. Click Terminal > New Terminal.

STEP 3 - INSTALL FLASK
In the VS Code terminal, type:
    python -m venv venv

Windows PowerShell:
    .\venv\Scripts\Activate.ps1

If PowerShell blocks activation, use Command Prompt terminal:
    venv\Scripts\activate.bat

Mac:
    source venv/bin/activate

Then type:
    python -m pip install -r requirements.txt

STEP 4 - START THE WEBSITE
Type:
    python app.py

You should see a local address, usually http://127.0.0.1:5000
Hold Ctrl and click the address, or copy it into Chrome.

STEP 5 - ADMIN LOGIN
Username: admin
Password: admin1234

These are local starter credentials. Change them before using this beyond your own computer.
For a custom admin account, set ADMIN_USERNAME and ADMIN_PASSWORD environment variables before the first run.
The default admin is created only when the database is first initialized.

STEP 6 - ADD MUSIC
1. Log in as admin.
2. In the Admin Dashboard, use "Add a raga recording".
3. Enter the raga details.
4. Upload a recording in MP3, WAV, OGG or M4A format.
5. Use recordings that you have permission to use. For the assignment, each excerpt should be at least 3 minutes and preferably include Alaap and Gat.

STEP 7 - TEST AS A PARTICIPANT
1. Log out from admin.
2. Register a test participant.
3. Log in as that participant.
4. Choose a raga with an uploaded audio file.
5. Play the audio for at least 60 seconds.
6. The emotion form unlocks.
7. Rate all nine emotions and submit.
8. Log back in as admin to see the annotation and export CSV.

STEP 8 - STOP THE WEBSITE
In the terminal where Flask is running, press Ctrl + C.

PROJECT FILES
app.py                  Flask backend and database logic
templates/               HTML pages
static/css/style.css     Website design
static/js/player.js      Listening timer and progress updates
static/audio/            Uploaded raga recordings
raga_emotion.db          Created automatically on first run

TROUBLESHOOTING
- If "python is not recognized", reinstall Python and tick Add Python to PATH.
- If port 5000 is busy, close the other Flask app or restart your computer.
- If the emotion form stays locked, make sure the audio is actually playing and wait for 60 seconds.
- If a raga has no audio, log in as admin and upload one.
- Keep the terminal open while using the local website.
