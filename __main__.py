from dotenv import load_dotenv

# Loads the variables of environments in the .env file
# of the current directory.
load_dotenv()

from chatbot import bot

if __name__ == "__main__":
    bot.polling()

