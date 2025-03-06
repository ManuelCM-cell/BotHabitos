import logging
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

# Configuración del registro
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Archivo JSON para almacenar hábitos
HABITS_FILE = "habits.json"

# Cargar hábitos desde el archivo JSON
def load_habits():
    try:
        with open(HABITS_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Guardar hábitos en el archivo JSON
def save_habits():
    with open(HABITS_FILE, "w") as file:
        json.dump(user_habits, file)

# Diccionario de hábitos cargados desde el JSON
user_habits = load_habits()

# Configuración del programador
scheduler = BackgroundScheduler()
scheduler.start()

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy tu bot para el control de hábitos. 😊\n"
        "Usa los siguientes comandos para interactuar conmigo:\n\n"
        "🔹 /add_habit [hábito] - Añade un nuevo hábito.\n"
        "🔹 /list_habits - Muestra todos tus hábitos.\n"
        "🔹 /delete_habit [número] - Elimina un hábito.\n"
        "🔹 /complete_habit [número] - Marca un hábito como completado.\n"
        "🔹 /set_reminder [número] [hora] - Configura un recordatorio.\n"
        "🔹 /progress_report - Muestra tu progreso."
    )

# Comando /add_habit
async def add_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    habit = " ".join(context.args)
    if not habit:
        await update.message.reply_text("⚠️ Escribe el nombre del hábito.")
        return
    if user_id not in user_habits:
        user_habits[user_id] = []
    user_habits[user_id].append({"name": habit, "completed": False})
    save_habits()
    await update.message.reply_text(f"✅ Hábito '{habit}' añadido.")

# Comando /list_habits
async def list_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    habits = user_habits.get(user_id, [])
    if not habits:
        await update.message.reply_text("📋 No tienes hábitos registrados.")
    else:
        message = "\n".join([f"{i+1}. {'✅' if h['completed'] else '❌'} {h['name']}" for i, h in enumerate(habits)])
        await update.message.reply_text(f"📋 Tus hábitos:\n\n{message}")

# Comando /delete_habit
async def delete_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    try:
        habit_index = int(context.args[0]) - 1
        if 0 <= habit_index < len(user_habits.get(user_id, [])):
            removed_habit = user_habits[user_id].pop(habit_index)
            save_habits()
            await update.message.reply_text(f"🗑️ Hábito '{removed_habit['name']}' eliminado.")
        else:
            await update.message.reply_text("⚠️ Número inválido.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Debes proporcionar el número del hábito a eliminar.")

# Comando /complete_habit
async def complete_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    try:
        habit_index = int(context.args[0]) - 1
        if 0 <= habit_index < len(user_habits.get(user_id, [])):
            user_habits[user_id][habit_index]["completed"] = True
            save_habits()
            await update.message.reply_text("🎉 Hábito completado. ✅")
        else:
            await update.message.reply_text("⚠️ Número inválido.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Debes proporcionar el número del hábito a completar.")

# Comando /set_reminder
async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    try:
        habit_index, time = int(context.args[0]) - 1, context.args[1]
        if 0 <= habit_index < len(user_habits.get(user_id, [])):
            hour, minute = map(int, time.split(':'))
            scheduler.add_job(
                send_reminder, 'cron', hour=hour, minute=minute, args=[update, habit_index], id=f"{user_id}_{habit_index}", replace_existing=True
            )
            await update.message.reply_text("⏰ Recordatorio configurado.")
        else:
            await update.message.reply_text("⚠️ Número inválido.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Uso: /set_reminder [número] [hora(HH:MM)]")

async def send_reminder(update: Update, habit_index: int):
    user_id = str(update.message.from_user.id)
    habit = user_habits.get(user_id, [])[habit_index]["name"]
    await update.message.reply_text(f"🔔 ¡Recuerda tu hábito: {habit}!")

# Comando /progress_report
async def progress_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    habits = user_habits.get(user_id, [])
    completed = sum(1 for h in habits if h["completed"])
    total = len(habits)
    progress = (completed / total) * 100 if total else 0
    await update.message.reply_text(f"📊 Progreso: {progress:.2f}% ({completed}/{total}) hábitos completados.")

# Función principal
def main():
    application = Application.builder().token("8042463241:AAG_sBJ-AtJXO6NfPEgiRPXX5G6GiAmCX7c").build()
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
