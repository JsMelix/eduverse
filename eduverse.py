import sys
import random
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.interval.IntervalGlobal import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import *
import threading

# ------------------- CLASE DEL JUEGO 3D (Panda3D) -------------------
class EduVerse3D(ShowBase):
    def __init__(self, qt_app):
        ShowBase.__init__(self)
        self.qt_app = qt_app
        self.current_island = "math"
        self.score = 0
        
        # Configurar escena
        self.setBackgroundColor(0.1, 0.15, 0.3)
        
        # Cargar terreno
        self.environ = self.loader.loadModel("models/environment")
        self.environ.reparentTo(self.render)
        self.environ.setScale(0.25, 0.25, 0.25)
        self.environ.setPos(-8, 42, 0)
        
        # Crear avatar (un cubo con textura)
        self.avatar = self.loader.loadModel("models/smiley")
        self.avatar.reparentTo(self.render)
        self.avatar.setScale(0.5)
        self.avatar.setPos(0, 10, 0)
        
        # Controles
        self.keyMap = {"left":0, "right":0, "forward":0, "back":0}
        self.accept("arrow_left", self.setKey, ["left",1])
        self.accept("arrow_left-up", self.setKey, ["left",0])
        self.accept("arrow_right", self.setKey, ["right",1])
        self.accept("arrow_right-up", self.setKey, ["right",0])
        self.accept("arrow_up", self.setKey, ["forward",1])
        self.accept("arrow_up-up", self.setKey, ["forward",0])
        self.accept("arrow_down", self.setKey, ["back",1])
        self.accept("arrow_down-up", self.setKey, ["back",0])
        
        # Cámara que sigue al avatar
        self.camera.setPos(0, -15, 5)
        self.camera.lookAt(self.avatar)
        
        # Crear islas visuales (simplificado)
        self.islands = {
            "math": self.create_island("Matemáticas", (5, 20, 0), (0.2, 0.6, 1.0)),
            "science": self.create_island("Ciencias", (-10, 30, 0), (0.1, 0.8, 0.2)),
            "history": self.create_island("Historia", (15, 35, 0), (0.8, 0.5, 0.1)),
            "coding": self.create_island("Programación", (-5, 45, 0), (0.9, 0.2, 0.6))
        }
        
        # Texto de puntuación y misión
        self.score_text = OnscreenText(text=f"Puntos: {self.score}", pos=(-1.3, 0.9), scale=0.07, fg=(1,1,1,1))
        self.mission_text = OnscreenText(text="Ve a la isla de Matemáticas", pos=(-1.3, 0.8), scale=0.05, fg=(0.9,0.9,0.5,1))
        
        # Tarea de actualización
        self.taskMgr.add(self.update, "update")
        
        # Botón flotante para iniciar quiz (simulado)
        self.quiz_available = False
        
    def create_island(self, name, position, color):
        """Crea un cubo coloreado que representa una isla de conocimiento"""
        island = self.loader.loadModel("models/box")
        island.reparentTo(self.render)
        island.setPos(position)
        island.setScale(1.5, 1.5, 1.5)
        island.setColor(color[0], color[1], color[2], 1)
        # Añadir texto encima
        text_node = TextNode('island_label')
        text_node.setText(name)
        text_node.setAlign(TextNode.ACenter)
        text_node.setScale(0.2)
        text_node_path = self.render.attachNewNode(text_node)
        text_node_path.setPos(position[0], position[1], position[2]+1.2)
        return island
    
    def setKey(self, key, value):
        self.keyMap[key] = value
    
    def update(self, task):
        dt = globalClock.getDt()
        speed = 5
        pos = self.avatar.getPos()
        
        if self.keyMap["left"]: pos.x -= speed * dt
        if self.keyMap["right"]: pos.x += speed * dt
        if self.keyMap["forward"]: pos.y -= speed * dt
        if self.keyMap["back"]: pos.y += speed * dt
        
        self.avatar.setPos(pos)
        self.camera.setPos(pos.x, pos.y-10, 5)
        self.camera.lookAt(pos)
        
        # Detectar colisión con islas
        for name, island in self.islands.items():
            island_pos = island.getPos()
            if abs(pos.x - island_pos.x) < 1.5 and abs(pos.y - island_pos.y) < 1.5:
                if self.current_island != name:
                    self.current_island = name
                    self.mission_text.setText(f"Misión: ¡Has llegado a {name.capitalize()}! Responde la pregunta")
                    self.trigger_quiz(name)
        
        return task.cont
    
    def trigger_quiz(self, subject):
        """Envía señal a la interfaz PyQt para mostrar quiz"""
        self.quiz_available = True
        # Usar QMetaObject.invokeMethod para llamar a Qt desde hilo de Panda3D
        QMetaObject.invokeMethod(self.qt_app.main_window, "show_quiz", Qt.QueuedConnection, Q_ARG(str, subject))
    
    def add_points(self, points):
        self.score += points
        self.score_text.setText(f"Puntos: {self.score}")
        self.mission_text.setText("¡Bien! Sigue explorando")

# ------------------- INTERFAZ EDUCATIVA PyQt5 -------------------
class QuizWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("EduVerse - Pregunta")
        self.setGeometry(300, 200, 400, 300)
        self.setStyleSheet("background-color: #1e2a3a; color: white;")
        self.layout = QVBoxLayout()
        
        self.question_label = QLabel("Pregunta")
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.layout.addWidget(self.question_label)
        
        self.options = []
        self.button_group = QButtonGroup()
        for i in range(4):
            btn = QRadioButton()
            self.options.append(btn)
            self.layout.addWidget(btn)
            self.button_group.addButton(btn, i)
        
        self.submit_btn = QPushButton("Responder")
        self.submit_btn.setStyleSheet("background-color: #4CAF50; padding: 8px;")
        self.submit_btn.clicked.connect(self.check_answer)
        self.layout.addWidget(self.submit_btn)
        
        self.setLayout(self.layout)
        self.current_subject = ""
        self.questions_db = {
            "math": ("¿Cuánto es 12 x 8?", ["96", "88", "104", "92"], 0),
            "science": ("¿Qué planeta es conocido como el planeta rojo?", ["Marte", "Júpiter", "Venus", "Saturno"], 0),
            "history": ("¿En qué año llegó Colón a América?", ["1492", "1498", "1500", "1489"], 0),
            "coding": ("¿Qué función se usa para imprimir en Python?", ["print()", "console.log()", "echo", "printf"], 0)
        }
    
    def set_subject(self, subject):
        self.current_subject = subject
        if subject in self.questions_db:
            q, opts, correct = self.questions_db[subject]
            self.question_label.setText(q)
            for i, opt in enumerate(opts):
                self.options[i].setText(opt)
                self.options[i].setChecked(False)
    
    def check_answer(self):
        selected = self.button_group.checkedId()
        if selected == -1:
            QMessageBox.warning(self, "Error", "Selecciona una respuesta")
            return
        _, _, correct_idx = self.questions_db[self.current_subject]
        if selected == correct_idx:
            QMessageBox.information(self, "Correcto", "¡Respuesta correcta! +10 puntos")
            self.parent().game.add_points(10)  # Llamar al juego
            self.close()
        else:
            QMessageBox.warning(self, "Incorrecto", "Respuesta incorrecta. Intenta en otra isla")
            self.close()

class MainQtWindow(QMainWindow):
    def __init__(self, gameApp):
        super().__init__()
        self.game = gameApp
        self.setWindowTitle("EduVerse - Metaverso Educativo")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Panel de control (metaverso)
        control_panel = QFrame()
        control_panel.setStyleSheet("background-color: #0f172a; border-radius: 10px;")
        control_layout = QHBoxLayout(control_panel)
        
        self.info_label = QLabel("🌍 EduVerse Metaverso | Avatar: Estudiante")
        self.info_label.setStyleSheet("font-size: 14px; color: #cbd5e1;")
        control_layout.addWidget(self.info_label)
        
        layout.addWidget(control_panel)
        
        # Visor 3D (incrustar Panda3D)
        self.viewer_widget = QWidget()
        self.viewer_widget.setMinimumHeight(400)
        layout.addWidget(self.viewer_widget)
        
        # Botones educativos
        btn_layout = QHBoxLayout()
        self.quiz_btn = QPushButton("📚 Modo Aprendizaje Rápido")
        self.quiz_btn.clicked.connect(self.quick_quiz)
        btn_layout.addWidget(self.quiz_btn)
        
        self.social_btn = QPushButton("👥 Ver Avatares Conectados")
        self.social_btn.clicked.connect(self.show_social)
        btn_layout.addWidget(self.social_btn)
        
        layout.addLayout(btn_layout)
        
        self.quiz_window = None
        
        # Inicializar el motor Panda3D en un hilo
        self.panda_thread = threading.Thread(target=self.run_panda)
        self.panda_thread.start()
    
    def run_panda(self):
        # Integración: pasar la referencia de Qt a Panda3D
        self.game.qt_app = QApplication.instance()
        self.game.main_window = self
        self.game.run()
    
    def show_quiz(self, subject):
        if not self.quiz_window or not self.quiz_window.isVisible():
            self.quiz_window = QuizWindow(self)
            self.quiz_window.set_subject(subject)
            self.quiz_window.show()
        else:
            self.quiz_window.raise_()
    
    def quick_quiz(self):
        self.show_quiz(random.choice(["math","science","history","coding"]))
    
    def show_social(self):
        QMessageBox.information(self, "Metaverso Social", "Versión demo: ¡Pronto podrás chatear con otros estudiantes en 3D!")

# ------------------- PUNTO DE ENTRADA -------------------
def main():
    qt_app = QApplication(sys.argv)
    # Necesario para usar QWebEngine (opcional)
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    
    # Crear instancia del juego Panda3D (sin run todavía)
    game_3d = EduVerse3D(qt_app)
    window = MainQtWindow(game_3d)
    window.show()
    
    sys.exit(qt_app.exec_())

if __name__ == "__main__":
    main()
