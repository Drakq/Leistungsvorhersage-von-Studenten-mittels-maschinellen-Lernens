import numpy as np
import pandas as pd

def zuFloat(zahl):
	try: return float(zahl)
	except ValueError: return 0

#Suche aus allen gegebenen Spalten alle Daten der Übungsblätter und sortiere sie
def findeBlaetter(df, blattNamen):
	if blattNamen == "": raise NameError("Blätter nicht differenzierbar")
	blaetterNamen = sorted(df.columns[df.columns.str.startswith(blattNamen)],
						   key=lambda blattname:zuFloat(blattname[len(blattNamen):]))
	if len(blaetterNamen) == 0: raise KeyError("Keine Blätter gefunden")
	return df[blaetterNamen].fillna(0).astype(float)

#maxPunkte pro Blatt werden auf 100 skaliert
def skaliere(blaetter, maxBlattPunkte):
	try:
		maxBlattPunkte = np.array(list(map(float, maxBlattPunkte)))
	except ValueError:
		raise ValueError(", ".join(map(str, maxBlattPunkte)) + " konnte nicht in Zahlen umgewandelt werden")
	if not maxBlattPunkte.all():
		raise NameError(", ".join(map(str, maxBlattPunkte)) + " enthält mindestens eine 0")
	if len(maxBlattPunkte) == 1:
		maxBlattPunkte = maxBlattPunkte[0]
	elif len(maxBlattPunkte) != blaetter.shape[1]:
		raise IndexError("Anzahl der Maximalpunkte stimmt nicht mit der Anzahl der Blätter überein")
	#maxima = np.nanmax(blaetter, axis=0)
	return blaetter * (100 / maxBlattPunkte)  # * (maxBlattPunkte/maxima)

#Blätter werden auf 12 erweitert oder verringert
def transformiereBlaetter(blaetter):
	spalten = blaetter.shape[1]
	
	#Wenn zu wenig Blätter, erstelle neue Blätter mit dem Durchschnitt in regelmäßigen Abständen
	if spalten < 12:
		durchschnitte = blaetter.mean(axis=1).reshape(-1, 1)
		
		#Berechne Spalten, in denen der Durchschnitt eingefügt werden soll
		indices = np.arange(0, 11, 11 / (13 - spalten))[1:]
		indices -= range(12 - spalten)
		indices[0], indices[-1] = np.floor(indices[0]), np.ceil(indices[-1])
		indices = indices.round().astype(int)
		
		blaetter = np.insert(blaetter, indices, durchschnitte, axis=1)
	
	#Wenn zu viele Blätter, teile die ersten Blätter auf die anderen auf.
	elif spalten > 12:
		#Punktzahlen müssen entsprechend verringert werden, 
		#da sonst die Maximalpunktzahl nicht verhältnismäßig ist
		blaetter *= 12 / spalten
		
		#Entfernte Spalten werden auf bearbeitete Blätter aufgeteilt
		bearbeitet = (blaetter[:, spalten - 12:] != 0)
		anzahlBearbeitet = bearbeitet.sum(axis=1)
		anzahlBearbeitet[anzahlBearbeitet == 0] = 1
		entfernt = (blaetter[:, :spalten - 12].sum(axis=1) / anzahlBearbeitet).reshape(-1, 1)
		
		blaetter = np.where(bearbeitet, blaetter[:, spalten - 12:] + entfernt, blaetter[:, spalten - 12:])
	
	return blaetter

#Berechne Gesamtsumme Übungspunkte und Übungspunkte pro bearbeitetes Blatt
def berechneKlausurFeatures(df):
	blaetterBearbeitet = (df != 0).sum(axis=1)
	summe_uebungs_punkte = df.sum(axis=1)
	uebungspunkte_pro_blatt = (summe_uebungs_punkte / blaetterBearbeitet).fillna(0)
	return np.array([summe_uebungs_punkte, uebungspunkte_pro_blatt])

#Wandle Noten in Punkte um
def zuPunkte(note):
	if note < 1.0: raise ValueError("Note besser als 1.0 enthalten")
	elif note <= 4.0:
		return {4.0:10, 3.7:11, 3.3:12, 3.0:13, 2.7:14, 2.3:15, 2.0:16, 1.7:17, 1.3:18, 1.0:19}[note] * 5 + 2.5
	else:
		#Normalverteilte Punkte zwischen 1 und 49, Erwartungswert aber bei 49
		punkte = np.random.normal(49, 48 / 3, 1)[0].clip(1, 97).astype(int)
		if punkte > 49: punkte = -punkte + 97
		return punkte
zuPunkte = np.vectorize(zuPunkte)

#Benennt Blätter um, sortiert sie, gleicht die Daten an den urspünglichen Datensatz an und
#fügt Features "summe-uebungs-punkte" und "uebungspunkte-pro-blatt" hinzu
#kurz: die Daten werden für das Training der Klausurpunkte und Übungspunkte vorbereitet.
def bereiteTraining(df, maxBlattPunkte, blattNamen, maxKlausurPunkte, klausurPunkteName, note):
	blaetter = findeBlaetter(df, blattNamen)
	
	blaetterNamen = blaetter.columns
	df = df.drop(blaetterNamen, axis=1)
	#die ggf. transformierten 12 Blätter umbenennen
	korrekteNamen = ["summe-blatt" + str(i) for i in range(1, 13)]
	df[korrekteNamen] = transformiereBlaetter(skaliere(blaetter.to_numpy(), maxBlattPunkte))
	
	#Füge Features Gesamtsumme und Übungspunkte pro bearbeitetes Blatt hinzu
	df["summe-uebungs-punkte"], df["uebungspunkte-pro-blatt"] = berechneKlausurFeatures(df[korrekteNamen])
	
	#Klausurpunkte unter richtigem Namen skaliert hinzufuegen
	if klausurPunkteName in df:
		if maxKlausurPunkte == "": raise KeyError("Keine Maximalpunktzahl der Klausur angegeben")
		df["summe-klausur-punkte"] = skaliere(df[klausurPunkteName].to_numpy(), [zuFloat(maxKlausurPunkte)])
	elif note in df:
		df["summe-klausur-punkte"] = zuPunkte(df[note].astype(float))
	else:
		raise KeyError("Keine Klausurergebnisse gefunden")
	
	#Wähle nur alle wichtigen Features
	return df[korrekteNamen + ["summe-uebungs-punkte", "uebungspunkte-pro-blatt", "summe-klausur-punkte"]]

#Sucht alle Blätter, sortiert sie und gleicht sie an den ursprünglichen Datensatz an
def bereiteUebungsVorhersage(df, maxBlattPunkte, blattNamen):
	return skaliere(findeBlaetter(df, blattNamen), maxBlattPunkte)

#Fügt Features "summe-uebungs-punkte" und "uebungspunkte-pro-blatt" hinzu.
#Damit die Summe nicht zu groß wird, maximal 12 Blätter
def bereiteKlausurVorhersage(df):
	if len(df.columns) > 12: df = pd.DataFrame(transformiereBlaetter(df.to_numpy()))
	df["summe-uebungs-punkte"], df["uebungspunkte-pro-blatt"] = berechneKlausurFeatures(df)
	return df