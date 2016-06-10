import jsocket
import logging

logger = logging.getLogger("eyeserver")
data = []
currentGlint = None
currentPupilCenter = None
currentPupilDiameter = None

class EyeServer(jsocket.ThreadedServer):
	def __init__(self):
		super(EyeServer, self).__init__()
		self.timeout = 2.0		
	
	def _process_message(self, obj):
		if obj != '':
			if obj['message'] == "new connection":
				print("New connection")

	def updateTrackingData(glint, pupilCenter, pupilDiameter):
		self.currentGlint = glint
		self.currentPupilDiameter = pupilDiameter
		self.currentPupilCenter = pupilCenter
		data["glint"] = glint
		data["diameter"] = pupilDiameter
		data["center"] = pupilCenter
		self.sendObj(data)