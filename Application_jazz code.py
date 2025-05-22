import music21
import pygame
import random
import tkinter as tk
from tkinter import ttk
from threading import Thread
import os # Importation du module os pour les opérations liées au système d'exploitation, notamment pour l'icône

# Définition de la classe principale de l'application
class JazzGeneratorApp:
    """
    Cette classe représente l'application de génération de jazz aléatoire.
    Elle gère l'interface utilisateur (GUI), la logique de génération musicale
    selon les principes du jazz, et la lecture audio du résultat.
    """
    def __init__(self, root):
        """
        Initialise l'application et configure l'interface utilisateur Tkinter.

        Args:
            root (tk.Tk): La fenêtre principale Tkinter sur laquelle l'application s'exécute.
        """
        self.root = root
        self.root.title("Générateur de Jazz Aléatoire") # Définit le titre de la fenêtre de l'application

        # Tentative d'ajout d'une icône à l'application.
        # Utilise os.path.join pour construire un chemin compatible avec différents OS.
        # os.path.dirname(__file__) obtient le répertoire du script actuel.
        try:
            self.root.iconbitmap(os.path.join(os.path.dirname(__file__), "applijazz.ico"))
        except tk.TclError:
            # Si l'icône n'est pas trouvée ou ne peut être chargée, un message est imprimé.
            # L'application continue de fonctionner sans icône.
            print("Icône non trouvée. L'application fonctionnera sans icône.")

        # Création et positionnement du libellé pour l'entrée de la durée
        self.duration_label = ttk.Label(root, text="Durée (secondes):")
        self.duration_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Création et positionnement du champ de saisie pour la durée
        self.duration_entry = ttk.Entry(root)
        self.duration_entry.insert(0, "30") # Valeur par défaut de 30 secondes
        self.duration_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Création et positionnement du bouton "Générer et Jouer le Jazz"
        # La commande 'generate_and_play' est associée à l'action du bouton.
        self.generate_play_button = ttk.Button(root, text="Générer et Jouer le Jazz", command=self.generate_and_play)
        self.generate_play_button.grid(row=1, column=0, columnspan=2, padx=5, pady=10)

        # Création et positionnement de la zone de texte pour afficher les messages de l'application
        self.output_text = tk.Text(root, height=5, width=50)
        self.output_text.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        # Ajout d'une barre de défilement à la zone de texte
        self.output_scrollbar = ttk.Scrollbar(root, command=self.output_text.yview)
        self.output_scrollbar.grid(row=2, column=2, sticky="ns")
        self.output_text.config(yscrollcommand=self.output_scrollbar.set) # Lie la barre de défilement à la zone de texte

        self.midi_file_path = None # Variable pour stocker le chemin du fichier MIDI généré
        pygame.mixer.init() # Initialisation du mixeur Pygame pour la lecture des fichiers audio (MIDI dans ce cas)

    def get_jazz_progression(self):
        """
        Définit et retourne une progression d'accords jazz classique et fixe.
        Cette progression est un exemple simple mais efficace, souvent utilisé
        comme base pour l'improvisation en jazz. Chaque tuple contient
        le nom de l'accord et la liste de ses notes avec leur octave.

        Returns:
            list: Une liste de tuples représentant la progression d'accords.
        """
        return [
            ('Cmaj7', ['C4', 'E4', 'G4', 'B4']), # Do majeur 7ème
            ('Fmaj7', ['F3', 'A3', 'C4', 'E4']), # Fa majeur 7ème
            ('G7', ['G3', 'B3', 'D4', 'F4']),    # Sol 7ème (accord de dominante)
            ('Cmaj7', ['C4', 'E4', 'G4', 'B4']), # Do majeur 7ème
            ('Amin7', ['A3', 'C4', 'E4', 'G4']), # La mineur 7ème
            ('D7', ['D3', 'F#3', 'A3', 'C4']),   # Ré 7ème
            ('G7', ['G3', 'B3', 'D4', 'F4']),    # Sol 7ème
            ('Cmaj7', ['C4', 'E4', 'G4', 'B4']), # Do majeur 7ème
        ]

    def add_tempo_swing(self):
        """
        Génère un tempo de swing aléatoire, typique du jazz, entre 60 et 65 BPM.
        Ce choix de tempo est crucial pour donner la sensation de "swing" et
        permettre l'expression musicale caractéristique du genre.

        Returns:
            music21.tempo.MetronomeMark: Un objet MetronomeMark de music21
                                         représentant le tempo choisi.
        """
        tempo = random.choice([60, 65]) # Sélectionne un tempo modéré
        return music21.tempo.MetronomeMark(number=tempo)

    def check_intervals(self, chord_notes):
        """
        Vérifie les intervalles entre les notes d'un accord pour éviter les dissonances
        trop fortes qui ne seraient pas souhaitables dans une progression jazz typique.
        Cela aide à garantir que la musique générée reste agréable à l'oreille.

        Args:
            chord_notes (list): Une liste de notes (strings ou music21.note.Note) composant l'accord.

        Returns:
            bool: True si l'accord est considéré comme consonant (pas de dissonance forte),
                  False sinon.
        """
        # Convertit toutes les notes en objets music21.note.Note pour la manipulation d'intervalles
        chord_notes_objects = [music21.note.Note(note) if isinstance(note, str) else note for note in chord_notes]

        # Parcourt toutes les paires de notes pour vérifier leurs intervalles
        for i in range(len(chord_notes_objects)):
            for j in range(i + 1, len(chord_notes_objects)):
                interval = music21.interval.Interval(chord_notes_objects[i], chord_notes_objects[j])

                # Les semitons 1 (seconde mineure), 2 (seconde majeure), 6 (triton), 10 (septième diminuée)
                # sont souvent considérés comme très dissonants ou nécessitant une résolution spécifique
                # qui n'est pas gérée par cette logique simple.
                if interval.semitones in [1, 2, 6, 10]:
                    return False  # Dissonance forte détectée, l'accord est potentiellement à éviter

        return True # Aucune dissonance forte détectée, l'accord est jugé consonant

    def generate_score(self, duration=30):
        """
        Génère une partition musicale complète (mélodie, ligne de basse et accords)
        dans le style jazz. La génération est basée sur une progression d'accords fixe
        et incorpore des éléments aléatoires pour simuler l'improvisation.

        Args:
            duration (int, optional): La durée totale souhaitée de la composition en secondes.
                                      Par défaut à 30 secondes.

        Returns:
            music21.stream.Score: L'objet Score de music21 contenant la composition complète.
        """
        score = music21.stream.Score() # Crée une nouvelle partition music21
        melody = music21.stream.Part()  # Partie pour la mélodie (main droite)
        bassline = music21.stream.Part()  # Partie pour la ligne de basse (main gauche)
        chords = music21.stream.Part()  # Partie pour les accords (souvent aussi main gauche)

        # Définition d'une note pédale (basse tenue) pour ajouter de la profondeur harmonique
        pedal_note = music21.note.Note('C2') # Note Do à l'octave 2
        pedal_note.quarterLength = 4 # Durée longue pour la pédale (une ronde)
        use_pedal = True # Indicateur pour activer/désactiver l'utilisation de la pédale

        score.append(self.add_tempo_swing()) # Ajoute le tempo swing généré à la partition

        total_time = 0 # Compteur du temps total de la composition générée
        progression = self.get_jazz_progression() # Récupère la progression d'accords fixe
        last_note = None # Garde en mémoire la dernière note mélodique pour une meilleure fluidité

        # Boucle principale de génération, continue tant que la durée n'est pas atteinte
        while total_time < duration:
            for chord_name, chord_notes in progression:
                # Vérifie la consonance de l'accord avant de l'utiliser
                if not self.check_intervals(chord_notes):
                    continue  # Si l'accord est dissonant, on passe à l'accord suivant dans la progression

                # Ajout de notes d'extension jazz (9ème, 13ème) sur certains accords pour enrichir le son
                if chord_name == 'G7':
                    chord_notes.append('A4')  # Ajoute la 9ème (La4) sur l'accord de Sol 7ème
                elif chord_name == 'D7':
                    chord_notes.append('C4')  # Ajoute la 13ème (Do4) sur l'accord de Ré 7ème

                # Génération de la ligne de basse (main gauche)
                bass_note = music21.note.Note(chord_notes[0])  # La basse prend la fondamentale de l'accord
                bass_note.quarterLength = 1.5 # Durée d'une noire pointée pour la basse
                bassline.append(bass_note) # Ajoute la note de basse à la partie de basse

                # Génération des accords (main gauche)
                chord = music21.chord.Chord(chord_notes) # Crée un accord à partir des notes
                chord.quarterLength = 1.5 # Durée d'une noire pointée pour l'accord
                chords.append(chord) # Ajoute l'accord à la partie des accords

                # Génération de la ligne mélodique (main droite)
                # La gamme est basée sur la fondamentale de l'accord courant pour la cohérence harmonique
                scale = music21.scale.MajorScale(chord_notes[0])
                for _ in range(2): # Ajoute deux notes mélodiques par accord pour la variété
                    if last_note is None:  # Pour la toute première note mélodique
                        # Choisit une note dans les degrés 1 à 5 de la gamme, transposée à l'octave 5
                        note_name = scale.pitchFromDegree(random.randint(1, 5)).nameWithOctave.replace('4', '5')
                    else:
                        # Pour les notes suivantes, choisit une note proche de la précédente
                        # pour une mélodie plus fluide et naturelle
                        note_name = scale.pitchFromDegree(random.randint(2, 5)).nameWithOctave.replace('4', '5')

                    note = music21.note.Note(note_name)
                    note.quarterLength = random.choice([0.75, 1.0]) # Durée aléatoire (croche pointée ou noire)
                    melody.append(note) # Ajoute la note mélodique à la partie mélodique
                    total_time += note.quarterLength # Met à jour le temps total généré

                    # Met à jour la dernière note générée pour la prochaine itération
                    last_note = note

                # Ajout occasionnel d'une note pédale pour soutenir l'harmonie
                if use_pedal and random.random() < 0.3: # 30% de chance d'ajouter une pédale
                    pedal = music21.note.Note(pedal_note.nameWithOctave) # Crée une nouvelle note pédale
                    pedal.quarterLength = random.choice([1.0, 1.5, 2.0]) # Durée aléatoire pour la pédale
                    pedal.volume.velocity = 40  # Volume plus faible pour la pédale (son plus doux)
                    chords.append(pedal) # Ajoute la note pédale à la partie des accords

                total_time += 1.5 # Avance le temps pour le prochain segment d'accord/mélodie
                if total_time >= duration:
                    break # Sort de la boucle si la durée totale est atteinte

        # Ajoute toutes les parties générées à la partition principale
        score.append(melody)  # La partie de la mélodie
        score.append(bassline)  # La partie de la ligne de basse
        score.append(chords)  # La partie des accords

        return score # Retourne la partition complète

    def play_music(self):
        """
        Charge et joue le fichier MIDI généré par l'application.
        Gère les erreurs potentielles lors de la lecture MIDI.
        """
        if self.midi_file_path: # Vérifie si un chemin de fichier MIDI est défini
            try:
                pygame.mixer.music.load(self.midi_file_path) # Charge le fichier MIDI dans le mixeur Pygame
                self.output_text.insert(tk.END, f"Lecture du fichier MIDI : {self.midi_file_path}\n") # Informe l'utilisateur
                pygame.mixer.music.play() # Lance la lecture de la musique
            except pygame.error as e:
                # En cas d'erreur de lecture (ex: fichier corrompu, problème de périphérique),
                # affiche un message d'erreur dans la zone de texte.
                self.output_text.insert(tk.END, f"Erreur de lecture MIDI: {e}\n")

    def generate_and_play(self):
        """
        Fonction principale déclenchée par l'interaction de l'utilisateur (clic sur le bouton).
        Elle gère l'ensemble du processus : validation de la durée, génération de la partition,
        exportation au format MIDI, et lancement de la lecture audio dans un thread séparé.
        """
        try:
            duration = int(self.duration_entry.get()) # Tente de convertir la durée saisie en entier
        except ValueError:
            # Si la saisie n'est pas un nombre valide, affiche une erreur et arrête la fonction.
            self.output_text.insert(tk.END, "Veuillez entrer une durée valide en secondes.\n")
            return

        self.output_text.delete(1.0, tk.END) # Efface le contenu précédent de la zone de sortie
        self.generate_play_button["state"] = "disabled" # Désactive le bouton pour éviter les clics multiples pendant le traitement

        score = self.generate_score(duration) # Appelle la fonction pour générer la partition musicale
        self.midi_file_path = 'jazz_temp.mid' # Définit le nom du fichier MIDI temporaire
        score.write('midi', fp=self.midi_file_path) # Exporte la partition générée au format MIDI

        self.output_text.insert(tk.END, "Jazz généré et lecture en cours...\n") # Informe l'utilisateur du statut
        # Lance la fonction play_music dans un nouveau thread.
        # Cela permet à l'interface utilisateur de rester réactive pendant que la musique joue.
        Thread(target=self.play_music).start()
        self.generate_play_button["state"] = "normal" # Réactive le bouton une fois le processus de génération et de lancement terminé

# Point d'entrée de l'application
if __name__ == "__main__":
    root = tk.Tk() # Crée la fenêtre principale de l'interface graphique Tkinter
    app = JazzGeneratorApp(root) # Instancie la classe JazzGeneratorApp
    root.mainloop() # Lance la boucle principale de Tkinter, qui gère les événements de l'interface
