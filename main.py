from website import create_app
from datetime import timedelta

app = create_app()
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

if __name__ == '__main__':
    app.run()