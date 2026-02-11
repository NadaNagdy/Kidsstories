# 📚 Kids Story Bot - Personalized Arabic Storybooks

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

A Facebook Messenger chatbot that generates personalized Arabic children's storybooks with AI-powered illustrations. Each story features the child as the hero, teaching important values like courage, honesty, cooperation, and respect.

## ✨ Features

### 🎨 AI-Powered Story Generation
- **Personalized Stories**: Child becomes the hero of their own story
- **Character Consistency**: AI analyzes the child's photo in extreme detail to ensure illustrations look exactly like them
- **Watercolor & Colored Pencil Style**: Soft, premium hand-drawn aesthetic
- **Age-Appropriate Content**: Stories tailored for ages 1-5 years
- **Moral Values**: Stories teach courage (الشجاعة), honesty (الصدق), cooperation (التعاون), and respect (الاحترام)

### 📖 Professional Cover Pages
- **Circular Hero Frame**: Child's portrait in an artistic circular frame
- **Arabic Title**: "بطل الـ[Value]" (Hero of [Value])
- **Mobile-Optimized**: Square format (1:1) perfect for phones and tablets

### 📱 Mobile-Friendly PDFs
- **Square Aspect Ratio**: 210x210mm pages prevent image stretching
- **Large Fonts**: Enhanced readability on small screens
- **High-Quality Text**: Proper Arabic text rendering with Amiri font

### 🎭 6-Panel Grid Storyboards
- **3-Row × 2-Column Layout**: Professional storyboard format
- **Specialized Cover Panel**: Circular photo with title and name
- **Story Panels**: Hand-drawn frames with dedicated text areas
- **Consistent Character**: Same appearance across all panels

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenRouter API Key ([Get one here](https://openrouter.ai))
- Facebook Page Access Token
- Railway account (for deployment)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/NadaNagdy/Kidsstories.git
   cd Kidsstories
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   export OPENROUTER_API_KEY="your_openrouter_api_key"
   export VERIFY_TOKEN="your_verify_token"
   export PAGE_ACCESS_TOKEN="your_facebook_page_token"
   ```

4. **Run locally**:
   ```bash
   uvicorn main:app --reload
   ```

5. **Expose to internet** (for Facebook webhook):
   ```bash
   ngrok http 8000
   ```
   Use the `https` URL in your Facebook App webhook settings: `https://<ngrok-id>.ngrok.io/webhook`

## 🎯 Usage

### Via Facebook Messenger

1. Send **"Start"** to the bot
2. Enter your child's name when prompted
3. Upload a clear photo of your child's face
4. Select the child's age group (1-2, 2-3, 3-4, or 4-5 years)
5. Choose a moral value for the story
6. Receive your personalized PDF storybook!

### Generate Storyboards (CLI)

Create 6-panel storyboards directly from the command line:

```bash
python3 create_storyboard.py "اسم الطفل" "الشجاعة" "path/to/photo.jpg"
```

**Parameters**:
- `"اسم الطفل"`: Child's name in Arabic
- `"الشجاعة"`: Value (الشجاعة, الصدق, التعاون, الاحترام)
- `"path/to/photo.jpg"`: Path to child's photo

**Output**: `storyboard_output/storyboard_اسم_الطفل.png`

## 🤖 AI Models & Technology

### OpenRouter Integration
The bot uses [OpenRouter.ai](https://openrouter.ai) for cost-effective access to premium AI models:

- **Vision Model**: `google/gemini-2.0-flash-lite-001` ($0.075/1M tokens)
  - Analyzes child photos in extreme detail
  - Captures face shape, eye color, hair texture, skin tone, distinctive features
  
- **Image Generation**: `google/gemini-2.5-flash-image` ($0.10/1M tokens)
  - Creates high-quality watercolor-style illustrations
  - Ensures character consistency across all pages

### Character Accuracy
The AI analyzes photos with extreme precision:
- Face shape and structure
- Eye color, shape, and expression
- Eyebrow shape and thickness
- Nose and mouth characteristics
- Hair color, texture, length, and style
- Skin tone (very specific)
- Distinctive features (dimples, freckles, etc.)

## 📂 Project Structure

```
Kidsstories/
├── main.py                 # FastAPI server & Messenger bot logic
├── openai_service.py       # OpenRouter API integration
├── story.py                # Story generation logic
├── image_utils.py          # Image processing & text overlay
├── pdf_utils.py            # PDF generation
├── messenger_api.py        # Facebook Messenger API
├── create_storyboard.py    # CLI storyboard generator
├── stories_content/        # Story templates by value
│   ├── الشجاعة.json
│   ├── الصدق.json
│   ├── التعاون.json
│   └── الاحترام.json
└── fonts/
    └── Amiri-Regular.ttf   # Arabic font
```

## 🎨 Story Content

Each moral value has age-appropriate stories:

- **الشجاعة (Courage)**: Overcoming fears, trying new things
- **الصدق (Honesty)**: Telling the truth, being trustworthy
- **التعاون (Cooperation)**: Working together, helping others
- **الاحترام (Respect)**: Kindness, consideration for others

Stories are stored in `stories_content/` as JSON files with:
- Age-specific content (1-2, 2-3, 3-4, 4-5 years)
- Scene descriptions for AI illustration
- Arabic text with `{child_name}` placeholders

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key | ✅ |
| `VERIFY_TOKEN` | Facebook webhook verification token | ✅ |
| `PAGE_ACCESS_TOKEN` | Facebook Page access token | ✅ |
| `PORT` | Server port (default: 8000) | ❌ |

### Customization

**Change Illustration Style**: Edit `openai_service.py` line 55:
```python
style_prompt = "Your custom style description here"
```

**Modify Cover Layout**: Edit `image_utils.py` function `create_cover_page()`

**Add New Stories**: Create JSON files in `stories_content/` following the existing format

## 🚢 Deployment

### Deploy to Railway

1. Click the Railway button at the top of this README
2. Add environment variables in Railway dashboard
3. Deploy!

### Deploy to Vercel/Heroku

Similar process - add environment variables and deploy. Make sure to:
- Set the correct `PORT` variable
- Configure webhook URL in Facebook App settings

## 🐛 Troubleshooting

### Common Issues

**"InvalidSchema" Error**:
- Fixed in latest version - handles both URLs and base64 images

**Arabic Text Not Rendering**:
- Ensure `fonts/Amiri-Regular.ttf` exists
- Check font file is valid (not HTML placeholder)

**Character Doesn't Look Like Photo**:
- Use a clear, well-lit, front-facing photo
- Ensure face is visible and not obscured
- Latest version uses enhanced character analysis

**PDF Images Stretched**:
- Fixed in latest version - uses square 210x210mm format

## 📝 License

MIT License - feel free to use and modify!

## 🙏 Acknowledgments

- **OpenRouter** for cost-effective AI model access
- **Google Gemini** for high-quality vision and image generation
- **Amiri Font** for beautiful Arabic typography

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

Made with ❤️ for children's education and imagination
