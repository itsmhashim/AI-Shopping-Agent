# 🛒 AI Shopping Agent

An AI-powered shopping automation system built with `Python`, designed to search, select, and checkout grocery items from Al-Fatah.pk using natural language inputs, Telegram interaction, and real-time browser automation.

___

## ✨ Features

- 🔎 **Smart Product Search**: Searches for products based on user requests and displays top results with images.
- 📩 **Telegram Integration**: Select products, confirm orders, and interact fully through Telegram inline buttons.
- ➕ **Quantity Management**: Automatically adds the correct quantity of selected products to the cart.
- 🛒 **Order Confirmation**: Summarizes cart and waits for user confirmation before proceeding.
- 🛠️ **Checkout Automation**: Navigates through checkout steps, filling address and contact details automatically.
- 🧠 **Model-Assisted Parsing**: Uses `DeepSeek`, `Qwen`, and `Gemini` APIs to parse and structure user inputs intelligently.

___

## ⚙️ Tech Stack

| Layer             | Tech                                               |
|-------------------|----------------------------------------------------|
| LLM APIs           | `DeepSeek V3`, `Qwen: QwQ 32B`, `Gemini 2.0 Flash` |
| Browser Automation | `Playwright` (Async)                               |
| Backend Server    | `FastAPI` (Telegram Webhook)                       |
| Messaging         | `Telegram Bot API`                                 |
| Orchestration     | `AsyncIO`                                          |

___

## ⛏️ Core Workflow

1. **Start Interaction:** User sends grocery items through Telegram.
2. **Parse & Search:** AI models parse items, and Playwright searches the online store.
3. **Select Product:** Bot sends top 3 matching products with images and inline selection buttons.
4. **Add to Cart:** Upon user selection, correct quantities are added.
5. **Order Summary:** Bot sends a summary and asks for confirmation.
6. **Checkout:** If confirmed, the bot proceeds to checkout, fills dummy address and contact fields, and reaches payment page.

___


## 🖥️ Demo & Showcase
Demo video and showcase coming soon!

---

## 📜 License
This project is licensed under the `MIT License`. See the [LICENSE](./LICENSE) file for details.

---

## 🤝 Contributing
Contributions are welcome! Feel free to fork this repo, create a new branch, and submit a Pull Request.

---

## 📬 Contact
📧 [muhammad.hashim40@ee.ceme.edu.pk](mailto:muhammad.hashim40@ee.ceme.edu.pk)

___


