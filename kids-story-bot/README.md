# Kids Story Messenger Bot

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/NadaNagdy/Kidsstories)

A Facebook Messenger Chatbot that generates personalized children's stories and converts them into PDF files.

## Features

-   **Photo Reception**: Receives a photo of the child (stored temporarily in memory).
-   **Interactive Quick Replies**: Asks the user to choose a moral value for the story.
-   **Story Generation**: Creates a short story based on the child's name and selected value.
-   **PDF Creation**: Generates a PDF of the story.
-   **File Delivery**: Sends the PDF back to the user via Messenger.

## Setup

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd kids-story-bot
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Variables**:
    You need to set up the following environment variables (or hardcode them for testing, but NOT recommended for production):
    -   `VERIFY_TOKEN`: A string you define for Facebook Webhook verification.
    -   `PAGE_ACCESS_TOKEN`: The access token for your Facebook Page.

4.  **Run the Server**:
    ```bash
    uvicorn main:app --reload
    ```

5.  **Expose to Internet (using ngrok)**:
    ```bash
    ngrok http 8000
    ```
    Copy the `https` URL from ngrok and paste it into your Meta App Webhook settings with `/webhook` appended (e.g., `https://<ngrok-id>.ngrok.io/webhook`).

## Usage

1.  Send "Start" to the bot.
2.  Upload a photo when prompted.
3.  Choose a value from the Quick Replies.
4.  Receive your personalized story PDF!
