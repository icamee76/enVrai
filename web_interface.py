from flask import Flask, render_template, request, jsonify, send_file
import json
import os
from pathlib import Path
import threading

def create_app(tic_detector_app):
    app = Flask(__name__)
    app.tic_detector = tic_detector_app
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/api/config')
    def get_config():
        return jsonify(app.tic_detector.config)
    
    @app.route('/api/config', methods=['POST'])
    def update_config():
        try:
            new_config = request.json
            app.tic_detector.config.update(new_config)
            app.tic_detector.save_config()
            
            # Recharger le modèle Whisper si nécessaire
            if 'whisper_model' in new_config:
                app.tic_detector.load_whisper_model()
            
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/expressions')
    def get_expressions():
        return jsonify(app.tic_detector.config['expressions'])
    
    @app.route('/api/expressions/<expr_key>', methods=['PUT'])
    def update_expression(expr_key):
        try:
            expr_data = request.json
            app.tic_detector.config['expressions'][expr_key] = expr_data
            app.tic_detector.save_config()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/expressions/<expr_key>', methods=['DELETE'])
    def delete_expression(expr_key):
        try:
            if expr_key in app.tic_detector.config['expressions']:
                del app.tic_detector.config['expressions'][expr_key]
                app.tic_detector.save_config()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/expressions', methods=['POST'])
    def add_expression():
        try:
            expr_data = request.json
            expr_key = expr_data.get('key')
            if expr_key:
                app.tic_detector.config['expressions'][expr_key] = {
                    'name': expr_data.get('name', ''),
                    'patterns': expr_data.get('patterns', []),
                    'action': expr_data.get('action', 'mp3'),
                    'mp3_file': expr_data.get('mp3_file', ''),
                    'enabled': expr_data.get('enabled', True)
                }
                app.tic_detector.save_config()
                return jsonify({'success': True})
            return jsonify({'success': False, 'error': 'Clé manquante'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/stats')
    def get_stats():
        return jsonify(app.tic_detector.get_stats())
    
    @app.route('/api/start')
    def start_detection():
        if not app.tic_detector.is_recording:
            threading.Thread(target=app.tic_detector.start_listening, daemon=True).start()
        return jsonify({'success': True, 'recording': app.tic_detector.is_recording})
    
    @app.route('/api/stop')
    def stop_detection():
        app.tic_detector.stop_listening()
        return jsonify({'success': True, 'recording': app.tic_detector.is_recording})
    
    @app.route('/api/mp3_files')
    def get_mp3_files():
        mp3_files = []
        mp3_dir = Path('mp3')
        if mp3_dir.exists():
            mp3_files = [f.name for f in mp3_dir.glob('*.mp3')]
        return jsonify(mp3_files)
    
    @app.route('/api/play_mp3/<filename>')
    def play_mp3(filename):
        try:
            success = app.tic_detector.play_mp3(filename)
            return jsonify({'success': success})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/play_recording/<filename>')
    def play_recording(filename):
        try:
            success = app.tic_detector.replay_audio(filename)
            return jsonify({'success': success})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/download/recording/<filename>')
    def download_recording(filename):
        try:
            file_path = Path('recordings') / filename
            if file_path.exists():
                return send_file(file_path, as_attachment=True)
            return jsonify({'error': 'Fichier non trouvé'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app