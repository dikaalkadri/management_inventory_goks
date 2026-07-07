import os
from flask import Flask

# Import Blueprints
from modules.eresto.routes import eresto_bp
from modules.stockin.routes import stockin_bp
from modules.sinkronisasi.routes import sinkronisasi_bp
from modules.mass_update.routes import mass_update_bp
from modules.mass_hide.routes import mass_hide_bp

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(eresto_bp)
app.register_blueprint(stockin_bp)
app.register_blueprint(sinkronisasi_bp)
app.register_blueprint(mass_update_bp)
app.register_blueprint(mass_hide_bp)

# Configurations
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB

# Ensure necessary directories exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('data', exist_ok=True)

if __name__ == '__main__':
    # Run the Flask app on localhost, port 5000
    app.run(host='0.0.0.0', port=5000, debug=False)