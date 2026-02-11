# Changelog

All notable changes to the Kids Story Bot project will be documented in this file.

## [2.0.0] - 2026-02-12

### 🚀 Major Changes

#### OpenRouter API Integration
- **Migrated from OpenAI to OpenRouter** for cost-effective AI model access
- **Vision Model**: Switched to `google/gemini-2.0-flash-lite-001` ($0.075/1M tokens)
- **Image Generation**: Now using `google/gemini-2.5-flash-image` ($0.10/1M tokens)
- **Cost Savings**: ~90% reduction in API costs while maintaining quality

#### Enhanced Character Accuracy
- **Extreme Detail Analysis**: Upgraded character description prompt to capture:
  - Face shape and structure
  - Eye color, shape, and expression
  - Eyebrow shape and thickness
  - Nose and mouth characteristics
  - Hair color, texture, length, and exact style
  - Skin tone (very specific)
  - Distinctive features (dimples, freckles, etc.)
- **Increased Token Limit**: From 150 to 250 tokens for detailed descriptions
- **Result**: AI-generated characters now look exactly like the child's photo

#### Watercolor & Colored Pencil Style
- **New Artistic Direction**: Replaced crayon style with soft watercolor and colored pencil aesthetic
- **Gentle Pastel Palette**: Soft yellows, blues, and pinks
- **Premium Feel**: Hand-drawn, professional children's book quality

### ✨ New Features

#### Refined Cover Page Layout
- **Circular Hero Frame**: Child's portrait in an artistic circular frame
- **Correct Title Format**: "بطل الـ[Value]" with proper Arabic article
- **Optimized Layout**:
  - Title at top (80pt font)
  - Circular illustration in center (650x650px)
  - Child's name at bottom (65pt font)
- **Soft Border**: Colored pencil-style border around circular frame

#### 6-Panel Grid Storyboard
- **New Layout**: 3-row × 2-column grid (previously 3×2)
- **Specialized Cover Panel**: Panel 1 with circular photo, title, and name
- **Story Panels**: Panels 2-6 with hand-drawn frames and dedicated text areas
- **CLI Support**: Generate storyboards via command line

#### Mobile-Friendly PDFs
- **Square Aspect Ratio**: 210×210mm (prevents image stretching)
- **Enhanced Readability**: Increased font sizes
  - Story text: 50pt (up from 35pt)
  - Cover text: 70-80pt (up from 50pt)
- **Perfect for Phones**: Optimized for mobile viewing

### 🔧 Technical Improvements

#### Code Changes

**openai_service.py**:
```diff
- client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
+ api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or "not_set"
+ client = OpenAI(
+     base_url="https://openrouter.ai/api/v1",
+     api_key=api_key
+ )

- model="gpt-4o-mini"
+ model="google/gemini-2.0-flash-lite-001"

- model="dall-e-3"
+ model="google/gemini-2.5-flash-image"
+ # Via Chat Completions API with modalities=["image"]
```

**image_utils.py**:
- Added `create_cover_page()` with circular cropping
- Added `create_grid_cover_panel()` for storyboard covers
- Added `create_story_panel()` for framed story scenes
- Enhanced Arabic text rendering with larger fonts

**pdf_utils.py**:
```diff
- pdf = FPDF()
- pdf.image(img_path, x=0, y=0, w=210, h=297)  # A4 stretched
+ pdf = FPDF(unit='mm', format=(210, 210))  # Square
+ pdf.image(img_path, x=0, y=0, w=210, h=210)  # No stretching
```

**main.py**:
- Updated cover generation to use circular layout
- Fixed title format to "بطل الـ[Value]"
- Improved character description workflow

### 🐛 Bug Fixes

#### Base64 Image Handling
- **Issue**: `InvalidSchema` error on Railway when processing base64 images
- **Fix**: Updated `image_utils.py` to detect and decode data URIs directly
- **Impact**: Bot no longer crashes on Railway deployment

#### Arabic Text Rendering
- **Issue**: Arabic text not displaying correctly (corrupted font)
- **Fix**: Downloaded valid `Amiri-Regular.ttf` from Google Fonts
- **Impact**: Proper RTL text rendering with correct character joining

#### Image Generation 404 Error
- **Issue**: "No endpoints found that support the requested output modalities: image"
- **Fix**: Switched to `google/gemini-2.5-flash-image` which explicitly supports image modality
- **Impact**: Reliable image generation on OpenRouter

### 📝 Documentation

- **README.md**: Complete rewrite with comprehensive documentation
- **CHANGELOG.md**: This file - tracking all changes
- **walkthrough.md**: Updated with technical migration details
- **task.md**: Maintained throughout development

## [1.0.0] - 2026-02-10

### Initial Release

- Facebook Messenger bot integration
- Story generation with OpenAI GPT-4o-mini
- Image generation with DALL-E 3
- PDF creation with Arabic text support
- Age-appropriate stories (1-5 years)
- Four moral values: Courage, Honesty, Cooperation, Respect
- Basic storyboard generation

---

## Migration Guide: OpenAI → OpenRouter

### Environment Variables

**Before**:
```bash
export OPENAI_API_KEY="sk-..."
```

**After**:
```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
# OPENAI_API_KEY still works as fallback
```

### API Costs Comparison

| Service | OpenAI | OpenRouter | Savings |
|---------|--------|------------|---------|
| Vision (GPT-4o-mini) | $0.15/1M | $0.075/1M (Gemini 2.0 Flash Lite) | 50% |
| Images (DALL-E 3) | $0.04/image | $0.10/1M tokens (Gemini 2.5 Flash) | ~90% |

### Code Migration

If you're upgrading from v1.0.0, simply:
1. Add `OPENROUTER_API_KEY` to your environment
2. Pull latest code from GitHub
3. Redeploy to Railway/Vercel

No code changes needed - backward compatible!

---

## Roadmap

### Planned Features
- [ ] Multi-language support (English, French)
- [ ] Custom story templates
- [ ] Voice narration
- [ ] Interactive story choices
- [ ] Parent dashboard
- [ ] Story sharing via social media

### Under Consideration
- Video story generation
- Augmented reality features
- Print-on-demand integration
- Mobile app version

---

**Legend**:
- 🚀 Major Changes
- ✨ New Features
- 🔧 Technical Improvements
- 🐛 Bug Fixes
- 📝 Documentation
