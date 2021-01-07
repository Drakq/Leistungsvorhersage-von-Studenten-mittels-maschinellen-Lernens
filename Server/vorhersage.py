from Server.datenVerarbeitung import berechneKlausurFeatures
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from glob import glob
import numpy as np
import pandas as pd

#Punktzahl in Note mithilfe der angegebenen Funktion umwandeln
def zuNote(erreichtePunkte):
	punkte = np.floor(erreichtePunkte * (20 / 100))
	if punkte < 10: return 5.0
	elif punkte >= 19: return 1.0
	else: return {10:4.0, 11:3.7, 12:3.3, 13:3.0, 14:2.7, 15:2.3, 16:2.0, 17:1.7, 18:1.3}[punkte]
zuNote = np.vectorize(zuNote)

class Schaetzer:
	#Erstelle Schätzer für nächste Leistungen in Übungsblättern und in der Klausur
	def __init__(self):
		self.uebungspunkte = [LinearRegression() for i in range(11)]
		self.klausurpunkte = [LinearRegression() for i in range(12)]
		self.polyFeat2 = PolynomialFeatures(2)
	
	def trainiere(self):
		#Suche alle CSV-Dateien und verbinde sie zu einem DataFrame
		dateien = [pd.read_csv(datei) for datei in glob("Server/data/Training/*.csv")]
		if not dateien: return
		df = pd.concat(dateien, ignore_index=True)
		
		#Trainiere jeden Übungsblattschätzer auf den zwei vergangenen Blättern
		df_uebung = df[df["summe-uebungs-punkte"] > 0]
		titel = np.char.array(["summe-blatt"] * 10)
		nummer = np.array([range(1, 11), range(2, 12), range(3, 13)], dtype=str)
		namen = (titel + nummer).T
		
		transformiert = list(map(lambda x:self.polyFeat2.fit_transform(df_uebung[x]), namen[:, :2]))
		[self.uebungspunkte[i].fit(transformiert[i - 1], df_uebung[namen[i - 1, -1]]) for i in range(1, 11)]
		self.uebungspunkte[0].fit(self.polyFeat2.fit_transform(df_uebung[["summe-blatt1"]]), df_uebung["summe-blatt2"])
		
		#Trainiere die Klausurschätzer mit allen, die die Klausur geschrieben haben
		#und wähle pro Blatt nur die Summe bis zum jeweiligen Zweitpunkt aus.
		df_klausur = df[df["summe-klausur-punkte"] > 0]
		blaetter = ["summe-blatt" + str(i) for i in range(1, 13)]
		vorbereitet = [berechneKlausurFeatures(df_klausur[blaetter[:i]]) for i in range(1, 13)]
		
		transformiert = list(map(lambda x:self.polyFeat2.fit_transform(x.T), vorbereitet))
		[self.klausurpunkte[i].fit(transformiert[i], df_klausur["summe-klausur-punkte"]) for i in range(0, 12)]
	
	#Die Leistungen auf dem nächsten Übnungsblatt werden mittels der letzten zwei Blätter
	#für jeden übergebenen Studenten vorhergesagt
	def vorhersageUebungsblatt(self, df):
		spalten = len(df.columns)
		#Wenn es zu viele Blätter gibt, wird der letzte Schätzer verwendet
		if spalten > 11: spalten = 11
		#Nutze die letzten beiden Übungsblätter
		transformiert = self.polyFeat2.fit_transform(df.iloc[:, -2:])
		return self.uebungspunkte[spalten - 1].predict(transformiert)
	
	#Für jeden übergebenen Studenten wird überprüft,
	#ob er unterdurchschnittliche Leistungen erbracht hat oder nicht
	def schlechteLeistung(self, df, stdMultiplikator):
		try: stdMultiplikator = float(stdMultiplikator)
		except ValueError: stdMultiplikator = 2
		aktuellesBlatt = df.iloc[:, -1]
		wuerdig = aktuellesBlatt[aktuellesBlatt > 0]
		durchschnitt = np.mean(wuerdig)
		std = np.std(wuerdig)
		kritisch = (aktuellesBlatt <= (durchschnitt - stdMultiplikator * std))
		return kritisch
	
	#Wenn ein Student unterdurchschnittliche Leistungen erbracht hat, ohne Sicht auf Änderung,
	#es aber zumindest versucht hat, ist er bereit für Hilfestellungen
	def vorhersageHilfe(self, df, stdMultiplikator):
		naechstesBlatt = self.vorhersageUebungsblatt(df)
		schlechteLeistung = self.schlechteLeistung(df, stdMultiplikator)
		geeignet = schlechteLeistung & (naechstesBlatt < 50)
		geeignet[df.iloc[:, -1] == 0] = False
		return geeignet
	
	#Die Klausurpunkte werden mittels der quadrierten Features 
	#"summe-uebungs-punkte" und "uebungspunkte-pro-blatt" geschätzt
	def vorhersageKlausur(self, df):
		transformiert = self.polyFeat2.fit_transform(df[["summe-uebungs-punkte", "uebungspunkte-pro-blatt"]])
		punkte = self.klausurpunkte[len(df.columns) - 3].predict(transformiert)
		maximum = punkte.max()
		if maximum < 100: punkte *= 100 / maximum
		return zuNote(punkte)