using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using System.Linq;

public class CalibScript : MonoBehaviour {
	public bool IsCalibrating;
	public EchoTest tracker;
	public int SamplesPerPoint = 50;
	public int PrematureSamplesKillCount = 50;
	public float XRange = 5;
	public float YRange = 3;

	List<Vector2> calibDataCenter = new List<Vector2>();
	List<Vector2> calibDataTL = new List<Vector2>();
	List<Vector2> calibDataTR = new List<Vector2>();
	List<Vector2> calibDataBL = new List<Vector2>();
	List<Vector2> calibDataBR = new List<Vector2>();

	Transform cS;

	// Use this for initialization
	void Start () {
		calibDataCenter = new List<Vector2>();
		calibDataTL = new List<Vector2>();
		calibDataTR = new List<Vector2>();
		calibDataBL = new List<Vector2>();
		calibDataBR = new List<Vector2>();

		cS = transform.Find ("calibSphere");

		IsCalibrating = true;
	}
	
	// Update is called once per frame
	void Update () {		
		//Step through positions
		if (IsCalibrating && calibDataCenter.Count < SamplesPerPoint) {
			//Set sphere position
			cS.localPosition = new Vector3(0.0f,0.0f,1.32f);
			//Collect samples
			if(calibDataCenter.Count == 0 || tracker.lastVector != calibDataCenter[calibDataCenter.Count-1]) calibDataCenter.Add(tracker.lastVector);
			Debug.Log ("Center: Added " + tracker.lastVector + " , now having " + calibDataCenter.Count + " samples");
		} else if (IsCalibrating && calibDataTL.Count < SamplesPerPoint) {
			//Set sphere position
			cS.localPosition = new Vector3(0.0f,YRange,1.32f);
			//Collect samples
			if(calibDataTL.Count == 0 || tracker.lastVector != calibDataTL[calibDataTL.Count-1]) calibDataTL.Add(tracker.lastVector);
			Debug.Log ("TL: Added " + tracker.lastVector + " , now having " + calibDataTL.Count + " samples");
		} else if (IsCalibrating && calibDataTR.Count < SamplesPerPoint) {
			//Set sphere position
			cS.localPosition = new Vector3(0.0f,-YRange,1.32f);
			//Collect samples
			if(calibDataTR.Count == 0 || tracker.lastVector != calibDataTR[calibDataTR.Count-1]) calibDataTR.Add(tracker.lastVector);
			Debug.Log ("TR: Added " + tracker.lastVector + " , now having " + calibDataTR.Count + " samples");
		} else if (IsCalibrating && calibDataBL.Count < SamplesPerPoint) {
			//Set sphere position
			cS.localPosition = new Vector3(-XRange,0.0f,1.32f);
			//Collect samples
			if(calibDataBL.Count == 0 || tracker.lastVector != calibDataBL[calibDataBL.Count-1]) calibDataBL.Add(tracker.lastVector);
			Debug.Log ("BL: Added " + tracker.lastVector + " , now having " + calibDataBL.Count + " samples");
		} else if (IsCalibrating && calibDataBR.Count < SamplesPerPoint) {
			//Set sphere position
			cS.localPosition = new Vector3(XRange,0.0f,1.32f);
			//Collect samples
			if(calibDataBR.Count == 0 || tracker.lastVector != calibDataBR[calibDataBR.Count-1]) calibDataBR.Add(tracker.lastVector);
			Debug.Log ("BR: Added " + tracker.lastVector + " , now having " + calibDataBR.Count + " samples");
		} else if(IsCalibrating) {
			//Truncate lists
			calibDataCenter.RemoveRange(0, PrematureSamplesKillCount);
			calibDataTL.RemoveRange(0, PrematureSamplesKillCount);
			calibDataBL.RemoveRange(0, PrematureSamplesKillCount);
			calibDataTR.RemoveRange(0, PrematureSamplesKillCount);
			calibDataBR.RemoveRange(0, PrematureSamplesKillCount);

			//Enough data, calculate
			//NaiveLinearCalibration();
			Calibration newCalib = NonLinearMRCalibration();

			//Update calib in tracker
			tracker.CurrentCalibration = newCalib;
			IsCalibrating = false;
		}
	}

	void NaiveLinearCalibration() {
		cS.GetComponent<Renderer> ().material.color = Color.blue;

		float centerAvgX = calibDataCenter.Select (v => v.x).Average ();
		float centerAvgY = calibDataCenter.Select (v => v.y).Average ();

		float TLAvgX = calibDataTL.Select (v => v.x).Average ();
		float TLAvgY = calibDataTL.Select (v => v.y).Average ();

		float TRAvgX = calibDataTR.Select (v => v.x).Average ();
		float TRAvgY = calibDataTR.Select (v => v.y).Average ();

		float BRAvgX = calibDataBR.Select (v => v.x).Average ();
		float BRAvgY = calibDataBR.Select (v => v.y).Average ();

		float BLAvgX = calibDataBL.Select (v => v.x).Average ();
		float BLAvgY = calibDataBL.Select (v => v.y).Average ();

		//Calculate ranges
		float yEyeRange = FindDifference(TLAvgY,TRAvgY);
		float yMin = TLAvgY;
		float yScreenRange = 2*YRange;
		float yRatio = yEyeRange / yScreenRange;

		//Calculate ranges
		float xEyeRange = FindDifference(TLAvgY,TRAvgY);
		float xMin = BLAvgX;
		float xScreenRange = 2*XRange;
		float xRatio = xEyeRange / xScreenRange;

		tracker.xOffset = xMin;
		tracker.yOffset = yMin;
		tracker.yRatio = yRatio;
		tracker.xRatio = xRatio;

		Debug.Log ("XOFF: "+xMin);
		Debug.Log ("YOFF: "+yMin);
		Debug.Log ("XRatio: "+xRatio);
		Debug.Log ("YRatio: "+yRatio);

		cS.GetComponent<Renderer> ().material.color = Color.magenta;
	}

	Calibration NonLinearMRCalibration() {
		Calibration calib = new Calibration ();
		List<CalibrationData> cds = new List<CalibrationData>();

		CalibrationData cdCenter = new CalibrationData (new Vector2(0, 0), calibDataCenter);
		cds.Add (cdCenter);

		CalibrationData cdTL = new CalibrationData (new Vector2 (-XRange, YRange), calibDataTL);
		cds.Add (cdTL);

		CalibrationData cdTR = new CalibrationData (new Vector2 (XRange, YRange), calibDataTR);
		cds.Add (cdTR);

		CalibrationData cdBL = new CalibrationData (new Vector2 (-XRange, -YRange), calibDataBL);
		cds.Add (cdBL);

		CalibrationData cdBR = new CalibrationData (new Vector2 (XRange, -YRange), calibDataBR);
		cds.Add (cdBR);

		calib.calibrationData = cds;
		calib.Calibrate (20, 2);

		return calib;
	}

	public float FindDifference(float nr1, float nr2)
	{
		return Mathf.Abs(nr1 - nr2);
	}
}
