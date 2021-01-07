from Server.datenVerarbeitung import bereiteTraining, bereiteUebungsVorhersage, bereiteKlausurVorhersage
import unittest
from pandas.testing import assert_frame_equal
import pandas as pd
import numpy as np
from unittest.mock import Mock

#pytest -v --cov=Server --cov-report=html
class test_datenVerarbeitung(unittest.TestCase):
	def setup_method(self, method):
		self.df_dreiBlaetter = pd.DataFrame({"summe-blatt1":[10.0], "summe-blatt2":[25.0], "summe-blatt3":[50.0]})
		
		self.df_zweiEintraege = pd.DataFrame(
			{"summe-blatt1":[10.0, 5.0], "summe-blatt2":[30.0, 25.0], "summe-blatt3":[50.0, 45.0]})
		
		self.df_unnoetigesFeld = pd.DataFrame({"blatt1":[100.0, 90.0], "blatt2":[80.0, 70.0], "blatt3":[60.0, 50.0],
											   "vor_und_nach_blatt_steht_etwas":["<--", "Das was er sagt"]})
		
		self.df_falscheReihenfolge = pd.DataFrame({"blatt2":[10.0, 9.0], "blatt1":[20.0, 18.0], "blatt3":[4.0, 5.0]})
		
		self.df_nichtEinordbaresBlatt = pd.DataFrame(
			{"summe-blatt2":[100.0], "summe-blattEins":[100.0], "summe-blatt300":[100.0]})
		
		self.df_zuVielBlaetter = pd.DataFrame(
			{"B1":[13.0], "B2":[130.0], "B3":[130.0], "B4":[130.0], "B5":[130.0], "B6":[65.0], "B7":[65.0],
			 "B8":[65.0],
			 "B9":[130.0], "B10":[130.0], "B11":[130.0], "B12":[130.0], "B13":[1300.0]})
		
		self.df_zuWenigBlaetter = pd.DataFrame(
			{"B1":[1.0], "B2":[2.0], "B3":[3.0], "B4":[4.0], "B5":[5.0], "B6":[6.0], "B7":[7.0], "B8":[8.0],
			 "B9":[9.0],
			 "B10":[10.0], "B11":[11.0]})
		
		self.df_klausurZuVielBlaetter = self.df_zuVielBlaetter.copy()
		self.df_klausurZuVielBlaetter["klausurpunkte"] = [40]
		
		self.df_klausurZuWenigBlaetter = self.df_zuWenigBlaetter.copy()
		self.df_klausurZuWenigBlaetter["klausurpunkte"] = [40]
		
		self.df_klausurNoteKeinePunkte = pd.DataFrame(
			{"B1":[1.0, 0], "B2":[2.0, 0], "B3":[3.0, 0], "B4":[4.0, 0], "B5":[5.0, 0], "B6":[6.0, 0], "B7":[7.0, 0],
			 "B8":[8.0, 0], "B9":[9.0, 0], "B10":[10.0, 0], "B11":[11.0, 0], "B12":[12.0, 0], "note":[3, 5]})
	
	def test_bereiteUebungsVorhersage(self):
		#bereiteUebungsVorhersage(df, maxBlattPunkte, blattNamen)
		df_dreiBlaetter_uebungsVorhersage = bereiteUebungsVorhersage(self.df_dreiBlaetter, [50], "summe-blatt")
		df_dreiBlaetterVerschiedeneMaxima_uebungsVorhersage = bereiteUebungsVorhersage(self.df_dreiBlaetter,
																					   [10, 25, 50], "summe-blatt")
		df_zweiEintraege_uebungsVorhersage = bereiteUebungsVorhersage(self.df_zweiEintraege, [50], "summe-blatt")
		df_unnoetigesFeld_uebungsVorhersage = bereiteUebungsVorhersage(self.df_unnoetigesFeld, [100], "blatt")
		df_falscheReihenfolge_uebungsVorhersage = bereiteUebungsVorhersage(self.df_falscheReihenfolge, [20], "blatt")
		df_nichtEinordbaresBlatt_uebungsVorhersage = bereiteUebungsVorhersage(self.df_nichtEinordbaresBlatt, [100],
																			  "summe-blatt")
		
		#Werte sollten sich verdoppeln
		df_dreiBlaetter_erwartet = pd.DataFrame({"summe-blatt1":[20.0], "summe-blatt2":[50.0], "summe-blatt3":[100.0]})
		
		#Immer Volle Punktzahl erreicht
		df_dreiBlaetterVerschiedeneMaxima_erwartet = pd.DataFrame(
			{"summe-blatt1":[100.0], "summe-blatt2":[100.0], "summe-blatt3":[100.0]})
		
		#Werte sollten sich verdoppeln
		df_zweiEintraege_erwartet = pd.DataFrame(
			{"summe-blatt1":[20.0, 10.0], "summe-blatt2":[60.0, 50.0], "summe-blatt3":[100.0, 90.0]})
		
		#Unnötiges Feld wird entfernt
		df_unnoetigesFeld_erwartet = self.df_unnoetigesFeld.copy().drop("vor_und_nach_blatt_steht_etwas", axis=1)
		
		#Reihenfolge ändert sich und Eintraege
		df_falscheReihenfolge_erwartet = pd.DataFrame(
			{"blatt1":[100.0, 90.0], "blatt2":[50.0, 45.0], "blatt3":[20.0, 25.0]})
		
		#Blätter sollten trotzdem erkannt werden
		df_nichtEinordbaresBlatt_erwartet = pd.DataFrame(
			{"summe-blattEins":[100.0], "summe-blatt2":[100.0], "summe-blatt300":[100.0]})
		
		assert_frame_equal(df_dreiBlaetter_uebungsVorhersage, df_dreiBlaetter_erwartet)
		assert_frame_equal(df_dreiBlaetterVerschiedeneMaxima_uebungsVorhersage,
						   df_dreiBlaetterVerschiedeneMaxima_erwartet)
		assert_frame_equal(df_zweiEintraege_uebungsVorhersage, df_zweiEintraege_erwartet)
		assert_frame_equal(df_unnoetigesFeld_uebungsVorhersage, df_unnoetigesFeld_erwartet)
		assert_frame_equal(df_falscheReihenfolge_uebungsVorhersage, df_falscheReihenfolge_erwartet)
		assert_frame_equal(df_nichtEinordbaresBlatt_uebungsVorhersage, df_nichtEinordbaresBlatt_erwartet)
		
		#Spalte "Blatt" existiert nicht
		self.assertRaises(KeyError, bereiteUebungsVorhersage, self.df_dreiBlaetter, [50], "Blatt")
		
		#Nur drei Blätter, aber vier Maximalpunkte
		self.assertRaises(IndexError, bereiteUebungsVorhersage, self.df_dreiBlaetter, [50, 100, 50, 100],
						  "summe-blatt")
	
	def test_bereiteKlausurVorhersage(self):
		#bereiteKlausurVorhersage(df)
		df_zweiEintraege_klausurVorhersage = bereiteKlausurVorhersage(
			bereiteUebungsVorhersage(self.df_zweiEintraege, [100], "summe-blatt"))
		df_zuVielBlaetter_klausurVorhersage = bereiteKlausurVorhersage(
			bereiteUebungsVorhersage(self.df_zuVielBlaetter, [100], "B"))
		df_zuWenigBlaetter_klausurVorhersage = bereiteKlausurVorhersage(
			bereiteUebungsVorhersage(self.df_zuWenigBlaetter, [100], "B"))
		
		#Die richtigen Werte für Gesamtsumme und Punkte pro Blatt werden hinzugefügt
		df_zweiEintraege_erwartet = self.df_zweiEintraege.copy()
		df_zweiEintraege_erwartet["summe-uebungs-punkte"],\
		df_zweiEintraege_erwartet["uebungspunkte-pro-blatt"] = [90.0, 75.0], [30.0, 25.0]
		
		#Alle Blätter werden mit 12/13 multipliziert, damit Gesamtsumme passt
		#und das erste Blatt wird entfernt und jedem bearbeitetem Blatt hinzugefügt (überall + 1)
		df_zuVielBlaetter_erwartet = pd.DataFrame(
			{0:[121.0], 1:[121.0], 2:[121.0], 3:[121.0], 4:[61.0], 5:[61.0], 6:[61.0], 7:[121.0], 8:[121.0], 9:[121.0],
			 10:[121.0], 11:[1201.0], "summe-uebungs-punkte":[2352.0], "uebungspunkte-pro-blatt":[196.0]})
		
		#Weniger Blätter sind vollkommen in Ordnung. Das passiert auch während des Semesters.
		#Also werden nur die notwendigen Klausurfeatures angehängt
		df_zuWenigBlaetter_erwartet = self.df_zuWenigBlaetter.copy()
		df_zuWenigBlaetter_erwartet["summe-uebungs-punkte"],\
		df_zuWenigBlaetter_erwartet["uebungspunkte-pro-blatt"] = [66.0], [6.0]
		
		assert_frame_equal(df_zweiEintraege_klausurVorhersage, df_zweiEintraege_erwartet)
		assert_frame_equal(df_zuVielBlaetter_klausurVorhersage, df_zuVielBlaetter_erwartet)
		assert_frame_equal(df_zuWenigBlaetter_klausurVorhersage, df_zuWenigBlaetter_erwartet)
	
	def test_bereiteTraining(self):
		#bereiteTraining(df, maxBlattPunkte, blattNamen, maxKlausurPunkte, klausurPunkte, note)
		df_klausurZuVielBlaetter_bereiteTraining = bereiteTraining(self.df_klausurZuVielBlaetter, [100], "B", 100,
																   "klausurpunkte", "")
		df_klausurZuWenigBlaetter_bereiteTraining = bereiteTraining(self.df_klausurZuWenigBlaetter, [100], "B", 100,
																	"klausurpunkte", "")
		np.random.normal = Mock(return_value=np.array([25]))
		df_klausurNoteKeinePunkte_bereiteTraining = bereiteTraining(self.df_klausurNoteKeinePunkte, [10], "B", "", "",
																	"note")
		
		#Alle Blätter werden mit 12/13 multipliziert, damit Gesamtsumme passt,
		#das erste Blatt wird entfernt und jedem bearbeitetem Blatt hinzugefügt (überall + 1)
		#Features für Klausurvorhersage verden hinzugefügt
		#und die Blätter werden umbenannt
		df_klausurZuVielBlaetter_erwartet = pd.DataFrame(
			{"summe-blatt1":[121.0], "summe-blatt2":[121.0], "summe-blatt3":[121.0], "summe-blatt4":[121.0],
			 "summe-blatt5":[61.0], "summe-blatt6":[61.0], "summe-blatt7":[61.0], "summe-blatt8":[121.0],
			 "summe-blatt9":[121.0], "summe-blatt10":[121.0], "summe-blatt11":[121.0], "summe-blatt12":[1201.0],
			 "summe-uebungs-punkte":[2352.0], "uebungspunkte-pro-blatt":[196.0], "summe-klausur-punkte":[40.0]})
		
		#In der Mitte der Blätter wird der durchschnitt 6 hinzugefügt
		df_klausurZuWenigBlaetter_erwartet = pd.DataFrame(
			{"summe-blatt1":[1.0], "summe-blatt2":[2.0], "summe-blatt3":[3.0], "summe-blatt4":[4.0],
			 "summe-blatt5":[5.0], "summe-blatt6":[6.0], "summe-blatt7":[6.0], "summe-blatt8":[7.0],
			 "summe-blatt9":[8.0], "summe-blatt10":[9.0], "summe-blatt11":[10.0], "summe-blatt12":[11.0],
			 "summe-uebungs-punkte":[72.0], "uebungspunkte-pro-blatt":[6.0], "summe-klausur-punkte":[40.0]})
		
		#Note werden in Punkte umgewandelt
		df_klausurNoteKeinePunkte_erwartet = pd.DataFrame(
			{"summe-blatt1":[10.0, 0], "summe-blatt2":[20.0, 0], "summe-blatt3":[30.0, 0], "summe-blatt4":[40.0, 0],
			 "summe-blatt5":[50.0, 0], "summe-blatt6":[60.0, 0], "summe-blatt7":[70.0, 0], "summe-blatt8":[80.0, 0],
			 "summe-blatt9":[90.0, 0], "summe-blatt10":[100.0, 0], "summe-blatt11":[110.0, 0],
			 "summe-blatt12":[120.0, 0], "summe-uebungs-punkte":[780.0, 0], "uebungspunkte-pro-blatt":[65.0, 0.0],
			 "summe-klausur-punkte":[67.5, 25.0]})
		
		assert_frame_equal(df_klausurZuVielBlaetter_bereiteTraining, df_klausurZuVielBlaetter_erwartet)
		assert_frame_equal(df_klausurZuWenigBlaetter_bereiteTraining, df_klausurZuWenigBlaetter_erwartet)
		assert_frame_equal(df_klausurNoteKeinePunkte_bereiteTraining, df_klausurNoteKeinePunkte_erwartet)
		
		#Keine Klausurergebnisse
		self.assertRaises(KeyError, bereiteTraining, self.df_klausurZuWenigBlaetter, [100], "B", "", "", "")