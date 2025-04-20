import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackContext,
)
from config import BOT_TOKEN
from db import get_user_habits, save_user_habits

# Logs
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy tu bot de hábitos. Comandos:\n"
        "/add_habit [hábito]\n"
        "/list_habits\n"
        "/delete_habit [número]\n"
        "/complete_habit [número]\n"
        "/set_reminder [número] [hora]\n"
        "/progress_report"
    )

# /add_habit
async def add_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    habit = " ".join(context.args)

    if not habit:
        await update.message.reply_text("⚠️ Escribe el hábito después del comando.")
        return

    habits = get_user_habits(user_id)
    habits.append({
        "name": habit,
        "completed": False,
        "added": datetime.now().isoformat()
    })
    save_user_habits(user_id, habits)
    await update.message.reply_text(f"✅ Hábito '{habit}' añadido.")

# /list_habits
async def list_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    habits = get_user_habits(user_id)

    if not habits:
        await update.message.reply_text("📋 No tienes hábitos registrados.")
        return

    texto = "\n".join([f"{i+1}. {'✅' if h['completed'] else '❌'} {h['name']}" for i, h in enumerate(habits)])
    await update.message.reply_text(f"📋 Tus hábitos:\n\n{texto}")

# /delete_habit
async def delete_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        index = int(context.args[0]) - 1
        habits = get_user_habits(user_id)
        if 0 <= index < len(habits):
            eliminado = habits.pop(index)
            save_user_habits(user_id, habits)
            await update.message.reply_text(f"🗑️ Hábito '{eliminado['name']}' eliminado.")
        else:
            await update.message.reply_text("⚠️ Índice inválido.")
    except:
        await update.message.reply_text("⚠️ Usa: /delete_habit [número]")

# /complete_habit
async def complete_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        index = int(context.args[0]) - 1
        habits = get_user_habits(user_id)
        if 0 <= index < len(habits):
            habits[index]["completed"] = True
            save_user_habits(user_id, habits)
            await update.message.reply_text(f"✅ Hábito '{habits[index]['name']}' completado.")
        else:
            await update.message.reply_text("⚠️ Índice inválido.")
    except:
        await update.message.reply_text("⚠️ Usa: /complete_habit [número]")

# /set_reminder
async def set_reminder(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    try:
        index = int(context.args[0]) - 1
        time_str = context.args[1]
        hour, minute = map(int, time_str.split(":"))
        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target < now:
            target += timedelta(days=1)

        habits = get_user_habits(user_id)
        habit_name = habits[index]["name"]

        context.job_queue.run_once(
            send_reminder,
            when=(target - now).total_seconds(),
            chat_id=update.message.chat_id,
            data={"habit_name": habit_name}
        )
        await update.message.reply_text(f"⏰ Recordatorio para '{habit_name}' a las {time_str}.")
    except:
        await update.message.reply_text("⚠️ Usa: /set_reminder [número] [hora]")

# función de recordatorio
async def send_reminder(context: CallbackContext):
    job = context.job
    await context.bot.send_message(
        job.chat_id,
        text=f"🔔 Recordatorio: No olvides hacer '{job.data['habit_name']}'"
    )

# /progress_report
async def progress_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    habits = get_user_habits(user_id)
    if not habits:
        await update.message.reply_text("📊 No tienes hábitos registrados.")
        return

    completed = sum(1 for h in habits if h["completed"])
    total = len(habits)
    porcentaje = (completed / total) * 100
    detalles = "\n".join([f"{h['name']}: {'✅' if h['completed'] else '❌'}" for h in habits])

    await update.message.reply_text(
        f"📊 Progreso: {completed}/{total} completados\n"
        f"Progreso total: {porcentaje:.2f}%\n\n{detalles}"
    )

# main
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_habit", add_habit))
    application.add_handler(CommandHandler("list_habits", list_habits))
    application.add_handler(CommandHandler("delete_habit", delete_habit))
    application.add_handler(CommandHandler("complete_habit", complete_habit))
    application.add_handler(CommandHandler("set_reminder", set_reminder))
    application.add_handler(CommandHandler("progress_report", progress_report))

    application.run_polling()

if __name__ == "__main__":
    main()
