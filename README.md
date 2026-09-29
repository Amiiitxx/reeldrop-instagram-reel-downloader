# 🎬 ReelDrop — Instagram Reel & Post Downloader

A simple and modern **Flask-based Instagram Reel & Post Downloader** that lets you download publicly accessible Instagram media in the highest quality available from the source.

<p align="center">
  <strong>Fast • Simple • High Quality</strong>
</p>

---

## ✨ Features

* 🎥 Download Instagram Reels
* 🖼️ Download Instagram Posts
* 📺 Highest available media quality
* ⚡ Fast URL-based downloading
* 🎨 Clean and responsive web interface
* 📱 Mobile-friendly design
* 📦 MP4 output
* 🚫 No unnecessary steps
* 🐍 Built with Python & Flask

---

## 🖥️ Preview

### Download Flow

```text
┌─────────────────────────────────────────────┐
│                                             │
│              ReelDrop                       │
│                                             │
│      Download Instagram Reels & Posts       │
│                                             │
│  ┌─────────────────────────┐ ┌───────────┐  │
│  │ Paste Instagram URL...  │ │ Download  │  │
│  └─────────────────────────┘ └───────────┘  │
│                                             │
│        ⚡ Fast   •   HD   •   Simple       │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Technology   | Purpose                |
| ------------ | ---------------------- |
| 🐍 Python    | Backend programming    |
| 🌐 Flask     | Web framework          |
| 📥 yt-dlp    | Media downloading      |
| 🎨 HTML5     | Page structure         |
| 💅 CSS3      | UI & responsive design |
| ⚡ JavaScript | Frontend interactions  |

---

## 📁 Project Structure

```text
reeldrop-instagram-reel-downloader/
│
├── app.py
├── requirements.txt
├── README.txt
│
├── templates/
│   └── index.html
│
├── static/
│   └── style.css
│
└── downloads/
    └── .gitkeep
```

> Downloaded media should remain local and should not be committed to the repository.

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/Amiiitxx/reeldrop-instagram-reel-downloader.git
```

### 2. Open the project

```bash
cd reeldrop-instagram-reel-downloader
```

### 3. Create a virtual environment

Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the application

```bash
python app.py
```

### 6. Open in browser

```text
http://127.0.0.1:5000
```

---

## 📥 How to Use

### Step 1

Open ReelDrop in your browser.

### Step 2

Copy a publicly accessible Instagram Reel or Post URL.

Example:

```text
https://www.instagram.com/reel/XXXXXXXXXXX/
```

### Step 3

Paste the URL into the input box.

### Step 4

Click:

```text
Download HD
```

### Step 5

After processing, click:

```text
Save MP4
```

The downloaded file will be saved inside the local `downloads/` directory.

---

## 🎯 Supported URLs

ReelDrop is designed for publicly accessible Instagram URLs such as:

```text
Instagram Reel
https://www.instagram.com/reel/...

Instagram Post
https://www.instagram.com/p/...

Instagram Video
https://www.instagram.com/tv/...
```

---

## ⚙️ How It Works

```text
Instagram URL
      │
      ▼
   Flask App
      │
      ▼
    yt-dlp
      │
      ▼
Highest Available Media
      │
      ▼
     MP4
      │
      ▼
 Local Downloads Folder
```

---

## 🔒 Privacy

ReelDrop does not require you to create an account on the application.

The application processes the URL and stores the downloaded media locally on the machine running the Flask server.

---

## ⚠️ Disclaimer

ReelDrop is intended for downloading **publicly accessible content that you have permission to download**.

Users are responsible for respecting:

* Instagram's Terms of Use
* Copyright laws
* Content creator rights
* Applicable local laws and regulations

Do not use this project to download or redistribute content without the necessary rights or permission.

---

## 🔮 Future Improvements

Planned improvements may include:

* [ ] Download progress indicator
* [ ] Thumbnail preview
* [ ] Video information before downloading
* [ ] Automatic file cleanup
* [ ] Better error messages
* [ ] Download history
* [ ] Audio-only downloads
* [ ] Dark/Light theme
* [ ] Docker support
* [ ] Cloud deployment

---

## 🤝 Contributing

Contributions are welcome.

1. Fork the repository
2. Create a new branch

```bash
git checkout -b feature/new-feature
```

3. Make your changes
4. Commit your changes

```bash
git commit -m "Add new feature"
```

5. Push the branch

```bash
git push origin feature/new-feature
```

6. Open a Pull Request

---

## 📄 License

This project is intended for educational and personal use.

---

## 👨‍💻 Author

**Amith**

GitHub: **[@Amiiitxx](https://github.com/Amiiitxx)**

---

<p align="center">
  Made with ❤️ using Python & Flask
</p>
