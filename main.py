import whisper
import pyaudio
import wave
import threading
import time
import numpy as np
from collections import deque
import tempfile
import os
import json
import re
from datetime import datetime
import argparse
import sys
import pygame
import uuid
from pathlib import Path

class TicDetectorApp:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.load_config()
        
        # Initialisation
        self.audio = None
        self.model = None
        self.is_recording = False
        self.is_playing = False
        
        # Stockage des enregistrements
        self.recordings_dir = Path("recordings")
        self.recordings_dir.mkdir(exist_ok=True)
        self.mp3_dir = Path("mp3")
        self.mp3_dir.mkdir(exist_ok=True)
        
        # Anti-doublon
        self.last_detections = deque(maxlen=10)
        
        # Statistiques
        self.detection_stats = {expr: 0 for expr in self.config["expressions"]}
        self.session_detections = []
        
        # Initialisation des composants
        pygame.mixer.init()
        
        if not self.init_audio():
            sys.exit(1)
        if not self.load_whisper_model():
            sys.exit(1)
    
    def load_config(self):
        """Charge la configuration depuis le fichier JSON"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            print(f"❌ Fichier de configuration {self.config_file} non trouvé")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Erreur dans le fichier de configuration: {e}")
            sys.exit(1)
    
    def save_config(self):
        """Sauvegarde la configuration"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def init_audio(self):
        """Initialise PyAudio"""
        try:
            self.audio = pyaudio.PyAudio()
            
            # Test du microphone
            test_stream = self.audio.open(
                format=getattr(pyaudio, self.config["audio_config"]["format"]),
                channels=self.config["audio_config"]["channels"],
                rate=self.config["audio_config"]["rate"],
                input=True,
                frames_per_buffer=self.config["audio_config"]["chunk"]
            )
            test_stream.close()
            
            print("✅ Microphone détecté et fonctionnel")
            return True
            
        except Exception as e:
            print(f"❌ Erreur audio: {e}")
            return False
    
    def load_whisper_model(self):
        """Charge le modèle Whisper"""
        try:
            model_size = self.config["whisper_model"]
            print(f"📥 Chargement du modèle Whisper '{model_size}'...")
            self.model = whisper.load_model(model_size)
            print(f"✅ Modèle {model_size} chargé")
            return True
            
        except Exception as e:
            print(f"❌ Erreur Whisper: {e}")
            return False
    
    def save_audio_segment(self, audio_data, detection_info):
        """Sauvegarde un segment audio qui a déclenché une détection"""
        try:
            filename = f"{detection_info['id']}.wav"
            filepath = self.recordings_dir / filename
            
            wf = wave.open(str(filepath), 'wb')
            wf.setnchannels(self.config["audio_config"]["channels"])
            wf.setsampwidth(self.audio.get_sample_size(getattr(pyaudio, self.config["audio_config"]["format"])))
            wf.setframerate(self.config["audio_config"]["rate"])
            wf.writeframes(audio_data)
            wf.close()
            
            detection_info['audio_file'] = filename
            return filename
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde audio: {e}")
            return None
    
    def play_mp3(self, mp3_file):
        """Joue un fichier MP3"""
        try:
            mp3_path = self.mp3_dir / mp3_file
            if mp3_path.exists():
                self.is_playing = True
                pygame.mixer.music.load(str(mp3_path))
                pygame.mixer.music.play()
                
                # Attendre la fin de la lecture
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                self.is_playing = False
                return True
            else:
                print(f"❌ Fichier MP3 non trouvé: {mp3_path}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lecture MP3: {e}")
            self.is_playing = False
            return False
    
    def replay_audio(self, audio_file):
        """Rejoue un enregistrement audio"""
        try:
            audio_path = self.recordings_dir / audio_file
            if audio_path.exists():
                self.is_playing = True
                
                # Lecture avec pygame
                pygame.mixer.music.load(str(audio_path))
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                self.is_playing = False
                return True
            else:
                print(f"❌ Fichier audio non trouvé: {audio_path}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur replay audio: {e}")
            self.is_playing = False
            return False
    
    def is_duplicate_detection(self, expression_key, text):
        """Vérifie si c'est une détection en doublon"""
        current_time = time.time()
        detection_key = f"{expression_key}:{text[:20]}"
        
        for timestamp, key in self.last_detections:
            if key == detection_key and current_time - timestamp < 5:
                return True
        
        self.last_detections.append((current_time, detection_key))
        return False
    
    def detect_expressions(self, text, audio_data):
        """Détecte les expressions dans le texte"""
        if not text or self.is_playing:
            return
            
        text_lower = text.lower()
        
        for expr_key, expr_config in self.config["expressions"].items():
            if not expr_config.get("enabled", True):
                continue
                
            # Vérification des patterns
            total_matches = 0
            for pattern in expr_config["patterns"]:
                matches = re.findall(pattern, text_lower)
                total_matches += len(matches)
            
            if total_matches > 0 and not self.is_duplicate_detection(expr_key, text):
                # Création de l'info de détection
                detection_info = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.now().isoformat(),
                    'expression': expr_config["name"],
                    'expression_key': expr_key,
                    'text': text,
                    'matches': total_matches,
                    'action': expr_config["action"],
                    'mp3_file': expr_config.get("mp3_file")
                }
                
                # Sauvegarde de l'audio
                audio_file = self.save_audio_segment(audio_data, detection_info)
                
                # Mise à jour des statistiques
                self.detection_stats[expr_key] += total_matches
                self.session_detections.append(detection_info)
                
                print(f"🎯 Détection: '{expr_config['name']}' dans '{text}' (Action: {expr_config['action']})")
                
                # Exécution des actions
                threading.Thread(
                    target=self.execute_action,
                    args=(detection_info,),
                    daemon=True
                ).start()
                
                return  # Une seule réaction par segment
    
    def execute_action(self, detection_info):
        """Exécute l'action définie pour la détection"""
        action = detection_info["action"]
        
        try:
            if action == "mp3" and detection_info["mp3_file"]:
                self.play_mp3(detection_info["mp3_file"])
                
            elif action == "replay" and detection_info.get("audio_file"):
                self.replay_audio(detection_info["audio_file"])
                
            elif action == "both":
                # MP3 puis replay
                if detection_info["mp3_file"]:
                    self.play_mp3(detection_info["mp3_file"])
                    time.sleep(0.5)  # Pause entre les deux
                if detection_info.get("audio_file"):
                    self.replay_audio(detection_info["audio_file"])
                    
        except Exception as e:
            print(f"❌ Erreur exécution action: {e}")
    
    def transcribe_audio(self, audio_data):
        """Transcrit l'audio en français"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                wf = wave.open(temp_file.name, 'wb')
                wf.setnchannels(self.config["audio_config"]["channels"])
                wf.setsampwidth(self.audio.get_sample_size(getattr(pyaudio, self.config["audio_config"]["format"])))
                wf.setframerate(self.config["audio_config"]["rate"])
                wf.writeframes(audio_data)
                wf.close()
                
                result = self.model.transcribe(
                    temp_file.name,
                    language="french",
                    fp16=False,
                    verbose=False,
                    condition_on_previous_text=False,
                    temperature=0.0
                )
                text = result["text"].strip()
                
                os.unlink(temp_file.name)
                return text
                
        except Exception as e:
            print(f"❌ Erreur transcription: {e}")
            return ""
    
    def audio_callback(self):
        """Thread d'enregistrement audio"""
        try:
            stream = self.audio.open(
                format=getattr(pyaudio, self.config["audio_config"]["format"]),
                channels=self.config["audio_config"]["channels"],
                rate=self.config["audio_config"]["rate"],
                input=True,
                frames_per_buffer=self.config["audio_config"]["chunk"]
            )
            
            print("🎤 Écoute en cours...")
            
            frames = []
            frame_count = 0
            frames_per_segment = int(self.config["audio_config"]["rate"] / self.config["audio_config"]["chunk"] * self.config["audio_config"]["record_seconds"])
            
            while self.is_recording:
                try:
                    data = stream.read(self.config["audio_config"]["chunk"], exception_on_overflow=False)
                    frames.append(data)
                    frame_count += 1
                    
                    if frame_count >= frames_per_segment and not self.is_playing:
                        audio_data = b''.join(frames)
                        
                        threading.Thread(
                            target=self.process_audio_segment,
                            args=(audio_data,),
                            daemon=True
                        ).start()
                        
                        # Overlap de 25%
                        overlap_frames = frames_per_segment // 4
                        frames = frames[-overlap_frames:] if len(frames) > overlap_frames else []
                        frame_count = len(frames)
                        
                except Exception as e:
                    print(f"⚠️ Erreur lecture audio: {e}")
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"❌ Erreur stream audio: {e}")
        finally:
            try:
                stream.stop_stream()
                stream.close()
            except:
                pass
    
    def process_audio_segment(self, audio_data):
        """Traite un segment audio"""
        try:
            if self.is_playing:
                return
                
            # Vérification niveau audio
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            if np.max(np.abs(audio_np)) < 1000:
                return
                
            # Transcription
            text = self.transcribe_audio(audio_data)
            
            if text and len(text.strip()) > 2 and not self.is_playing:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] 📝 {text}")
                
                # Détection des expressions
                self.detect_expressions(text, audio_data)
                    
        except Exception as e:
            print(f"⚠️ Erreur traitement: {e}")
    
    def start_listening(self):
        """Démarre l'écoute"""
        self.is_recording = True
        
        audio_thread = threading.Thread(target=self.audio_callback, daemon=True)
        audio_thread.start()
        
        print("\n" + "="*80)
        print("🎤 Détecteur de tics de langage français (Version MP3)")
        print(f"🤖 Modèle Whisper: {self.config['whisper_model']}")
        print(f"📂 Enregistrements: {self.recordings_dir}")
        print(f"🎵 MP3: {self.mp3_dir}")
        print("="*80)
        print("Ctrl+C pour arrêter\n")
        
        try:
            while self.is_recording:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_listening()
    
    def stop_listening(self):
        """Arrête l'écoute"""
        print("\n🛑 Arrêt en cours...")
        self.is_recording = False
        time.sleep(1)
        
        # Affichage des statistiques
        print(f"\n📊 Statistiques de la session:")
        total_detections = sum(self.detection_stats.values())
        
        if total_detections > 0:
            for expr_key, count in self.detection_stats.items():
                if count > 0:
                    expr_name = self.config["expressions"][expr_key]["name"]
                    percentage = (count / total_detections * 100)
                    print(f"   • {expr_name}: {count} fois ({percentage:.1f}%)")
        else:
            print("   Aucune détection")
        
        if self.audio:
            self.audio.terminate()
        pygame.mixer.quit()
        print("\n👋 Session terminée!")
    
    def get_stats(self):
        """Retourne les statistiques pour l'API web"""
        return {
            'detection_stats': self.detection_stats,
            'session_detections': self.session_detections,
            'is_recording': self.is_recording,
            'config': self.config
        }

def main():
    parser = argparse.ArgumentParser(description='Détecteur de tics avec MP3 et interface web')
    parser.add_argument('--config', default='config.json', help='Fichier de configuration')
    parser.add_argument('--web', action='store_true', help='Lancer l\'interface web')
    
    args = parser.parse_args()
    
    if args.web:
        from web_interface import create_app
        app_instance = TicDetectorApp(args.config)
        web_app = create_app(app_instance)
        print("🌐 Interface web disponible sur http://localhost:5010")
        web_app.run(host='0.0.0.0', port=5010, debug=True)
    else:
        print("🚀 Détecteur de tics de langage français (Version MP3)")
        app = TicDetectorApp(args.config)
        app.start_listening()

if __name__ == "__main__":
    main()