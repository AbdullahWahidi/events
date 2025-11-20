from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import cloudscraper
from bs4 import BeautifulSoup
import os
# import pandas as pd
from datetime import time, timezone
async def data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # default time range
    time_ = context.user_data.get("time_", "")

    scraper = cloudscraper.create_scraper()
    url = f'https://www.forexfactory.com/calendar?{time_}'
    response = scraper.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    impact_map = {
        "icon--ff-impact-yel": "Low",
        "icon--ff-impact-ora": "Medium",
        "icon--ff-impact-red": "High",
    }

    events = []
    rows = soup.select("tr.calendar__row")
    current_date = None

    for row in rows:
        date_cell = row.select_one(".calendar__cell.calendar__date .date")
        if date_cell:
            current_date = date_cell.get_text(strip=True)

        time = row.select_one(".calendar__time")
        currency = row.select_one(".calendar__currency")
        impact_icon = row.select_one(".calendar__impact span")
        actual = row.select_one(".calendar__actual")
        event_name = row.select_one(".calendar__event-title")
        forecast = row.select_one(".calendar__forecast")
        previous = row.select_one(".calendar__previous")

        if not (currency and event_name and impact_icon):
            continue

        currency_text = currency.text.strip()
        impact_class = impact_icon["class"][-1]
        impact_level = impact_map.get(impact_class, "Unknown")

        if currency_text == "USD" and impact_level in ["Medium", "High"]:
            events.append({
                "Date": current_date,
                "Time": time.text.strip() if time else "—",
                "Currency": currency_text,
                "Impact": impact_level,
                "Actual": actual.text.strip() if actual else "—",
                "Forecast": forecast.text.strip() if forecast else "—",
                "Previous": previous.text.strip() if previous else "—",
                "Event": event_name.text.strip(),
            })

    if not events:
        await update.message.reply_text("No USD Medium/High impact events found.")
        return

    message = "📅 *All listed events*\n\n"
    for e in events:
        message += (
            f"📆 {e['Date']}\n"
            f"🔹 *{e['Event']}* ({e['Impact']} Impact)\n"
            f"⏰ Time: {e['Time']}\n"
            f"📊 Forecast: {e['Forecast']} | Previous: {e['Previous']} | Actual: {e['Actual']}\n"
            "----------------------------------------\n"
        )

    for chunk in [message[i:i+4000] for i in range(0, len(message), 4000)]:
        await update.message.reply_text(chunk, parse_mode="Markdown")


# ✅ week COMMAND
async def tweek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["time_"] = "week=this"   # <-- set your desired time range
    await data(update, context)               # <-- MUST pass update & context

async def lweek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["time_"] = "week=last"   # <-- set your desired time range
    await data(update, context)               # <-- MUST pass update & context\
async def nweek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["time_"] = "week=next"   # <-- set your desired time range
    await data(update, context)               # <-- MUST pass update & context

#day commands
async def tday(update=None, context=None, chat_id=None):
    if chat_id:
        # Create temporary user_data
        temp_context = type("obj", (), {"user_data": {"time_": "day=today"}, "bot": context.bot})

        await data(
            update=type("obj", (), {"message": type("obj", (), {
                "reply_text": lambda text, **kwargs: context.bot.send_message(chat_id=chat_id, text=text, **kwargs)
            })}),
            context=temp_context
        )
        return

    # Normal user call
    context.user_data["time_"] = "day=today"
    await data(update, context)

async def nday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["time_"] = "day=tomorrow"   # <-- set your desired time range
    await data(update, context)               # <-- MUST pass update & context

async def yday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["time_"] = "day=yesterday"   # <-- set your desired time range
    await data(update, context)

async def customdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Please enter a date.\nExample:\n/c nov12.2025 ")
        return

    user_date = f'day={context.args[0]}'   # "2025-11-12"

    context.user_data["time_"] = user_date

    await data(update, context)                # <-- MUST pass update & context

#month commands
async def tmonth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["time_"] = "month=this"   # <-- set your desired time range
    await data(update, context)               # <-- MUST pass update & context

async def lmonth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["time_"] = "month=last"   # <-- set your desired time range
    await data(update, context)               # <-- MUST pass update & context

async def nmonth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["time_"] = "month=next"   # <-- set your desired time range
    await data(update, context)               # <-- MUST pass update & context
chatid= os.getenv("id")
CHAT_ID = chatid   # your group ID

async def daily_tday_job(context: ContextTypes.DEFAULT_TYPE):
    await tday(update=None, context=context, chat_id=CHAT_ID)


TOKEN = os.getenv("TELEGRAM_TOKEN")

# 🚫 Replace this with your new token (revoke the old one!)
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("tweek", tweek))
app.add_handler(CommandHandler("lweek", lweek))
app.add_handler(CommandHandler("nweek", nweek))

app.add_handler(CommandHandler("tday", tday))
app.add_handler(CommandHandler("nday", nday))
app.add_handler(CommandHandler("yday", yday))
app.add_handler(CommandHandler("c", customdate))

app.add_handler(CommandHandler("tmonth", tmonth))
app.add_handler(CommandHandler("nmonth", nmonth))
app.add_handler(CommandHandler("lmonth", lmonth))
app.job_queue.run_daily(
    daily_tday_job,
    time=time(hour=0, minute=5, tzinfo=timezone.utc),
    name="tday_auto"
    )
    
app.run_polling()
