from Server.server import schaetzer, app
from waitress import serve

#python -m Server
if __name__ == "__main__":
	schaetzer.trainiere()
	with open("Server/static/banner.txt", "r") as f: print(f.read())
	serve(app, listen="*:8080")