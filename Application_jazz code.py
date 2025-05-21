import music21
import pygame
import random
import tkinter as tk
from tkinter import ttk
from threading import Thread
import os

class JazzGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Générateur de Jazz Aléatoire")
        try:
            self.root.iconbitmap(os.path.join(os.path.dirname(__file__), "applijazz.ico"))  # Ajout de l'icône
        except tk.TclError:
            print("Icône non trouvée. L'application fonctionnera sans icône.")

        self.duration_label = ttk.Label(root, text="Durée (secondes):")
        self.duration_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.duration_entry = ttk.Entry(root)
        self.duration_entry.insert(0, "30")
        self.duration_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.generate_play_button = ttk.Button(root, text="Générer et Jouer le Jazz", command=self.generate_and_play)
        self.generate_play_button.grid(row=1, column=0, columnspan=2, padx=5, pady=10)

        self.output_text = tk.Text(root, height=5, width=50)
        self.output_text.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        self.output_scrollbar = ttk.Scrollbar(root, command=self.output_text.yview)
        self.output_scrollbar.grid(row=2, column=2, sticky="ns")
        self.output_text.config(yscrollcommand=self.output_scrollbar.set)

        self.midi_file_path = None
        pygame.mixer.init()

    def get_jazz_progression(self):
        return [
            ('Cmaj7', ['C4', 'E4', 'G4', 'B4']),
            ('Fmaj7', ['F3', 'A3', 'C4', 'E4']),
            ('G7', ['G3', 'B3', 'D4', 'F4']),
            ('Cmaj7', ['C4', 'E4', 'G4', 'B4']),
            ('Amin7', ['A3', 'C4', 'E4', 'G4']),
            ('D7', ['D3', 'F#3', 'A3', 'C4']),
            ('G7', ['G3', 'B3', 'D4', 'F4']),
            ('Cmaj7', ['C4', 'E4', 'G4', 'B4']),
        ]

    def add_tempo_swing(self):
        tempo = random.choice([60, 65])
        return music21.tempo.MetronomeMark(number=tempo)

    def check_intervals(self, chord_notes):
        # Convertir les notes en objets music21.note.Note
        chord_notes_objects = [music21.note.Note(note) if isinstance(note, str) else note for note in chord_notes]

        # Vérifier les intervalles entre les notes pour éviter les dissonances
        for i in range(len(chord_notes_objects)):
            for j in range(i + 1, len(chord_notes_objects)):
                interval = music21.interval.Interval(chord_notes_objects[i], chord_notes_objects[j])

                # Si l'intervalle est une seconde mineure (dissonance forte), ou si l'intervalle est trop faible (par exemple, un triton),
                # on considère que l'accord est dissonant
                if interval.semitones in [1, 2, 6, 10]:  # Seconde mineure, septième diminuée, triton
                    return False  # Dissonance détectée
        return True

    def generate_score(self, duration=30):
        score = music21.stream.Score()
        melody = music21.stream.Part()  # Main droite (mélodie)
        bassline = music21.stream.Part()  # Main gauche (basse)
        chords = music21.stream.Part()  # Accords, souvent utilisés pour la main gauche aussi

        pedal_note = music21.note.Note('C2')
        pedal_note.quarterLength = 4
        use_pedal = True

        score.append(self.add_tempo_swing())

        total_time = 0
        progression = self.get_jazz_progression()
        last_note = None

        while total_time < duration:
            for chord_name, chord_notes in progression:
                # Vérifier si l'accord est consonant avant de l'ajouter
                if not self.check_intervals(chord_notes):
                    continue  # Si l'accord est dissonant, on passe à l'accord suivant

                # Ajouter l'accord avec quelques variations jazz (ex. ajout de 9ème, 13ème)
                if chord_name == 'G7':
                    chord_notes.append('A4')  # Ajouter la 9ème sur G7 pour donner un effet jazz
                elif chord_name == 'D7':
                    chord_notes.append('C4')  # Ajouter la 13ème sur D7

                # Partie main gauche : bassline
                bass_note = music21.note.Note(chord_notes[0])  # Prendre la première note pour la basse
                bass_note.quarterLength = 1.5
                bassline.append(bass_note)

                # Partie main gauche : accords
                chord = music21.chord.Chord(chord_notes)
                chord.quarterLength = 1.5
                chords.append(chord)

                # Partie main droite : mélodie
                scale = music21.scale.MajorScale(chord_notes[0])  # Utilisation de la gamme majeure
                for _ in range(2):
                    if last_note is None:  # Première note
                        note_name = scale.pitchFromDegree(random.randint(1, 5)).nameWithOctave.replace('4', '5')
                    else:
                        # Pour la suite de la mélodie, choisir une note proche de la précédente
                        note_name = scale.pitchFromDegree(random.randint(2, 5)).nameWithOctave.replace('4', '5')

                    note = music21.note.Note(note_name)
                    note.quarterLength = random.choice([0.75, 1.0])
                    melody.append(note)
                    total_time += note.quarterLength

                    # Conserver la dernière note générée pour la prochaine itération
                    last_note = note

                if use_pedal and random.random() < 0.3:
                    pedal = music21.note.Note(pedal_note.nameWithOctave)
                    pedal.quarterLength = random.choice([1.0, 1.5, 2.0])
                    pedal.volume.velocity = 40  # Moins fort
                    chords.append(pedal)

                total_time += 1.5
                if total_time >= duration:
                    break

        # Ajouter les différentes parties à la partition
        score.append(melody)  # Main droite : mélodie
        score.append(bassline)  # Main gauche : basse
        score.append(chords)  # Main gauche : accords


        return score

    def play_music(self):
        if self.midi_file_path:
            try:
                pygame.mixer.music.load(self.midi_file_path)
                self.output_text.insert(tk.END, f"Lecture du fichier MIDI : {self.midi_file_path}\n")
                pygame.mixer.music.play()
            except pygame.error as e:
                self.output_text.insert(tk.END, f"Erreur de lecture MIDI: {e}\n")

    def generate_and_play(self):
        try:
            duration = int(self.duration_entry.get())
        except ValueError:
            self.output_text.insert(tk.END, "Veuillez entrer une durée valide en secondes.\n")
            return

        self.output_text.delete(1.0, tk.END)
        self.generate_play_button["state"] = "disabled"

        score = self.generate_score(duration)
        self.midi_file_path = 'jazz_temp.mid'
        score.write('midi', fp=self.midi_file_path)

        self.output_text.insert(tk.END, "Jazz généré et lecture en cours...\n")
        Thread(target=self.play_music).start()
        self.generate_play_button["state"] = "normal"

if __name__ == "__main__":
    root = tk.Tk()
    app = JazzGeneratorApp(root)
    root.mainloop()
