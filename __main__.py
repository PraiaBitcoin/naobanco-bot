from dotenv import load_dotenv

# Loads the variables of environments in the .env file
# of the current directory.
load_dotenv()

import app

if __name__ == "__main__":
    app.start()