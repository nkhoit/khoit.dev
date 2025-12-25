# khoit.dev

Personal website for Nguyen Khoi Tran - Senior Software Engineer

## 🚀 Tech Stack

- HTML5
- CSS3 (Custom styling with CSS variables)
- Vanilla JavaScript
- Azure Static Web Apps (for deployment)

## 📦 Deployment

This site is configured for automatic deployment to Azure Static Web Apps.

### Setting up Azure Static Web Apps

1. **Create Azure Static Web App:**
   - Go to [Azure Portal](https://portal.azure.com)
   - Click "Create a resource" → Search for "Static Web Apps"
   - Click "Create"

2. **Configure the Static Web App:**
   - **Subscription:** Choose your Azure subscription
   - **Resource Group:** Create new or select existing
   - **Name:** `khoit-dev` (or your preferred name)
   - **Plan type:** Free (perfect for personal sites)
   - **Region:** Choose closest to your target audience
   - **Source:** GitHub
   - **GitHub Account:** Authorize and select `nkhoit/khoit.dev`
   - **Branch:** `main`
   - **Build Details:**
     - Build Presets: `Custom`
     - App location: `/` (root)
     - Api location: (leave empty)
     - Output location: (leave empty)

3. **Deploy:**
   - Click "Review + Create" → "Create"
   - Azure will automatically create a GitHub Actions workflow in `.github/workflows/`
   - Every push to `main` branch will trigger automatic deployment

4. **Custom Domain (Optional):**
   - In Azure Portal, go to your Static Web App
   - Navigate to "Custom domains"
   - Add `khoit.dev` as custom domain
   - Follow DNS configuration instructions

## 🛠️ Local Development

Simply open `index.html` in your browser, or use a local server:

```bash
# Using Python
python -m http.server 8000

# Using Node.js (http-server)
npx http-server

# Using PHP
php -S localhost:8000
```

Then visit `http://localhost:8000`

## 📁 Project Structure

```
khoit.dev/
├── index.html              # Main HTML file
├── styles.css              # Styling
├── script.js               # JavaScript functionality
├── staticwebapp.config.json # Azure Static Web Apps configuration
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## 🎨 Features

- **Responsive Design:** Works on all devices (mobile, tablet, desktop)
- **Smooth Scrolling:** Navigation with smooth scroll animations
- **Modern UI:** Clean, professional design with hover effects
- **Performance:** Lightweight, no frameworks needed
- **SEO Friendly:** Proper meta tags and semantic HTML
- **Accessibility:** ARIA labels and keyboard navigation support

## 🔧 Customization

### Update Content
Edit `index.html` to update your experience, skills, or contact information.

### Modify Styling
Edit `styles.css` to change colors, fonts, or layout. CSS variables are defined at the top for easy customization:

```css
:root {
    --primary-color: #0066cc;
    --secondary-color: #005bb5;
    /* ... more variables */
}
```

### Add Features
Edit `script.js` to add new interactive features or animations.

## 📝 License

© 2025 Nguyen Khoi Tran. All rights reserved.
