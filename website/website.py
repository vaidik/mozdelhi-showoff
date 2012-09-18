from app import app

try:
    app.config.from_object('settings')
except ImportError:
    import sys
    print >> sys.stderr, "Please create a settings.py with the necessary settings. See settings-sample.py."

import models
import views

if __name__ == '__main__':
    app.run()
