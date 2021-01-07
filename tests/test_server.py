from Server.server import app
from Server.vorhersage import Schaetzer
import unittest
from pandas.testing import assert_frame_equal
import pandas as pd
from io import BytesIO
from werkzeug.datastructures import FileStorage
from unittest.mock import Mock, patch

#pytest -v --cov=Server --cov-report=html
class test_server(unittest.TestCase):
	def setup_method(self, method):
		self.app = app.test_client()
		self.daten = pd.DataFrame({"summe-blatt1":[1, 2], "summe-blatt2":[2, 3], "summe-blatt3":[3, 4]})
	
	def test_startseite(self):
		rueckgabe = self.app.get("/")
		self.assertEqual(rueckgabe.status_code, 200)
	
	#Get auf Training nicht möglich
	def test_trainiere(self):
		rueckgabe = self.app.get("/training")
		self.assertEqual(rueckgabe.status_code, 405)
	
	#Vorhersageübersicht ohne Vorhersage
	def test_vorhersage(self):
		rueckgabe = self.app.get("/vorhersage")
		self.assertEqual(rueckgabe.status_code, 200)
		self.assertTrue("Keine Vorhersage gestartet!" in rueckgabe.get_data(as_text=True))
	
	#Download ohne Vorhersage
	def test_download(self):
		rueckgabe = self.app.get("/vorhersage/download")
		self.assertEqual(rueckgabe.status_code, 200)
		self.assertTrue("Keine Vorhersage gestartet!" in rueckgabe.get_data(as_text=True))
	
	def test_nichtVorhanden(self):
		rueckgabe = self.app.get("/nichtVorhanden")
		self.assertEqual(rueckgabe.status_code, 404)
	
	def test_vorhersagePOST(self):
		with patch("Server.server.session", dict()) as session:
			csv = FileStorage(stream=BytesIO(self.daten.to_csv(index=False).encode("utf-8")),
							  filename="hallo_welt.csv",
							  content_type="text/csv")
			
			erwartet = pd.DataFrame({"mentoring":[True, False], "erwartete-note":[5.0, 1.0]})
			
			#Die echten Daten sollen nicht verwendet werden
			Schaetzer.vorhersageHilfe = Mock(return_value=erwartet["mentoring"])
			Schaetzer.vorhersageKlausur = Mock(return_value=erwartet["erwartete-note"])
			
			rueckgabe = self.app.post("/vorhersage",
									  data={"maxBlattPunkte":"150", "blattNamen":"summe-blatt", "daten":csv},
									  content_type="multipart/form-data", follow_redirects=True)
			
			#Rückgabe ist erwartete CSV-Datei
			self.assertEqual(rueckgabe.status_code, 200)
			assert_frame_equal(pd.read_csv(BytesIO(rueckgabe.data)), erwartet, check_dtype=False)
			
			#Vorhersage als JSON in Session-Cookie
			self.assertEqual(session["vorhersage"], erwartet.to_json(orient="records"))
			
			#Bei get auf /Vorhersage wird Vorhersage angezeigt
			rueckgabe = self.app.get("/vorhersage")
			html = rueckgabe.get_data(as_text=True)
			self.assertEqual(rueckgabe.status_code, 200)
			self.assertTrue("Prognose für die Klausur" in html and "Hilfeleistungen" in html)
			
			#Bei Download wird Vorhersage aus Session-Cookie runtergeladen
			csv = self.app.get("/vorhersage/download")
			self.assertEqual(csv.status_code, 200)
			assert_frame_equal(pd.read_csv(BytesIO(csv.data)), erwartet, check_dtype=False)
	
	def test_vorhersageMaxBlattPunkteKeineZahl(self):
		csv = FileStorage(stream=BytesIO(self.daten.to_csv(index=False).encode("utf-8")), filename="hallo_welt.csv",
						  content_type="text/csv")
		
		rueckgabe = self.app.post("/vorhersage",
								  data={"maxBlattPunkte":"Guten Tag!", "blattNamen":"summe-blatt", "daten":csv},
								  content_type="multipart/form-data", follow_redirects=True)
		html = rueckgabe.get_data(as_text=True)
		
		self.assertEqual(rueckgabe.status_code, 200)
		self.assertTrue("Trainieren" in html and "Vorhersage" in html and "Upload leider nicht erfolgreich" in html)
	
	def test_vorhersageKeineBlaetter(self):
		csv = FileStorage(stream=BytesIO(self.daten.to_csv(index=False).encode("utf-8")), filename="hallo_welt.csv",
						  content_type="text/csv")
		
		rueckgabe = self.app.post("/vorhersage", data={"maxBlattPunkte":"100", "blattNamen":"Blatt", "daten":csv},
								  content_type="multipart/form-data", follow_redirects=True)
		html = rueckgabe.get_data(as_text=True)
		
		self.assertEqual(rueckgabe.status_code, 200)
		self.assertTrue("Trainieren" in html and "Vorhersage" in html and "Keine Blätter gefunden" in html)
	
	def test_trainierePOST(self):
		daten = self.daten.copy()
		daten["summe-klausur-punkte"] = [50, 100]
		csv = FileStorage(stream=BytesIO(daten.to_csv(index=False).encode("utf-8")), filename="hallo_welt.csv",
						  content_type="text/csv")
		
		with patch("Server.server.pd.DataFrame.to_csv"):
			Schaetzer.trainiere = Mock()  #Der Echte Schätzer soll nicht trainiert werden
			
			rueckgabe = self.app.post("/training",
									  data={"maxBlattPunkte":"50", "blattNamen":"summe-blatt",
											"maxKlausurPunkte":"100",
											"klausurPunkteName":"summe-klausur-punkte", "daten":csv},
									  content_type="multipart/form-data", follow_redirects=True)
			html = rueckgabe.get_data(as_text=True)
			
			self.assertEqual(rueckgabe.status_code, 200)
			self.assertTrue("Trainieren" in html and "Vorhersage" in html and "Upload erfolgreich!" in html)
	
	def test_trainiereMaxBlattPunkteKeineZahl(self):
		csv = FileStorage(stream=BytesIO(self.daten.to_csv(index=False).encode("utf-8")), filename="hallo_welt.csv",
						  content_type="text/csv")
		
		rueckgabe = self.app.post("/training",
								  data={"maxBlattPunkte":"Guten Tag!", "blattNamen":"summe-blatt", "daten":csv},
								  content_type="multipart/form-data", follow_redirects=True)
		html = rueckgabe.get_data(as_text=True)
		
		self.assertEqual(rueckgabe.status_code, 200)
		self.assertTrue(
			"Trainieren" in html and "Vorhersage" in html and "konnte nicht in Zahlen umgewandelt werden" in html)
	
	def test_trainiereMaxBlattPunkteEnthaltenNull(self):
		csv = FileStorage(stream=BytesIO(self.daten.to_csv(index=False).encode("utf-8")), filename="hallo_welt.csv",
						  content_type="text/csv")
		
		rueckgabe = self.app.post("/training", data={"maxBlattPunkte":"0", "blattNamen":"summe-blatt", "daten":csv},
								  content_type="multipart/form-data", follow_redirects=True)
		html = rueckgabe.get_data(as_text=True)
		
		self.assertEqual(rueckgabe.status_code, 200)
		self.assertTrue("Trainieren" in html and "Vorhersage" in html and "enthält mindestens eine 0" in html)
	
	def test_trainiereKeineKlausurergebnisse(self):
		csv = FileStorage(stream=BytesIO(self.daten.to_csv(index=False).encode("utf-8")), filename="hallo_welt.csv",
						  content_type="text/csv")
		
		rueckgabe = self.app.post("/training", data={"maxBlattPunkte":"100", "blattNamen":"summe-blatt", "daten":csv},
								  content_type="multipart/form-data", follow_redirects=True)
		html = rueckgabe.get_data(as_text=True)
		
		self.assertEqual(rueckgabe.status_code, 200)
		self.assertTrue("Trainieren" in html and "Vorhersage" in html and "Keine Klausurergebnisse gefunden" in html)