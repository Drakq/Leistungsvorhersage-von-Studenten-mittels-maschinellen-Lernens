from Server.datenVerarbeitung import bereiteTraining, bereiteUebungsVorhersage, bereiteKlausurVorhersage
from Server.vorhersage import Schaetzer
from flask import Flask, request, render_template, flash, redirect, make_response, session, url_for
from csv import Sniffer
from io import StringIO
import pandas as pd

app = Flask(__name__)
app.secret_key = "42"
schaetzer = Schaetzer()

@app.route("/")
def startseite():
	maxBlattPunkte = request.args.get("maxBlattPunkte")
	blattNamen = request.args.get("blattNamen")
	stdMultiplikator = request.args.get("stdMultiplikator")
	maxKlausurPunkte = request.args.get("maxKlausurPunkte")
	klausurPunkteName = request.args.get("klausurPunkteName")
	note = request.args.get("note")
	
	return render_template("index.html", maxBlattPunkte=maxBlattPunkte, blattNamen=blattNamen,
						   stdMultiplikator=stdMultiplikator, maxKlausurPunkte=maxKlausurPunkte,
						   klausurPunkteName=klausurPunkteName, note=note)

#curl "http://localhost:8080/vorhersage" -X POST -i -F maxBlattPunkte=100 -F blattNamen=summe-blatt
#-F daten=@../data/info1_1617.csv
@app.route("/vorhersage/", methods=["POST"])
@app.route("/vorhersage", methods=["POST"])
def bildeVorhersage():
	#Sammle Daten aus dem POST
	maxBlattPunkte = request.form["maxBlattPunkte"]
	blattNamen = request.form["blattNamen"]
	stdMultiplikator = request.form.get("stdMultiplikator")
	
	datei = request.files["daten"].read()
	sep = Sniffer().sniff(str(datei)[:100]).delimiter
	df = pd.read_csv(StringIO(str(datei, "utf-8")), sep=sep)
	df.replace(",", ".", regex=True, inplace=True)
	df.replace("-", float("nan"), regex=True, inplace=True)
	
	try:
		#Um auf benötigte Hilfeleistung zu überprüfen, werden nur die gegebenen Blätter benötigt
		df_uebung = bereiteUebungsVorhersage(df, maxBlattPunkte.split(","), blattNamen)
		geeignet = schaetzer.vorhersageHilfe(df_uebung, stdMultiplikator)
		
		#Um die vorraussichtliche Klausurnote vorherzusagen, 
		#werden "summe-uebungs-punkte" und "uebungspunkte-pro-blatt" benötigt
		df_uebung = bereiteKlausurVorhersage(df_uebung)
		note = schaetzer.vorhersageKlausur(df_uebung)
		
		vorhersage = pd.DataFrame({"mentoring":geeignet, "erwartete-note":note})
		
		#Lege Vorhersage als JSON in Session-Cookie ab
		session["vorhersage"] = vorhersage.to_json(orient="records")
		
		#Gebe die CSV-Datei zurück
		csv = make_response(vorhersage.to_csv(index=False))
		csv.headers["Content-Disposition"] = "attachment; filename=Vorhersage.csv"
		csv.headers["Content-Type"] = "text/csv"
		return csv
	except Exception as e:
		flash("Upload leider nicht erfolgreich: " + str(e), "error")
		return redirect(url_for("startseite", maxBlattPunkte=maxBlattPunkte, blattNamen=blattNamen,
								stdMultiplikator=stdMultiplikator))

@app.route("/vorhersage", methods=["GET"])
def zeigeVorhersage():
	if "vorhersage" in session:
		#Zeige die letzte Vorhersage
		return render_template("vorhersage.html", json=session["vorhersage"])
	else:
		return render_template("vorhersage.html")

@app.route("/vorhersage/download", methods=["GET"])
def downloadVorhersage():
	if "vorhersage" in session:
		#Lade die letzte Vorhersage aus Session-Cookie und gib als csv zurück.
		vorhersage = pd.read_json(session["vorhersage"], orient="records")
		csv = make_response(vorhersage.to_csv(index=False, float_format="%.1f"))
		csv.headers["Content-Disposition"] = "attachment; filename=Vorhersage.csv"
		csv.headers["Content-Type"] = "text/csv"
		return csv
	else:
		return render_template("vorhersage.html")

#curl "http://localhost:8080/training" -X POST -i -F maxBlattPunkte=100 -F blattNamen=summe-blatt -F
# maxKlausurPunkte=150 -F klausurPunkteName=summe-klausur-punkte -F note=note -F daten=@../data/info1_1617.csv
@app.route("/training/", methods=["POST"])
@app.route("/training", methods=["POST"])
def trainiere():
	#Sammle Daten aus dem POST
	maxBlattPunkte = request.form["maxBlattPunkte"]
	blattNamen = request.form["blattNamen"]
	maxKlausurPunkte = request.form.get("maxKlausurPunkte")
	klausurPunkteName = request.form.get("klausurPunkteName")
	note = request.form.get("note")
	
	datei = request.files["daten"]
	inhalt = datei.read()
	sep = Sniffer().sniff(str(inhalt)[:100]).delimiter
	df = pd.read_csv(StringIO(str(inhalt, "utf-8")), sep=sep)
	df.replace(",", ".", regex=True, inplace=True)
	
	try:
		#Daten werden den ursprünglichen angegleicht und wichtige Features werden gespeichtert
		df = bereiteTraining(df, maxBlattPunkte.split(","), blattNamen, maxKlausurPunkte, klausurPunkteName, note)
		df.to_csv("Server/data/Training/" + datei.filename, index=False)
		
		#Alle Schätzer werden mit den geänderten Daten neu trainiert
		schaetzer.trainiere()
		
		flash("Upload erfolgreich!", "erfolg")
	except Exception as e:
		flash("Upload leider nicht erfolgreich: " + str(e), "error")
		return redirect(url_for("startseite", maxBlattPunkte=maxBlattPunkte, blattNamen=blattNamen,
								maxKlausurPunkte=maxKlausurPunkte, klausurPunkteName=klausurPunkteName, note=note))
	
	return redirect(url_for("startseite"))

@app.errorhandler(404)
def error404(error):
	flash("Angefragte Seite existiert nicht", "error")
	return render_template("index.html"), 404

@app.errorhandler(405)
def error405(error):
	flash("Diese Anfragemethode wird auf diesem Pfad nicht unterstützt", "error")
	return render_template("index.html"), 405