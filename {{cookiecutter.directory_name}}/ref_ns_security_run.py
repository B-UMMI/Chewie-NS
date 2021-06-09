import os
from app import create_app

# Port variable to run the server on.
#PORT = os.environ.get('PORT')

app = create_app()
app.app_context().push()
# from app.models import User

if __name__ == "__main__":
    app.run(threaded=True)
